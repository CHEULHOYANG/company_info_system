
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email import message_from_bytes as em_message_from_bytes
import email as em_lib
import imaplib
import re
import base64
from datetime import datetime
import uuid
import threading
import time
import sqlite3
import pytz
from jinja2 import Template
import ssl

KST = pytz.timezone('Asia/Seoul')
def get_kst_now():
    return datetime.now(KST)


import os
app_dir = os.path.dirname(os.path.abspath(__file__))

# --- 데이터베이스 경로 및 연결 설정 (Config) ---
import sqlite3
import os

app_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = None

def _initialize_db_path():
    global DB_PATH
    if os.environ.get('RENDER'):
        # render.com 서버 환경 - 쓰기 가능한 Persistent Disk 우선 확인
        possible_paths = [
            '/var/data',
            '/opt/render/project/data',
            '/opt/render/data',
            '/data',
            os.path.join(app_dir, 'data'),
            app_dir
        ]
        
        selected_path = None
        for path in possible_paths:
            if os.path.exists(path):
                # 쓰기 권한 테스트
                try:
                    test_file = os.path.join(path, 'db_write_test.tmp')
                    with open(test_file, 'w') as f: f.write('test')
                    os.remove(test_file)
                    selected_path = path
                    break
                except: continue
        
        if selected_path:
            DB_PATH = os.path.join(selected_path, 'company_database.db')
        else:
            # 최종 Fallback: 현재 디렉터리
            DB_PATH = os.path.join(app_dir, 'company_database.db')
    else:
        # 로컬 개발 환경
        DB_PATH = os.path.join(app_dir, 'company_database.db')
    
    # 디렉토리 보장
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        try: os.makedirs(db_dir, exist_ok=True)
        except: pass
    
    print(f"[DB_CONFIG] Using Database at: {DB_PATH}")

_initialize_db_path()

def get_db_connection(timeout=20):
    """데이터베이스 연결을 반환합니다. 병렬 처리 및 성능 최적화."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=timeout)
    conn.row_factory = sqlite3.Row
    return conn
# ---------------------------------------------

class EmailSender:
    def __init__(self, smtp_server='smtp.gmail.com', smtp_port=587, 
                 sender_email='', sender_password=''):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def send_batch_emails(self, user_id, companies_data, subject, body_template, smtp_config_id=None, group_name=None, attachments=None):
        batch_id = str(uuid.uuid4())
        sent_at = datetime.now()
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO send_batches 
            (batch_id, user_id, smtp_config_id, subject, body, total_count, sent_at, status, group_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'in_progress', ?)
            ''', (batch_id, user_id, smtp_config_id, subject, body_template, len(companies_data), sent_at, group_name))
            conn.commit()
            
            thread = threading.Thread(target=self._send_batch_worker, args=(batch_id, companies_data, subject, body_template, group_name, attachments))
            thread.daemon = True
            thread.start()
            return {'batch_id': batch_id, 'total': len(companies_data), 'status': 'in_progress'}
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _is_sender_error(self, error_msg):
        """에러 메시지를 분석하여 송신자 측 오류(한도 초과 등)인지 판별합니다."""
        if not error_msg: return False
        msg = str(error_msg).lower()
        sender_error_keywords = [
            'limit exceeded', 'quota', 'authentication', 'auth', 
            'timeout', 'connection refused', 'network', 'too many',
            'blocked', '554 5.7.1', 'daily', 'per day'
        ]
        return any(kw in msg for kw in sender_error_keywords)

    def _is_limit_error(self, error_msg):
        """에러 메시지 중 발송 한도 초과(Daily Limit) 오류인지 판별합니다."""
        if not error_msg: return False
        msg = str(error_msg).lower()
        limit_keywords = ['limit exceeded', 'quota', 'per day', 'for day', 'too many requests']
        return any(kw in msg for kw in limit_keywords)

        
    def _get_smtp_connection(self):
        """Creates and returns a new SMTP connection based on current config."""
        print(f"Connecting to SMTP {self.smtp_server}:{self.smtp_port}...")
        context = ssl.create_default_context()
        
        if int(self.smtp_port) == 465:
            server = smtplib.SMTP_SSL(self.smtp_server, int(self.smtp_port), timeout=25, context=context)
        else:
            server = smtplib.SMTP(self.smtp_server, int(self.smtp_port), timeout=25)
            server.ehlo()
            if int(self.smtp_port) == 587:
                server.starttls(context=context)
                server.ehlo()
        
        server.login(self.sender_email, self.sender_password)
        return server

    def _send_batch_worker(self, batch_id, companies_data, subject, body_template, group_name, attachments=None):
        success_count = 0
        fail_count = 0
        sent_count = 0
        total = len(companies_data)
        
        print(f"\n[BATCH START] ID: {batch_id} | Total: {total} | Group: {group_name}")
        print("="*60)
        
        server = None
        try:
            server = self._get_smtp_connection()
            print("SMTP Connected & Logged in. Starting loop...")
            self._update_batch_status(batch_id, status='in_progress')
            
            for company in companies_data:
                sent_count += 1
                email = company.get('email')
                biz_no = company.get('biz_no')
                
                if not email:
                    fail_count += 1
                    self._log_email_result(batch_id, biz_no, 'N/A', group_name, subject, 'FAIL', error="이메일 주소 없음")
                                # Personalization: Korean Macros
                mapping = {
                    '{상호}': company.get('company_name', ''),
                    '{대표자}': company.get('representative_name', ''),
                    '{이메일}': email,
                    '{연락처}': company.get('phone_number', company.get('phone', '')),
                    '{주소}': company.get('address', '')
                }
                
                current_body = body_template
                current_subject = subject
                for tag, val in mapping.items():
                    current_body = current_body.replace(tag, str(val))
                    current_subject = current_subject.replace(tag, str(val))
                
                # Attempt to send
                sent_ok = False
                error_msg = None
                try:
                    self._send_email_internal(server, email, current_subject, current_body, attachments)
                    sent_ok = True
                except Exception as e:
                    error_msg = str(e)
                    print(f"[{sent_count}/{total}] SEND FAIL: {email} | Error: {error_msg}")
                    # Reconnect if session is broken
                    try:
                        server = self._get_smtp_connection()
                    except: pass
                
                if sent_ok:
                    self._log_email_result(batch_id, biz_no, email, group_name, current_subject, 'SUCCESS')
                    success_count += 1
                else:
                    fail_count += 1
                    # 송신 오류인지 수신 계정(반송) 오류인지 판별
                    is_sender_err = self._is_sender_error(error_msg)
                    is_limit_err = self._is_limit_error(error_msg)
                    
                    if is_sender_err:
                        # 송신 한도 초과 등은 계정 차단하지 않음
                        self._log_email_result(batch_id, biz_no, email, group_name, current_subject, 'FAIL', error=error_msg, is_bounce=False)
                        
                        # 일일 한도 초과인 경우 즉시 루프 중단
                        if is_limit_err:
                            print(f"[LIMIT EXCEEDED] ID: {batch_id} | Stopping batch...")
                            self._update_batch_status(batch_id, status='LIMIT_EXCEEDED', completed=True)
                            break
                    else:
                        # 수신자 계정 문제(반송 등)인 경우에만 자동 보정 대상 포함
                        self._log_email_result(batch_id, biz_no, email, group_name, current_subject, 'FAIL', error=error_msg, is_bounce=True)
                        self._disable_invalid_email(biz_no, error_msg)

                # Real-time progress update
                self._update_batch_progress(batch_id, sent_count, success_count, fail_count)
                
                # Dynamic sleep to avoid rate limiting
                time.sleep(0.5) 

            print("="*60)
            print(f"[BATCH COMPLETED] ID: {batch_id} | Success: {success_count} | Fail: {fail_count}\n")
            self._update_batch_status(batch_id, status='completed', completed=True)
            
        except Exception as e:
            print(f"\n[BATCH ERROR] ID: {batch_id} | Fatal Error: {str(e)}\n")
            import traceback
            traceback.print_exc()
            self._update_batch_status(batch_id, status='error', error=str(e))
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass

    def _log_email_result(self, batch_id, biz_no, email, group_name, subject, status, error=None, is_bounce=False):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Log the individual result
        cursor.execute('''
            INSERT INTO email_send_log (batch_id, biz_no, email, group_name, subject, status, error_msg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (batch_id, biz_no, email, group_name, subject, status, error))
        
        # Update Company_Basic with the latest status
        now_str = get_kst_now().strftime('%Y-%m-%d %H:%M:%S')
        if status == 'SUCCESS':
            # Successful send means email is usable, and we reset the fix status
            cursor.execute('''
                UPDATE Company_Basic 
                SET email_usable = 1, email_fix_status = 0, 
                    last_send_at = ?, last_send_status = 'SUCCESS'
                WHERE biz_no = ?
            ''', (now_str, biz_no))
        else:
            # Failure (특히 송신 측 오류가 아닌 '반송'인 경우에만 사용 불가 처리)
            if is_bounce:
                cursor.execute('''
                    UPDATE Company_Basic 
                    SET email_usable = 0, last_send_at = ?, last_send_status = 'FAIL'
                    WHERE biz_no = ?
                ''', (now_str, biz_no))
            else:
                # 송신 측 오류일 경우 usable 상태 유지
                cursor.execute('''
                    UPDATE Company_Basic 
                    SET last_send_at = ?, last_send_status = 'FAIL_SENDER'
                    WHERE biz_no = ?
                ''', (now_str, biz_no))
            
        conn.commit()
        conn.close()

    def _disable_invalid_email(self, biz_no, error_msg):
        """Disables the email and marks as rejected to prevent further attempts"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE Company_Basic 
            SET email_usable = 0, last_send_status = 'REJECTED', 
                email_fix_status = 0
            WHERE biz_no = ?
        ''', (biz_no,))
        conn.commit()
        conn.close()

    def _update_batch_progress(self, batch_id, sent_count, success_count, fail_count):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE send_batches 
            SET sent_count = ?, success_count = ?, fail_count = ? 
            WHERE batch_id = ?
        ''', (sent_count, success_count, fail_count, batch_id))
        conn.commit()
        conn.close()

    def _update_batch_status(self, batch_id, status, completed=False, error=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        if completed:
            cursor.execute('UPDATE send_batches SET status = ?, completed_at = ? WHERE batch_id = ?', (status, get_kst_now(), batch_id))
        elif error:
            cursor.execute('UPDATE send_batches SET status = ?, last_error = ? WHERE batch_id = ?', (status, error, batch_id))
        else:
            cursor.execute('UPDATE send_batches SET status = ? WHERE batch_id = ?', (status, batch_id))
        conn.commit()
        conn.close()

    def _send_email_internal(self, server, to_email, subject, body, attachments=None):
        import os
        from email.header import Header
        
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = to_email
        
        # HTML body
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        # Attachments
        if attachments:
            for att in attachments:
                file_path = att.get('path')
                file_name = att.get('name')
                
                if not file_path or not os.path.exists(file_path):
                    continue
                    
                with open(file_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    
                    # Handle Korean filename
                    safe_name = Header(file_name, 'utf-8').encode()
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={safe_name}",
                    )
                    msg.attach(part)
                    
        server.send_message(msg)

# --- Compatibility Functions ---

def get_email_groups():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM email_groups ORDER BY id")
    groups = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return groups

def get_group_members(group_id):
    """
    그룹에 속한 모든 멤버를 조회합니다.
    반송 상태(email_usable=0)도 함께 반환하여 UI에서 표시할 수 있게 합니다.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cb.biz_no, cb.company_name, cb.email, cb.representative_name, 
               cb.email_usable, cb.last_send_status, cb.region
        FROM Company_Basic cb
        JOIN email_group_members egm ON cb.biz_no = egm.biz_no
        WHERE egm.group_id = ?
        ORDER BY CASE WHEN cb.email_usable = 0 THEN 1 ELSE 0 END,
                 cb.company_name
    ''', (group_id,))
    members = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return members

def get_email_history(batch_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1순위: batch_id로 직접 조회 (가장 정확)
        cursor.execute('''
            SELECT el.*, COALESCE(cb.company_name, el.biz_no) as company_name 
            FROM email_send_log el
            LEFT JOIN Company_Basic cb ON el.biz_no = cb.biz_no
            WHERE el.batch_id = ?
            ORDER BY el.sent_at DESC
        ''', (batch_id,))
        history = [dict(row) for row in cursor.fetchall()]
        
        # 2순위: 결과가 없으면 group_name으로 조회 (구버전 호환)
        if not history:
            cursor.execute('''
                SELECT el.*, COALESCE(cb.company_name, el.biz_no) as company_name 
                FROM email_send_log el
                LEFT JOIN Company_Basic cb ON el.biz_no = cb.biz_no
                WHERE el.group_name = (SELECT group_name FROM send_batches WHERE batch_id = ?)
                ORDER BY el.sent_at DESC
            ''', (batch_id,))
            history = [dict(row) for row in cursor.fetchall()]
        
        return history
    except Exception as e:
        print(f"[get_email_history] Error: {e}")
        return []
    finally:
        conn.close()

def cleanup_email_groups():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM email_group_members')
        cursor.execute('DELETE FROM email_groups')
        cursor.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'email_groups'")
        conn.commit()
        return {'success': True}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'message': str(e)}
    finally:
        conn.close()

def generate_smart_groups(category='GENERAL', limit_per_group=100, is_risk_mode=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Prevent Duplicates for the specific category: Clear only relevant groups before generation
        # This allows GENERAL, MANAGED, and SANDBOX groups to coexist.
        cursor.execute('''
            DELETE FROM email_group_members 
            WHERE group_id IN (SELECT id FROM email_groups WHERE category = ?)
        ''', (category,))
        cursor.execute('DELETE FROM email_groups WHERE category = ?', (category,))
        
        # High Risk Industry Keywords
        HIGH_RISK_KEYWORDS = ['자동차부품', '금속가공', '화학', '고무', '플라스틱', '물류창고', '목재', '용접']
        risk_conditions = " OR ".join([f"industry_name LIKE '%{k}%'" for k in HIGH_RISK_KEYWORDS])
        
        # Region Mapping
        region_map = {
            '서울': ['서울'], '경기': ['경기', '경기도'], '인천': ['인천', '인천광역시'],
            '강원': ['강원', '강원특별자치도'], '충청': ['충남', '충북'], '대전': ['대전'],
            '부산': ['부산'], '울산': ['울산', '울산광역시'], '대구': ['대구'],
            '광주': ['광주'], '전남': ['전남'], '전북': ['전북', '전북특별자치도'],
            '경남': ['경남'], '경북': ['경북'], '제주': ['제주', '제주특별자치도'], '세종': ['세종']
        }
        
        total_created = 0
        total_groups = 0
        
        for region_name, db_regions in region_map.items():
            filter_sql = ""
            if category == 'GENERAL':
                filter_sql = """
                    AND company_size NOT IN ('대기업', '중견기업')
                    AND company_name NOT LIKE '%(사)%'
                    AND company_name NOT LIKE '%사단법인%'
                """
            
            # Risk Mode Filtering: if ON, only show high risk. Otherwise, show all but sort by risk.
            mode_filter = ""
            if is_risk_mode:
                mode_filter = f"AND ({risk_conditions})"
            
            query = f'''
                SELECT biz_no, 
                       (CASE WHEN {risk_conditions} THEN 1 ELSE 0 END) as is_high_risk
                FROM Company_Basic 
                WHERE email_usable = 1 
                AND email IS NOT NULL 
                AND email != ''
                AND category = ?
                AND region IN ({",".join(["'"+r+"'" for r in db_regions])})
                {filter_sql}
                {mode_filter}
                ORDER BY is_high_risk DESC, biz_no ASC
            '''
            cursor.execute(query, (category,))
            rows = cursor.fetchall()
            biz_nos = [row['biz_no'] for row in rows]
            
            if not biz_nos:
                continue
                
            import math
            num_region_groups = math.ceil(len(biz_nos) / limit_per_group)
            
            for i in range(num_region_groups):
                start = i * limit_per_group
                end = min((i + 1) * limit_per_group, len(biz_nos))
                chunk = biz_nos[start:end]
                
                # Check if this chunk has any high risk members (always true if is_risk_mode is ON)
                # But even in regular mode, if high risk companies are at the start, name them accordingly.
                has_high_risk = any(row['is_high_risk'] == 1 for row in rows[start:end])
                
                # Naming: 지역_[제조_]100_순번
                industry_tag = "제조_" if has_high_risk else ""
                group_name = f"{region_name}_{industry_tag}{limit_per_group}_{i+1}"
                
                cursor.execute('''
                    INSERT INTO email_groups (name, category, member_count) 
                    VALUES (?, ?, ?)
                ''', (group_name, category, len(chunk)))
                group_id = cursor.lastrowid
                
                member_data = [(group_id, b) for b in chunk]
                cursor.executemany('INSERT INTO email_group_members (group_id, biz_no) VALUES (?, ?)', member_data)
                
                total_created += len(chunk)
                total_groups += 1
                
        conn.commit()
        return {'success': True, 'total_companies': total_created, 'num_groups': total_groups}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'message': str(e)}
    finally:
        conn.close()

def get_all_batches(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM send_batches 
        WHERE user_id = ?
        ORDER BY sent_at DESC
    ''', (user_id,))
    batches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return batches

def bulk_update_delivery_results(delivery_items):
    """
    외부 리포트(CSV 등)로부터 전달받은 대량의 발송 결과를 시스템에 일괄 반영합니다.
    Args:
        delivery_items: [{'biz_no': '...', 'status': 'SUCCESS/FAIL/BOUNCE', 'error': '...'}]
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        now_str = get_kst_now().strftime('%Y-%m-%d %H:%M:%S')
        updated_count = 0
        
        for item in delivery_items:
            biz_no = item.get('biz_no')
            status = (item.get('status') or 'SUCCESS').upper()
            error_msg = item.get('error') or ''
            
            if not biz_no: continue
            
            # 1. Company_Basic 테이블 업데이트 (글로벌 상태)
            usable = 1 if status == 'SUCCESS' else 0
            if status == 'BOUNCE':
                fix_status = 0 # 반송이면 수정 모드 초기화 (수정대상으로 표시)
            else:
                fix_status = 1 if status == 'FAIL' else 0

            cursor.execute('''
                UPDATE Company_Basic 
                SET email_usable = ?, 
                    last_send_at = ?, 
                    last_send_status = ?,
                    email_fix_status = ?
                WHERE biz_no = ?
            ''', (usable, now_str, status, fix_status, biz_no))
            
            # 2. 관련 로그가 있다면 최근 로그도 업데이트 (가장 최근 발송건 1건)
            cursor.execute('''
                UPDATE email_send_log
                SET status = ?, error_msg = COALESCE(?, error_msg)
                WHERE biz_no = ? AND id = (
                    SELECT id FROM email_send_log WHERE biz_no = ? ORDER BY sent_at DESC LIMIT 1
                )
            ''', (status, error_msg, biz_no, biz_no))
            
            if cursor.rowcount > 0:
                updated_count += 1
                
        conn.commit()
        return {'success': True, 'count': updated_count}
    except Exception as e:
        conn.rollback()
        print(f"[bulk_update_delivery_results] Error: {e}")
        return {'success': False, 'message': str(e)}
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────
# 📬 반송 메일 자동 감지 & DB 업데이트 (IMAP 기반)
# ─────────────────────────────────────────────────────────────

class EmailReceiver:
    """Gmail/Naver 등의 IMAP을 통해 반송(bounce) 메일을 감지합니다."""

    def __init__(self, imap_server, imap_port, email_addr, password):
        self.imap_server = imap_server
        self.imap_port = int(imap_port or 993)
        self.email_addr = email_addr
        self.password = password

    def connect(self):
        """IMAP 서버에 연결하고 mail 객체를 반환합니다."""
        import socket
        # Render/클라우드 환경에서 IMAP 연결 타임아웃 설정 (25초)
        socket.setdefaulttimeout(25)
        try:
            if self.imap_port == 993:
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            else:
                mail = imaplib.IMAP4(self.imap_server, self.imap_port)
            mail.login(self.email_addr, self.password)
        finally:
            # 타임아웃을 기본값으로 복구 (다른 연결에 영향 없도록)
            socket.setdefaulttimeout(None)
        return mail

    def check_bounces(self, since_date: str):
        """
        since_date('YYYY-MM-DD') 이후 받은편지함에서 반송 메일을 찾아
        반송된 이메일 주소 목록(소문자 set)을 반환합니다.
        """
        bounced = set()
        mail = None
        try:
            try:
                mail = self.connect()
            except imaplib.IMAP4.error as e:
                raise Exception(f"IMAP 인증 실패: {str(e)}. 비밀번호 또는 IMAP 서버 설정을 확인해주세요.")
            except Exception as e:
                raise Exception(f"IMAP 연결 실패 ({self.imap_server}:{self.imap_port}): {str(e)}")
            
            # Gmail의 경우 "[Gmail]/All Mail" (전체보관함)을 우선 시도 (가장 확실함)
            # 다른 서버는 INBOX를 기본으로 사용
            is_gmail = 'gmail' in self.imap_server.lower()
            target_folders = []
            if is_gmail:
                target_folders = ['"[Gmail]/All Mail"', 'INBOX', '"[Gmail]/Spam"', 'INBOX.Junk']
            else:
                target_folders = ['INBOX', 'Spam', 'Junk']

            for folder in target_folders:
                try:
                    # 폴더 선택 (Gmail의 경우 영문 명칭이 한글 계정에서도 작동함)
                    status, _ = mail.select(folder)
                    if status != 'OK': continue

                    date_obj = datetime.strptime(since_date, '%Y-%m-%d')
                    imap_date = date_obj.strftime('%d-%b-%Y')
                    status, messages = mail.search(None, f'(SINCE "{imap_date}")')
                    if status != 'OK':
                        continue

                    for num in messages[0].split():
                        try:
                            status, data = mail.fetch(num, '(RFC822)')
                            if status != 'OK':
                                continue
                            raw_email = data[0][1]
                            msg = em_message_from_bytes(raw_email)

                            # 발신자가 반송 시스템인지 확인
                            sender = str(msg.get('From', '')).lower()
                            subject_raw = str(msg.get('Subject', '')).lower()
                            is_bounce = any(kw in sender for kw in [
                                'mailer-daemon', 'postmaster', 'delivery', 'noreply', 'no-reply'
                            ]) or any(kw in subject_raw for kw in [
                                'delivery status', 'undeliverable', 'returned mail',
                                'failure notice', 'delivery failure', 'mail delivery failed',
                                '반송', '전달 실패', 'delivery notification'
                            ])

                            if not is_bounce:
                                continue

                            # 메일 본문에서 이메일 주소 추출
                            content = self._extract_text(msg)
                            found = re.findall(
                                r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', content
                            )
                            for addr in found:
                                addr_lower = addr.lower()
                                # 자기 자신 주소나 시스템 주소 제외
                                if addr_lower != self.email_addr.lower() and \
                                   not any(kw in addr_lower for kw in ['mailer-daemon', 'postmaster']):
                                    bounced.add(addr_lower)
                        except Exception as e:
                            print(f"[EmailReceiver] 메일 파싱 오류: {e}")
                            continue

                except Exception as fe:
                    print(f"[EmailReceiver] 폴더 {folder} 처리 중 오류: {fe}")
                    continue

            mail.logout()
        except Exception as e:
            print(f"[EmailReceiver] IMAP 연결/검색 오류: {e}")
            raise
        finally:
            try:
                if mail:
                    mail.logout()
            except:
                pass

        return bounced

    def _extract_text(self, msg):
        """이메일 메시지에서 텍스트 내용을 추출합니다."""
        text = ''
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct in ('text/plain', 'text/html', 'message/delivery-status'):
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            text += payload.decode('utf-8', errors='replace')
                    except:
                        text += str(part.get_payload())
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    text = payload.decode('utf-8', errors='replace')
            except:
                text = str(msg.get_payload())
        return text


def check_bounce_and_update(smtp_config_id: int, since_date: str):
    """
    IMAP으로 반송 메일을 확인한 뒤 DB를 업데이트합니다.

    처리 흐름:
    1. smtp_configs에서 IMAP 설정 조회
    2. EmailReceiver로 받은편지함 반송 메일 파싱
    3. email_send_log에서 해당 이메일 주소의 레코드를 BOUNCE로 변경
    4. Company_Basic.email_usable = 0, last_send_status = 'BOUNCE' 로 설정
    5. send_batches의 fail_count / success_count 재집계

    Returns dict: {success, bounced_count, updated_log_count, message}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. SMTP 설정 조회
        cursor.execute('SELECT * FROM smtp_configs WHERE config_id = ?', (smtp_config_id,))
        config = cursor.fetchone()
        if not config:
            return {'success': False, 'message': 'SMTP 설정을 찾을 수 없습니다.'}

        imap_server = config['imap_server'] if config['imap_server'] else 'imap.gmail.com'
        imap_port   = config['imap_port']   if config['imap_port']   else 993

        # 2. 반송 메일 감지
        receiver = EmailReceiver(
            imap_server=imap_server,
            imap_port=imap_port,
            email_addr=config['sender_email'],
            password=config['sender_password']
        )
        bounced_emails = receiver.check_bounces(since_date)
        print(f"[check_bounce] 감지된 반송 이메일: {bounced_emails}")

        if not bounced_emails:
            return {
                'success': True,
                'bounced_count': 0,
                'updated_log_count': 0,
                'message': '반송된 이메일이 없습니다. (받은편지함 확인 완료)'
            }

        # 3. email_send_log 에서 해당 날짜 이후 발송된 레코드 중 반송 이메일 → BOUNCE
        updated_log = 0
        for email_addr in bounced_emails:
            cursor.execute('''
                UPDATE email_send_log
                SET status = 'BOUNCE', error_msg = '반송(수신 불가) - IMAP 자동 감지'
                WHERE LOWER(email) = ?
                  AND sent_at >= ?
                  AND status = 'SUCCESS'
            ''', (email_addr.lower(), since_date + ' 00:00:00'))
            updated_log += cursor.rowcount

        # 4. Company_Basic 업데이트: email_usable=0, 상태='BOUNCE'
        now_str = get_kst_now().strftime('%Y-%m-%d %H:%M:%S')
        bounce_list = list(bounced_emails)
        placeholders = ','.join(['?'] * len(bounce_list))
        cursor.execute(f'''
            UPDATE Company_Basic
            SET email_usable = 0,
                last_send_status = 'BOUNCE',
                last_send_at = ?
            WHERE LOWER(email) IN ({placeholders})
        ''', [now_str] + [e.lower() for e in bounce_list])

        # 5. send_batches 재집계 (since_date 이후 배치만)
        cursor.execute('''
            SELECT DISTINCT batch_id FROM email_send_log
            WHERE sent_at >= ?
        ''', (since_date + ' 00:00:00',))
        batch_ids = [r[0] for r in cursor.fetchall() if r[0]]

        for bid in batch_ids:
            cursor.execute('''
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as succ,
                    SUM(CASE WHEN status IN ('FAIL','ERROR','BOUNCE') THEN 1 ELSE 0 END) as fail
                FROM email_send_log WHERE batch_id = ?
            ''', (bid,))
            row = cursor.fetchone()
            if row:
                cursor.execute('''
                    UPDATE send_batches
                    SET success_count = ?, fail_count = ?
                    WHERE batch_id = ?
                ''', (row['succ'] or 0, row['fail'] or 0, bid))

        conn.commit()

        return {
            'success': True,
            'bounced_count': len(bounced_emails),
            'updated_log_count': updated_log,
            'bounced_emails': list(bounced_emails),
            'message': (
                f'반송 감지 완료: {len(bounced_emails)}개 이메일 반송 확인, '
                f'{updated_log}건 로그 업데이트, '
                f'타겟 그룹 발송 불가 처리 완료'
            )
        }

    except Exception as e:
        conn.rollback()
        print(f"[check_bounce_and_update] Error: {e}")
        return {'success': False, 'message': f'반송 확인 오류: {str(e)}'}
    finally:
        conn.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print(" [🔵 QUANTUM EMAIL SERVICE ENGINE V2.0 ]")
    print("="*60)
    print("  ● 엔진 상태: 가동 준비 완료 (ONLINE/READY)")
    print("  ● 현재 모드: 퀀텀 프리미엄 라이브러리 전용")
    print("  ● 연동 모듈: web_app.py / email_management.html")
    print("-" * 60)
    print("  ※ 시스템 가동을 위해 터미널에서 아래 명령을 실행하십시오:")
    print("  > python web_app.py")
    print("="*60 + "\n")
