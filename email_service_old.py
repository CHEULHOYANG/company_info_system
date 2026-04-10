
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

# µ¥ÀÌÅÍº£ÀÌ½º °æ·Î ¼³Á¤: Render ¼­¹ö ¹èÆ÷ ½Ã ¿µ±¸ ÀúÀå¼Ò Áö¿ø ¹× ·ÎÄÃ °³¹ß È¯°æ Áö¿ø
if os.environ.get('RENDER'):
    print("\n=== Render È¯°æ °¨Áö - Persistent Disk °æ·Î Å½»ö ===")
    
    # ·çÆ® µð·ºÅÍ¸® ³»¿ë È®ÀÎ (µð¹ö±ë¿ë)
    try:
        root_items = os.listdir('/')
        print(f"/ µð·ºÅÍ¸® ³»¿ë: {root_items}")
    except Exception as e:
        print(f"·çÆ® µð·ºÅÍ¸® È®ÀÎ ½ÇÆÐ: {e}")
    
    # °¡´ÉÇÑ °æ·Îµé È®ÀÎ
    possible_paths = [
        '/var/data',
        '/opt/render/project/data', 
        '/opt/render/data',
        '/data',
        '/tmp/data',
        '/app/data',
        os.path.join(app_dir, 'data')
    ]
    
    print(f"\n=== °¡´ÉÇÑ µ¥ÀÌÅÍ °æ·Îµé È®ÀÎ ===")
    persistent_disk_path = None
    for path in possible_paths:
        print(f"°æ·Î È®ÀÎ Áß: {path}")
        if os.path.exists(path):
            print(f"? ¹ß°ß: {path}")
            
            # µð·ºÅÍ¸® ³»¿ë È®ÀÎ
            try:
                contents = os.listdir(path)
                print(f"  ³»¿ë: {contents}")
            except Exception as e:
                print(f"  ³»¿ë È®ÀÎ ½ÇÆÐ: {e}")
            
            # µð·ºÅÍ¸®¿¡ ¾²±â ±ÇÇÑÀÌ ÀÖ´ÂÁö È®ÀÎ
            try:
                test_file = os.path.join(path, 'test_write.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                persistent_disk_path = path
                print(f"? ¾²±â ±ÇÇÑ È®ÀÎ: {path}")
                break
            except Exception as e:
                print(f"? ¾²±â ±ÇÇÑ ¾øÀ½: {path} - {e}")
        else:
            print(f"? ¾øÀ½: {path}")
    
    # Persistent Disk µð·ºÅÍ¸® È®ÀÎ ¹× »ý¼º
    if persistent_disk_path:
        # Persistent Disk°¡ ¸¶¿îÆ®µÈ °æ¿ì
        DB_PATH = os.path.join(persistent_disk_path, 'company_database.db')
        print(f"\n? »ç¿ëÇÒ DB °æ·Î: {DB_PATH}")
        
        # ±âÁ¸ DB ÆÄÀÏ È®ÀÎ
        if os.path.exists(DB_PATH):
            print(f"? ±âÁ¸ DB ÆÄÀÏ ¹ß°ß: {DB_PATH}")
        else:
            print(f"»õ DB ÆÄÀÏ »ý¼º ¿¹Á¤: {DB_PATH}")
        
        # µð·ºÅÍ¸® »ý¼º ½Ãµµ
        try:
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            print(f"? DB µð·ºÅÍ¸® ÁØºñ ¿Ï·á: {os.path.dirname(DB_PATH)}")
        except Exception as e:
            print(f"? DB µð·ºÅÍ¸® »ý¼º ½ÇÆÐ: {e}")
    else:
        print("\n? »ç¿ë °¡´ÉÇÑ Persistent Disk °æ·Î¸¦ Ã£À» ¼ö ¾øÀ½")
        # Persistent Disk°¡ ¾ø´Â °æ¿ì (±âÁ¸ ·ÎÁ÷ À¯Áö)
        # 1¼øÀ§: ±âÁ¸ DB ÆÄÀÏÀÌ ÀÖÀ¸¸é °è¼Ó »ç¿ë (µ¥ÀÌÅÍ º¸Á¸)
        existing_db = os.path.join(app_dir, 'company_database.db')
        if os.path.exists(existing_db):
            DB_PATH = existing_db
            print(f"Using existing DB (no persistent disk): {DB_PATH}")
        else:
            # 2¼øÀ§: ±âÁ¸ DB°¡ ¾øÀ¸¸é data Æú´õ¿¡ »õ·Î »ý¼º
            db_dir = os.path.join(app_dir, 'data')
            os.makedirs(db_dir, exist_ok=True)
            DB_PATH = os.path.join(db_dir, 'company_info.db')
            print(f"Creating new DB (no persistent disk): {DB_PATH}")
else:
    # ·ÎÄÃ °³¹ß È¯°æ - ±âÁ¸ ÆÄÀÏ »ç¿ë
    DB_PATH = os.path.join(app_dir, 'company_database.db')
    print(f"Local DB: {DB_PATH}")

print(f"[EmailService] Using Database at: {DB_PATH}")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

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

    def _send_batch_worker(self, batch_id, companies_data, subject, body_template, group_name, attachments=None):
        success_count = 0
        fail_count = 0
        sent_count = 0
        total = len(companies_data)
        
        print(f"\n[BATCH START] ID: {batch_id} | Total: {total} | Group: {group_name}")
        print("="*60)
        
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
                    self._log_email_result(batch_id, biz_no, 'N/A', group_name, subject, 'FAIL', error="?´ë©”ì¼ ì£¼ì†Œ ?—†?Œ")
                                # Personalization: Korean Macros
                mapping = {
                    '{?ƒ?˜¸}': company.get('company_name', ''),
                    '{????‘œ?ž}': company.get('representative_name', ''),
                    '{?´ë©”ì¼}': email,
                    '{?—°?½ì²?}': company.get('phone_number', company.get('phone', '')),
                    '{ì£¼ì†Œ}': company.get('address', '')
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
                    # AUTO FILTER: Disable invalid email for future batches
                    self._log_email_result(batch_id, biz_no, email, group_name, current_subject, 'FAIL', error=error_msg)
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

    def _log_email_result(self, batch_id, biz_no, email, group_name, subject, status, error=None):
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
            # Failure (especially bounce/reject) means email is NOT usable until fixed
            cursor.execute('''
                UPDATE Company_Basic 
                SET email_usable = 0, last_send_at = ?, last_send_status = 'FAIL'
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
    ê·¸ë£¹?— ?†?•œ ëª¨ë“  ë©¤ë²„ë¥? ì¡°íšŒ?•©?‹ˆ?‹¤.
    ë°˜ì†¡ ?ƒ?ƒœ(email_usable=0)?„ ?•¨ê»? ë°˜í™˜?•˜?—¬ UI?—?„œ ?‘œ?‹œ?•  ?ˆ˜ ?žˆê²? ?•©?‹ˆ?‹¤.
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
        # 1?ˆœ?œ„: batch_idë¡? ì§ì ‘ ì¡°íšŒ (ê°??ž¥ ? •?™•)
        cursor.execute('''
            SELECT el.*, COALESCE(cb.company_name, el.biz_no) as company_name 
            FROM email_send_log el
            LEFT JOIN Company_Basic cb ON el.biz_no = cb.biz_no
            WHERE el.batch_id = ?
            ORDER BY el.sent_at DESC
        ''', (batch_id,))
        history = [dict(row) for row in cursor.fetchall()]
        
        # 2?ˆœ?œ„: ê²°ê³¼ê°? ?—†?œ¼ë©? group_name?œ¼ë¡? ì¡°íšŒ (êµ¬ë²„? „ ?˜¸?™˜)
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
        HIGH_RISK_KEYWORDS = ['?ž?™ì°¨ë???’ˆ', 'ê¸ˆì†ê°?ê³?', '?™”?•™', 'ê³ ë¬´', '?”Œ?¼?Š¤?‹±', 'ë¬¼ë¥˜ì°½ê³ ', 'ëª©ìž¬', '?š©? ‘']
        risk_conditions = " OR ".join([f"industry_name LIKE '%{k}%'" for k in HIGH_RISK_KEYWORDS])
        
        # Region Mapping
        region_map = {
            '?„œ?š¸': ['?„œ?š¸'], 'ê²½ê¸°': ['ê²½ê¸°', 'ê²½ê¸°?„'], '?¸ì²?': ['?¸ì²?', '?¸ì²œê´‘?—­?‹œ'],
            'ê°•ì›': ['ê°•ì›', 'ê°•ì›?Š¹ë³„ìžì¹˜ë„'], 'ì¶©ì²­': ['ì¶©ë‚¨', 'ì¶©ë¶'], '???? „': ['???? „'],
            'ë¶??‚°': ['ë¶??‚°'], '?š¸?‚°': ['?š¸?‚°', '?š¸?‚°ê´‘ì—­?‹œ'], '???êµ?': ['???êµ?'],
            'ê´‘ì£¼': ['ê´‘ì£¼'], '? „?‚¨': ['? „?‚¨'], '? „ë¶?': ['? „ë¶?', '? „ë¶íŠ¹ë³„ìžì¹˜ë„'],
            'ê²½ë‚¨': ['ê²½ë‚¨'], 'ê²½ë¶': ['ê²½ë¶'], '? œì£?': ['? œì£?', '? œì£¼íŠ¹ë³„ìžì¹˜ë„'], '?„¸ì¢?': ['?„¸ì¢?']
        }
        
        total_created = 0
        total_groups = 0
        
        for region_name, db_regions in region_map.items():
            filter_sql = ""
            if category == 'GENERAL':
                filter_sql = """
                    AND company_size NOT IN ('???ê¸°ì—…', 'ì¤‘ê²¬ê¸°ì—…')
                    AND company_name NOT LIKE '%(?‚¬)%'
                    AND company_name NOT LIKE '%?‚¬?‹¨ë²•ì¸%'
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
                
                # Naming: ì§??—­_[? œì¡?_]100_?ˆœë²?
                industry_tag = "? œì¡?_" if has_high_risk else ""
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
    ?™¸ë¶? ë¦¬í¬?Š¸(CSV ?“±)ë¡œë???„° ? „?‹¬ë°›ì?? ????Ÿ‰?˜ ë°œì†¡ ê²°ê³¼ë¥? ?‹œ?Š¤?…œ?— ?¼ê´? ë°˜ì˜?•©?‹ˆ?‹¤.
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
            
            # 1. Company_Basic ?…Œ?´ë¸? ?—…?°?´?Š¸ (ê¸?ë¡œë²Œ ?ƒ?ƒœ)
            usable = 1 if status == 'SUCCESS' else 0
            if status == 'BOUNCE':
                fix_status = 0 # ë°˜ì†¡?´ë©? ?ˆ˜? • ëª¨ë“œ ì´ˆê¸°?™” (?ˆ˜? •????ƒ?œ¼ë¡? ?‘œ?‹œ)
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
            
            # 2. ê´?? ¨ ë¡œê·¸ê°? ?žˆ?‹¤ë©? ìµœê·¼ ë¡œê·¸?„ ?—…?°?´?Š¸ (ê°??ž¥ ìµœê·¼ ë°œì†¡ê±? 1ê±?)
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

# ???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
# ?Ÿ“? ë°˜ì†¡ ë©”ì¼ ?ž?™ ê°ì?? & DB ?—…?°?´?Š¸ (IMAP ê¸°ë°˜)
# ???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

class EmailReceiver:
    """Gmail/Naver ?“±?˜ IMAP?„ ?†µ?•´ ë°˜ì†¡(bounce) ë©”ì¼?„ ê°ì???•©?‹ˆ?‹¤."""

    def __init__(self, imap_server, imap_port, email_addr, password):
        self.imap_server = imap_server
        self.imap_port = int(imap_port or 993)
        self.email_addr = email_addr
        self.password = password

    def connect(self):
        """IMAP ?„œë²„ì— ?—°ê²°í•˜ê³? mail ê°ì²´ë¥? ë°˜í™˜?•©?‹ˆ?‹¤."""
        if self.imap_port == 993:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
        else:
            mail = imaplib.IMAP4(self.imap_server, self.imap_port)
        mail.login(self.email_addr, self.password)
        return mail

    def check_bounces(self, since_date: str):
        """
        since_date('YYYY-MM-DD') ?´?›„ ë°›ì???Ž¸ì§??•¨?—?„œ ë°˜ì†¡ ë©”ì¼?„ ì°¾ì•„
        ë°˜ì†¡?œ ?´ë©”ì¼ ì£¼ì†Œ ëª©ë¡(?†Œë¬¸ìž set)?„ ë°˜í™˜?•©?‹ˆ?‹¤.
        """
        bounced = set()
        mail = None
        try:
            try:
                mail = self.connect()
            except imaplib.IMAP4.error as e:
                raise Exception(f"IMAP ?¸ì¦? ?‹¤?Œ¨: {str(e)}. ë¹„ë??ë²ˆí˜¸ ?˜?Š” IMAP ?„œë²? ?„¤? •?„ ?™•?¸?•´ì£¼ì„¸?š”.")
            except Exception as e:
                raise Exception(f"IMAP ?—°ê²? ?‹¤?Œ¨ ({self.imap_server}:{self.imap_port}): {str(e)}")
            
            # Gmail?˜ ê²½ìš° "[Gmail]/All Mail" (? „ì²´ë³´ê´??•¨)?„ ?š°?„  ?‹œ?„ (ê°??ž¥ ?™•?‹¤?•¨)
            # ?‹¤ë¥? ?„œë²„ëŠ” INBOXë¥? ê¸°ë³¸?œ¼ë¡? ?‚¬?š©
            is_gmail = 'gmail' in self.imap_server.lower()
            target_folders = []
            if is_gmail:
                target_folders = ['"[Gmail]/All Mail"', 'INBOX', '"[Gmail]/Spam"', 'INBOX.Junk']
            else:
                target_folders = ['INBOX', 'Spam', 'Junk']

            for folder in target_folders:
                try:
                    # ?´?” ?„ ?ƒ (Gmail?˜ ê²½ìš° ?˜ë¬? ëª…ì¹­?´ ?•œê¸? ê³„ì •?—?„œ?„ ?ž‘?™?•¨)
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

                            # ë°œì‹ ?žê°? ë°˜ì†¡ ?‹œ?Š¤?…œ?¸ì§? ?™•?¸
                            sender = str(msg.get('From', '')).lower()
                            subject_raw = str(msg.get('Subject', '')).lower()
                            is_bounce = any(kw in sender for kw in [
                                'mailer-daemon', 'postmaster', 'delivery', 'noreply', 'no-reply'
                            ]) or any(kw in subject_raw for kw in [
                                'delivery status', 'undeliverable', 'returned mail',
                                'failure notice', 'delivery failure', 'mail delivery failed',
                                'ë°˜ì†¡', '? „?‹¬ ?‹¤?Œ¨', 'delivery notification'
                            ])

                            if not is_bounce:
                                continue

                            # ë©”ì¼ ë³¸ë¬¸?—?„œ ?´ë©”ì¼ ì£¼ì†Œ ì¶”ì¶œ
                            content = self._extract_text(msg)
                            found = re.findall(
                                r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', content
                            )
                            for addr in found:
                                addr_lower = addr.lower()
                                # ?žê¸? ?ž?‹  ì£¼ì†Œ?‚˜ ?‹œ?Š¤?…œ ì£¼ì†Œ ? œ?™¸
                                if addr_lower != self.email_addr.lower() and \
                                   not any(kw in addr_lower for kw in ['mailer-daemon', 'postmaster']):
                                    bounced.add(addr_lower)
                        except Exception as e:
                            print(f"[EmailReceiver] ë©”ì¼ ?ŒŒ?‹± ?˜¤ë¥?: {e}")
                            continue

                except Exception as fe:
                    print(f"[EmailReceiver] ?´?” {folder} ì²˜ë¦¬ ì¤? ?˜¤ë¥?: {fe}")
                    continue

            mail.logout()
        except Exception as e:
            print(f"[EmailReceiver] IMAP ?—°ê²?/ê²??ƒ‰ ?˜¤ë¥?: {e}")
            raise
        finally:
            try:
                if mail:
                    mail.logout()
            except:
                pass

        return bounced

    def _extract_text(self, msg):
        """?´ë©”ì¼ ë©”ì‹œì§??—?„œ ?…?Š¤?Š¸ ?‚´?š©?„ ì¶”ì¶œ?•©?‹ˆ?‹¤."""
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
    IMAP?œ¼ë¡? ë°˜ì†¡ ë©”ì¼?„ ?™•?¸?•œ ?’¤ DBë¥? ?—…?°?´?Š¸?•©?‹ˆ?‹¤.

    ì²˜ë¦¬ ?ë¦?:
    1. smtp_configs?—?„œ IMAP ?„¤? • ì¡°íšŒ
    2. EmailReceiverë¡? ë°›ì???Ž¸ì§??•¨ ë°˜ì†¡ ë©”ì¼ ?ŒŒ?‹±
    3. email_send_log?—?„œ ?•´?‹¹ ?´ë©”ì¼ ì£¼ì†Œ?˜ ? ˆì½”ë“œë¥? BOUNCEë¡? ë³?ê²?
    4. Company_Basic.email_usable = 0, last_send_status = 'BOUNCE' ë¡? ?„¤? •
    5. send_batches?˜ fail_count / success_count ?ž¬ì§‘ê³„

    Returns dict: {success, bounced_count, updated_log_count, message}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. SMTP ?„¤? • ì¡°íšŒ
        cursor.execute('SELECT * FROM smtp_configs WHERE config_id = ?', (smtp_config_id,))
        config = cursor.fetchone()
        if not config:
            return {'success': False, 'message': 'SMTP ?„¤? •?„ ì°¾ì„ ?ˆ˜ ?—†?Šµ?‹ˆ?‹¤.'}

        imap_server = config['imap_server'] if config['imap_server'] else 'imap.gmail.com'
        imap_port   = config['imap_port']   if config['imap_port']   else 993

        # 2. ë°˜ì†¡ ë©”ì¼ ê°ì??
        receiver = EmailReceiver(
            imap_server=imap_server,
            imap_port=imap_port,
            email_addr=config['sender_email'],
            password=config['sender_password']
        )
        bounced_emails = receiver.check_bounces(since_date)
        print(f"[check_bounce] ê°ì???œ ë°˜ì†¡ ?´ë©”ì¼: {bounced_emails}")

        if not bounced_emails:
            return {
                'success': True,
                'bounced_count': 0,
                'updated_log_count': 0,
                'message': 'ë°˜ì†¡?œ ?´ë©”ì¼?´ ?—†?Šµ?‹ˆ?‹¤. (ë°›ì???Ž¸ì§??•¨ ?™•?¸ ?™„ë£?)'
            }

        # 3. email_send_log ?—?„œ ?•´?‹¹ ?‚ ì§? ?´?›„ ë°œì†¡?œ ? ˆì½”ë“œ ì¤? ë°˜ì†¡ ?´ë©”ì¼ ?†’ BOUNCE
        updated_log = 0
        for email_addr in bounced_emails:
            cursor.execute('''
                UPDATE email_send_log
                SET status = 'BOUNCE', error_msg = 'ë°˜ì†¡(?ˆ˜?‹  ë¶ˆê??) - IMAP ?ž?™ ê°ì??'
                WHERE LOWER(email) = ?
                  AND sent_at >= ?
                  AND status = 'SUCCESS'
            ''', (email_addr.lower(), since_date + ' 00:00:00'))
            updated_log += cursor.rowcount

        # 4. Company_Basic ?—…?°?´?Š¸: email_usable=0, ?ƒ?ƒœ='BOUNCE'
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

        # 5. send_batches ?ž¬ì§‘ê³„ (since_date ?´?›„ ë°°ì¹˜ë§?)
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
                f'ë°˜ì†¡ ê°ì?? ?™„ë£?: {len(bounced_emails)}ê°? ?´ë©”ì¼ ë°˜ì†¡ ?™•?¸, '
                f'{updated_log}ê±? ë¡œê·¸ ?—…?°?´?Š¸, '
                f'???ê²? ê·¸ë£¹ ë°œì†¡ ë¶ˆê?? ì²˜ë¦¬ ?™„ë£?'
            )
        }

    except Exception as e:
        conn.rollback()
        print(f"[check_bounce_and_update] Error: {e}")
        return {'success': False, 'message': f'ë°˜ì†¡ ?™•?¸ ?˜¤ë¥?: {str(e)}'}
    finally:
        conn.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print(" [?Ÿ”? QUANTUM EMAIL SERVICE ENGINE V2.0 ]")
    print("="*60)
    print("  ?— ?—”ì§? ?ƒ?ƒœ: ê°??™ ì¤?ë¹? ?™„ë£? (ONLINE/READY)")
    print("  ?— ?˜„?ž¬ ëª¨ë“œ: ?????? ?”„ë¦¬ë?¸ì—„ ?¼?´ë¸ŒëŸ¬ë¦? ? „?š©")
    print("  ?— ?—°?™ ëª¨ë“ˆ: web_app.py / email_management.html")
    print("-" * 60)
    print("  ??? ?‹œ?Š¤?…œ ê°??™?„ ?œ„?•´ ?„°ë¯¸ë„?—?„œ ?•„?ž˜ ëª…ë ¹?„ ?‹¤?–‰?•˜?‹­?‹œ?˜¤:")
    print("  > python web_app.py")
    print("="*60 + "\n")
