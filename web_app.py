# -*- coding: cp949 -*-
import os
import sqlite3
import io
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, Response
from datetime import datetime
import pandas as pd
import math
import csv
from werkzeug.utils import secure_filename
from jinja2 import FileSystemLoader, TemplateNotFound

# --- 커스텀 템플릿 로더 (CP949 지원) ---
class CP949FileSystemLoader(FileSystemLoader):
    def get_source(self, environment, template):
        # 파일 경로 찾기
        for searchpath in self.searchpath:
            filename = os.path.join(searchpath, template)
            if os.path.exists(filename):
                # CP949로 먼저 시도, 실패하면 UTF-8로 시도
                try:
                    with open(filename, 'r', encoding='cp949') as f:
                        source = f.read()
                except UnicodeDecodeError:
                    with open(filename, 'r', encoding='utf-8') as f:
                        source = f.read()
                
                mtime = os.path.getmtime(filename)
                def uptodate():
                    try:
                        return os.path.getmtime(filename) == mtime
                    except OSError:
                        return False
                return source, filename, uptodate
        
        raise TemplateNotFound(template)

# --- 기본 설정 ---
app = Flask(__name__)
app.secret_key = 'your_very_secret_key_12345'

# 커스텀 템플릿 로더 설정
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.jinja_loader = CP949FileSystemLoader(template_dir)

# DB 경로 설정 (기존 데이터 보존하면서 GitHub 업데이트 시 DB 보존)
app_dir = os.path.dirname(os.path.abspath(__file__))

# render.com에서는 환경변수 RENDER가 설정됨
if os.environ.get('RENDER'):
    # render.com 서버 환경
    
    # 1순위: 기존 DB 파일이 있으면 계속 사용 (데이터 보존)
    existing_db = os.path.join(app_dir, 'company_database.db')
    if os.path.exists(existing_db):
        DB_PATH = existing_db
        print(f"Using existing DB: {DB_PATH}")
    else:
        # 2순위: 기존 DB가 없으면 data 폴더에 새로 생성
        db_dir = os.path.join(app_dir, 'data')
        os.makedirs(db_dir, exist_ok=True)
        DB_PATH = os.path.join(db_dir, 'company_info.db')
        print(f"Creating new DB: {DB_PATH}")
else:
    # 로컬 개발 환경 - 기존 파일 사용
    DB_PATH = os.path.join(app_dir, 'company_database.db')
    print(f"Local DB: {DB_PATH}")

# --- DB 연결 함수 및 사용자 계정 ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 사용자 테이블 초기화 함수
def init_user_tables():
    """사용자 관리 테이블들을 초기화합니다."""
    conn = get_db_connection()
    try:
        # SQL 파일 읽기 및 실행
        sql_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_user_table.sql')
        if os.path.exists(sql_file_path):
            try:
                # CP949 인코딩으로 먼저 시도
                with open(sql_file_path, 'r', encoding='cp949') as f:
                    sql_script = f.read()
            except UnicodeDecodeError:
                # UTF-8로 재시도
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
            
            # 각 SQL 문을 분리하여 실행
            for statement in sql_script.split(';'):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)
            conn.commit()
            print("User tables initialized successfully")
        else:
            print("SQL file not found, creating minimal user table")
            # 최소한의 사용자 테이블 생성
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Users (
                    user_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    user_level TEXT NOT NULL CHECK (user_level IN ('V', 'S', 'M', 'N')),
                    user_level_name TEXT NOT NULL,
                    branch_code TEXT NOT NULL,
                    branch_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    gender TEXT CHECK (gender IN ('M', 'F')),
                    birth_date TEXT,
                    status TEXT DEFAULT 'ACTIVE',
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 기본 관리자 계정 생성
            conn.execute('''
                INSERT OR REPLACE INTO Users 
                (user_id, password, name, user_level, user_level_name, branch_code, branch_name, phone) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('ct0001', 'ych1123!', '양철호', 'V', '메인관리자', 'EA3000', '중앙지점', '010-1234-5678'))
            conn.commit()
    except Exception as e:
        print(f"Error initializing user tables: {e}")
    finally:
        conn.close()

# 사용자 인증 함수
def authenticate_user(user_id, password):
    """사용자 인증을 수행합니다."""
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT * FROM Users WHERE user_id = ? AND status = 'ACTIVE'", 
            (user_id,)
        ).fetchone()
        
        if user and user['password'] == password:
            # 마지막 로그인 시간 업데이트
            conn.execute(
                "UPDATE Users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            return dict(user)
        return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    finally:
        conn.close()

# 사용자 정보 조회 함수
def get_user_info(user_id):
    """사용자 정보를 조회합니다."""
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT * FROM Users WHERE user_id = ? AND status = 'ACTIVE'", 
            (user_id,)
        ).fetchone()
        return dict(user) if user else None
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None
    finally:
        conn.close()

# 권한 확인 함수
def check_permission(user_level, required_level):
    """사용자 권한을 확인합니다."""
    level_hierarchy = {'V': 4, 'S': 3, 'M': 2, 'N': 1}
    return level_hierarchy.get(user_level, 0) >= level_hierarchy.get(required_level, 0)

# 앱 시작 시 사용자 테이블 초기화
init_user_tables()

# --- 비상장 주식 가치 계산 ---
def calculate_unlisted_stock_value(financial_data):
    """
    필요한 재무 항목:
    - total_assets: 자산총계
    - total_liabilities: 부채총계
    - net_income: 순이익(최근 3년 평균)
    - shares_issued_count: 발행주식수(없으면 자본금/5000)
    - capital_stock_value: 자본금
    """
    if not financial_data:
        return {}
    df_financial = pd.DataFrame(financial_data)
    if df_financial.empty:
        return {}

    latest_data = df_financial.sort_values(by='fiscal_year', ascending=False).iloc[0]

    total_assets = float(latest_data.get('total_assets') or 0)
    total_liabilities = float(latest_data.get('total_liabilities') or 0)

    # 최근 3년 평균 순이익
    net_income_3y_avg = pd.to_numeric(df_financial['net_income'], errors='coerce').mean()
    if pd.isna(net_income_3y_avg):
        net_income_3y_avg = 0

    asset_value = total_assets - total_liabilities
    profit_value = net_income_3y_avg / 0.1 if net_income_3y_avg else 0

    calculated_value = (asset_value * 2 + profit_value * 3) / 5

    total_shares = float(latest_data.get('shares_issued_count') or 0)
    if total_shares <= 1:
        capital_stock = float(latest_data.get('capital_stock_value') or 0)
        if capital_stock > 0:
            total_shares = capital_stock / 5000
        else:
            total_shares = 1
    if total_shares == 0:
        total_shares = 1

    stock_value = calculated_value / total_shares if total_shares else 0

    return {
        "asset_value": asset_value,
        "profit_value": profit_value,
        "calculated_value": calculated_value,
        "total_shares_issued": total_shares,
        "estimated_stock_value": stock_value
    }

# --- 기업정보 데이터 조회 함수 추가 ---
def query_companies_data(args):
    conn = get_db_connection()
    query = """
        SELECT
            b.*,
            f.fiscal_year,
            f.total_assets,
            f.sales_revenue,
            f.retained_earnings
        FROM Company_Basic b
        LEFT JOIN (
            SELECT biz_no, fiscal_year, total_assets, sales_revenue, retained_earnings
            FROM Company_Financial
            WHERE (biz_no, fiscal_year) IN (
                SELECT biz_no, MAX(fiscal_year) FROM Company_Financial GROUP BY biz_no
            )
        ) f ON b.biz_no = f.biz_no
    """
    filters = []
    params = []
    if args.get('biz_no'):
        filters.append("b.biz_no LIKE ?")
        params.append(f"%{args.get('biz_no')}%")
    if args.get('company_name'):
        filters.append("b.company_name LIKE ?")
        params.append(f"%{args.get('company_name')}%")
    if args.get('industry_name'):
        filters.append("b.industry_name LIKE ?")
        params.append(f"%{args.get('industry_name')}%")
    if args.get('company_size') and args.get('company_size') != '전체':
        filters.append("b.company_size = ?")
        params.append(args.get('company_size'))
    # 지역(주소) 검색: 모든 키워드가 포함되어야 함
    if args.get('region'):
        region_keywords = [kw.strip() for kw in args.get('region').split() if kw.strip()]
        for kw in region_keywords:
            filters.append("b.address LIKE ?")
            params.append(f"%{kw}%")
    # 이익잉여금 min/max (retained_earnings, 백만단위 입력값을 실제 단위로 변환)
    if args.get('ret_min'):
        try:
            ret_min_val = int(args.get('ret_min')) * 1000000
            filters.append("f.retained_earnings >= ?")
            params.append(ret_min_val)
        except Exception:
            pass
    if args.get('ret_max'):
        try:
            ret_max_val = int(args.get('ret_max')) * 1000000
            filters.append("f.retained_earnings <= ?")
            params.append(ret_max_val)
        except Exception:
            pass
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY b.biz_no"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# --- 로그아웃 라우트 추가 ---
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

# --- 접촉이력 조회 라우트 추가 ---
@app.route('/history')
def history_search():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('history.html', user_name=session.get('user_name'))

# --- 로그인 라우트 추가 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        
        # DB 기반 사용자 인증
        user_info = authenticate_user(user_id, password)
        if user_info:
            session['logged_in'] = True
            session['user_id'] = user_id
            session['user_name'] = user_info['name']
            session['user_level'] = user_info['user_level']
            session['user_level_name'] = user_info['user_level_name']
            session['branch_code'] = user_info['branch_code']
            session['branch_name'] = user_info['branch_name']
            session['phone'] = user_info['phone']
            return redirect(url_for('main'))
        else:
            error = '아이디 또는 비밀번호가 올바르지 않습니다.'
    return render_template('login.html', error=error)

# --- index(홈) 페이지 라우트 추가 ---

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user_name = session.get('user_name')

    conn = get_db_connection()

    # 페이지네이션 설정
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    # Company_Basic 테이블로 변경
    total_companies = conn.execute('SELECT COUNT(*) FROM Company_Basic').fetchone()[0]
    total_pages = math.ceil(total_companies / per_page)

    companies = conn.execute('SELECT * FROM Company_Basic LIMIT ? OFFSET ?', (per_page, offset)).fetchall()

    # 접촉 이력 조회 권한 처리 로직
    user_level = session.get('user_level', 'N')
    contact_params = []
    contact_history_query = "SELECT * FROM Contact_History"
    
    # V(메인관리자), S(서브관리자)는 전체 이력 조회 가능
    if not check_permission(user_level, 'S'):
        contact_history_query += " WHERE registered_by = ?"
        contact_params.append(user_id)
    contact_history_query += " ORDER BY contact_datetime DESC"
    contact_history = conn.execute(contact_history_query, contact_params).fetchall()

    conn.close()

    return render_template('index.html',
                           user_name=user_name,
                           companies=companies,
                           total_pages=total_pages,
                           current_page=page)

@app.route('/main')
def main():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # 사용자 권한 정보를 템플릿에 전달
    user_data = {
        'user_name': session.get('user_name'),
        'user_level': session.get('user_level', 'N'),
        'user_level_name': session.get('user_level_name', '일반담당자'),
        'branch_name': session.get('branch_name', ''),
        'can_manage_users': check_permission(session.get('user_level', 'N'), 'S')
    }
    
    return render_template('main.html', **user_data)
# (불필요한 잘못된 들여쓰기 라인 제거)
# --- 접촉이력 데이터 조회 API 추가 ---
@app.route('/api/contact_history_csv', methods=['GET', 'POST'])
def contact_history_csv():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    if request.method == 'GET':
        # 조건 없이 전체 Contact_History를 CSV로 반환
        conn = get_db_connection()
        rows = conn.execute('SELECT history_id, contact_datetime, biz_no, contact_type, contact_person, memo, registered_by FROM Contact_History ORDER BY history_id').fetchall()
        conn.close()
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['history_id','contact_datetime','biz_no','contact_type','contact_person','memo','registered_by'])
        for row in rows:
            cw.writerow([row['history_id'], row['contact_datetime'], row['biz_no'], row['contact_type'], row['contact_person'], row['memo'], row['registered_by']])
        output = si.getvalue().encode('utf-8-sig')
        return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=contact_history.csv"})
    else:
        # 업로드: 기존 데이터 전체 삭제 후, 업로드된 CSV로 전체 대체
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': 'CSV 파일만 업로드 가능합니다.'}), 400
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)
        conn = get_db_connection()
        try:
            conn.execute('DELETE FROM Contact_History')
            inserted, updated = 0, 0
            for row in reader:
                if row.get('history_id'):
                    cur = conn.execute("SELECT 1 FROM Contact_History WHERE history_id = ?", (row['history_id'],))
                    if cur.fetchone():
                        conn.execute("UPDATE Contact_History SET contact_datetime=?, biz_no=?, contact_type=?, contact_person=?, memo=?, registered_by=? WHERE history_id = ?",
                            (row['contact_datetime'], row['biz_no'], row['contact_type'], row['contact_person'], row['memo'], row['registered_by'], row['history_id']))
                        updated += 1
                        continue
                conn.execute("INSERT INTO Contact_History (history_id, contact_datetime, biz_no, contact_type, contact_person, memo, registered_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (row.get('history_id'), row.get('contact_datetime'), row.get('biz_no'), row.get('contact_type'), row.get('contact_person'), row.get('memo'), row.get('registered_by')))
                inserted += 1
            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            conn.close()
        return jsonify({'success': True, 'inserted': inserted, 'updated': updated})
@app.route('/api/history_search')
def api_history_search():
    print(">>> /api/history_search 라우트 진입")  # 라우트 진입 확인용 로그
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session.get('user_id')
    print(f"접속 user_id: {user_id}")

    query = """
        SELECT
            h.history_id,
            h.contact_datetime,
            h.biz_no,
            b.company_name,
            h.contact_type,
            h.contact_person,
            h.memo,
            h.registered_by
        FROM Contact_History h
        LEFT JOIN Company_Basic b ON h.biz_no = b.biz_no
    """
    filters = []
    params = []

    search_user = request.args.get('registered_by')
    user_level = session.get('user_level', 'N')
    
    # 담당자ID가 명확히 입력된 경우만 해당 담당자 등록건만 조회
    if search_user is not None and search_user.strip() != "":
        filters.append("h.registered_by = ?")
        params.append(search_user.strip())
    else:
        # 담당자ID 미입력 시 권한에 따라 조회 범위 결정
        if check_permission(user_level, 'S'):  # V(메인관리자), S(서브관리자)
            # 전체 이력 조회 (필터 없음)
            pass
        else:
            # M(매니저), N(일반담당자)는 본인 등록건만 조회
            filters.append("h.registered_by = ?")
            params.append(user_id)

    if request.args.get('start_date'):
        filters.append("h.contact_datetime >= ?")
        params.append(request.args.get('start_date') + ' 00:00:00')
    if request.args.get('end_date'):
        filters.append("h.contact_datetime <= ?")
        params.append(request.args.get('end_date') + ' 23:59:59')
    if request.args.get('biz_no'):
        filters.append("h.biz_no LIKE ?")
        params.append(f"%{request.args.get('biz_no')}%")

    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY h.contact_datetime DESC"


    conn = get_db_connection()
    results = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(row) for row in results])

# ▼▼▼ [수정] get_companies 함수 ▼▼▼
@app.route('/api/companies')
def get_companies():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page
        
        all_data = query_companies_data(request.args)
        total_rows = len(all_data)
        
        has_next_page = total_rows > (offset + per_page)
        
        paginated_data = all_data.iloc[offset : offset + per_page].where(pd.notnull(all_data), None)
        
        return jsonify({
            'companies': paginated_data.to_dict('records'),
            'hasNextPage': has_next_page,
            'offset': offset,
            'totalRows': total_rows
        })
    except Exception as e:
        print(f"Error in get_companies: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/export_excel')
def export_excel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        import xlsxwriter  # ensure xlsxwriter is installed
        df = query_companies_data(request.args)
        if len(df) > 500:
            return "검색 결과가 500건을 초과합니다. 조건을 조정하여 500건 이하로 조회해주세요.", 400
        df.rename(columns={
            'biz_no': '사업자번호', 'company_name': '기업명', 'representative_name': '대표자명', 'phone_number': '전화번호',
            'company_size': '기업규모', 'address': '주소', 'industry_name': '업종명', 'fiscal_year': '최신결산년도',
            'total_assets': '자산총계', 'sales_revenue': '매출액', 'retained_earnings': '이익잉여금'
        }, inplace=True)
        excel_cols = ['사업자번호', '기업명', '대표자명', '전화번호', '기업규모', '주소', '업종명', '최신결산년도', '자산총계', '매출액', '이익잉여금']
        df_excel = df[[col for col in excel_cols if col in df.columns]]
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='기업정보')
        output.seek(0)
        return Response(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": "attachment;filename=company_data.xlsx"})
    except ImportError:
        return "엑셀 파일 생성에 필요한 'xlsxwriter' 패키지가 설치되어 있지 않습니다. 관리자에게 문의하세요.", 500
    except Exception as e:
        print(f"Error in export_excel: {e}")
        return f"엑셀 파일 생성 중 오류가 발생했습니다. 상세: {e}", 500

# ...existing code...
@app.route('/company/<biz_no>')
def company_detail(biz_no):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    source_page = request.args.get('source')
    is_popup = (source_page == 'history_popup')

    conn = get_db_connection()
    user_id = session.get('user_id')
    
    basic_query = """
    SELECT cb.*, cf.rating1, cb.group_transaction_yn, cb.gfc_transaction_yn
    FROM Company_Basic cb
    LEFT JOIN (SELECT biz_no, rating1, fiscal_year FROM Company_Financial ORDER BY fiscal_year DESC) AS cf ON cb.biz_no = cf.biz_no
    WHERE cb.biz_no = ? GROUP BY cb.biz_no
    """
    basic_info = conn.execute(basic_query, (biz_no,)).fetchone()
    
    financial_query = """
    SELECT fiscal_year, sales_revenue, net_income, total_assets, total_equity, retained_earnings, corporate_tax, 
           undistributed_retained_earnings, advances_paid, advances_received, shares_issued_count, total_liabilities,
           IFNULL(capital_stock_value, 0) as capital_stock_value
    FROM Company_Financial WHERE biz_no = ? ORDER BY fiscal_year DESC LIMIT 3
    """
    financial_info = conn.execute(financial_query, (biz_no,)).fetchall()
    
    representatives = conn.execute("SELECT name, birth_date, gender, is_gfc FROM Company_Representative WHERE biz_no = ?", (biz_no,)).fetchall()
    shareholders = conn.execute("SELECT * FROM Company_Shareholder WHERE biz_no = ?", (biz_no,)).fetchall()
    
    history_query = "SELECT * FROM Contact_History WHERE biz_no = ?"
    history_params = [biz_no]
    user_level = session.get('user_level', 'N')

    # 권한에 따른 접촉이력 조회 범위 설정
    if user_level == 'V':  # 메인관리자: 모든 이력
        pass
    elif user_level == 'S':  # 서브관리자: 관리자급 이력만
        history_query += " AND registered_by IN (SELECT user_id FROM Users WHERE user_level IN ('V', 'S'))"
    else:  # 매니저, 일반담당자: 본인 이력만
        history_query += " AND registered_by = ?"
        history_params.append(user_id)
    
    history_query += " ORDER BY contact_datetime DESC"
    contact_history = conn.execute(history_query, tuple(history_params)).fetchall()

    try:
        patents = conn.execute("SELECT * FROM Company_Patent WHERE biz_no = ?", (biz_no,)).fetchall()
    except sqlite3.OperationalError:
        patents = []
    
    try:
        additional_info_row = conn.execute("SELECT * FROM Company_Additional WHERE biz_no = ?", (biz_no,)).fetchone()
    except sqlite3.OperationalError:
        additional_info_row = None
    conn.close()

    additional_info = dict(additional_info_row) if additional_info_row else {}
    if additional_info:
        today_str = datetime.now().strftime('%Y-%m-%d')
        if additional_info.get('is_innobiz') == '1' and additional_info.get('innobiz_expiry_date') and additional_info['innobiz_expiry_date'] < today_str:
            additional_info['is_innobiz'] = '0'
        if additional_info.get('is_mainbiz') == '1' and additional_info.get('mainbiz_expiry_date') and additional_info['mainbiz_expiry_date'] < today_str:
            additional_info['is_mainbiz'] = '0'
        if additional_info.get('is_venture') == '1' and additional_info.get('venture_expiry_date') and additional_info['venture_expiry_date'] < today_str:
            additional_info['is_venture'] = '0'

    financial_data_for_calc = [dict(row) for row in financial_info] if financial_info else []
    stock_valuation = calculate_unlisted_stock_value(financial_data_for_calc)
    
    company_data = {
        'basic': dict(basic_info) if basic_info else {},
        'financials': [dict(row) for row in financial_info],
        'representatives': [dict(row) for row in representatives],
        'shareholders': [dict(row) for row in shareholders],
        'history': [dict(row) for row in contact_history],
        'patents': [dict(row) for row in patents],
        'additional': additional_info,
        'stock_valuation': stock_valuation
    }
    return render_template('detail.html', company=company_data, is_popup=is_popup)

@app.route('/api/contact_history', methods=['POST', 'PUT'])
def handle_contact_history():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    user_id = session.get('user_id', 'unknown')
    contact_datetime_str = data.get('contact_datetime')
    history_id = data.get('history_id')

    if not contact_datetime_str:
        return jsonify({"success": False, "message": "접촉일시를 입력해주세요."}), 400
    try:
        # ISO 형식의 날짜 문자열을 파싱 (timezone 정보 제거)
        if contact_datetime_str.endswith('Z'):
            contact_datetime_str = contact_datetime_str[:-1]
        elif '+' in contact_datetime_str:
            contact_datetime_str = contact_datetime_str.split('+')[0]
        elif contact_datetime_str.count(':') == 3:  # timezone offset 형태 처리
            contact_datetime_str = ':'.join(contact_datetime_str.split(':')[:3])
        
        submitted_dt = datetime.fromisoformat(contact_datetime_str.replace('Z', ''))
        now_dt = datetime.now()
        
        # 1분의 여유시간을 두어 네트워크 지연이나 시간 동기화 오차를 허용
        from datetime import timedelta
        if submitted_dt > (now_dt + timedelta(minutes=1)):
            return jsonify({"success": False, "message": "미래 날짜 및 시간으로 등록/수정할 수 없습니다."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "잘못된 날짜 형식입니다."}), 400

    formatted_datetime = contact_datetime_str.replace('T', ' ')
    conn = get_db_connection()
    try:
        biz_no = data.get('biz_no')
        contact_type = data.get('contact_type')
        contact_person = data.get('contact_person')
        memo = data.get('memo')
        
        if request.method == 'POST':
            conn.execute(
                """INSERT INTO Contact_History (biz_no, contact_datetime, contact_type, contact_person, memo, registered_by) VALUES (?, ?, ?, ?, ?, ?)""",
                (biz_no, formatted_datetime, contact_type, contact_person, memo, user_id)
            )
            new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
            return jsonify({"success": True, "message": "추가되었습니다.", "new_history_id": new_id})
        
        elif request.method == 'PUT':
            if not history_id:
                return jsonify({"success": False, "message": "수정할 이력 ID가 없습니다."}), 400
            conn.execute(
                "UPDATE Contact_History SET contact_datetime=?, contact_type=?, contact_person=?, memo=?, registered_by=? WHERE history_id = ?", 
                (formatted_datetime, contact_type, contact_person, memo, user_id, history_id)
            )
            conn.commit()
            return jsonify({"success": True, "message": "수정되었습니다."})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/contact_history/<int:history_id>', methods=['DELETE'])
def delete_contact_history(history_id):
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM Contact_History WHERE history_id = ?", (history_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 증여세 계산기 라우트 ---
@app.route('/gift_tax')
def gift_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('gift_tax.html', user_name=session.get('user_name'))

# --- 양도소득세 계산기 라우트 ---
@app.route('/transfer_tax')
def transfer_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('transfer_tax.html', user_name=session.get('user_name'))

# --- 종합소득세 계산기 라우트 ---
@app.route('/income_tax')
def income_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('income_tax.html', user_name=session.get('user_name'))

# --- 4대보험료 계산기 라우트 ---
@app.route('/social_ins_tax')
def social_ins_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('social_ins_tax.html', user_name=session.get('user_name'))


# --- 취득세 계산기 라우트 ---
@app.route('/acquisition_tax')
def acquisition_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('acquisition_tax.html', user_name=session.get('user_name'))

# --- 퇴직금 계산기 라우트 ---
@app.route('/retirement_pay')
def retirement_pay():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('retirement_pay.html', user_name=session.get('user_name'))


@app.route('/industrial_accident')
def industrial_accident():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('industrial_accident.html', user_name=session.get('user_name'))

# --- 사용자 관리 라우트 (메인관리자, 서브관리자만 접근 가능) ---
@app.route('/user_management')
def user_management():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_level = session.get('user_level', 'N')
    if not check_permission(user_level, 'S'):  # 서브관리자 이상만 접근 가능
        return "접근 권한이 없습니다.", 403
    
    return render_template('user_management.html', user_name=session.get('user_name'))

# --- 사용자 목록 API ---
@app.route('/api/users')
def get_users():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    if not check_permission(user_level, 'S'):
        return jsonify({"error": "Permission denied"}), 403
    
    conn = get_db_connection()
    try:
        users = conn.execute('''
            SELECT user_id, name, password, user_level, user_level_name, branch_code, branch_name, 
                   phone, gender, birth_date, status, last_login, created_date
            FROM Users ORDER BY user_level, user_id
        ''').fetchall()
        return jsonify([dict(user) for user in users])
    finally:
        conn.close()

# --- 사용자 추가/수정 API ---
@app.route('/api/users', methods=['POST', 'PUT'])
def manage_user():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    if not check_permission(user_level, 'S'):
        return jsonify({"error": "Permission denied"}), 403
    
    data = request.json
    conn = get_db_connection()
    
    try:
        if request.method == 'POST':
            # 사용자 추가
            conn.execute('''
                INSERT INTO Users 
                (user_id, password, name, user_level, user_level_name, branch_code, branch_name, 
                 phone, gender, birth_date, email, position, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['user_id'], data['password'], data['name'], data['user_level'], 
                data['user_level_name'], data['branch_code'], data['branch_name'],
                data['phone'], data.get('gender'), data.get('birth_date'), 
                data.get('email'), data.get('position'), data.get('status', 'ACTIVE')
            ))
            conn.commit()
            return jsonify({"success": True, "message": "사용자가 추가되었습니다."})
        
        elif request.method == 'PUT':
            # 사용자 수정
            conn.execute('''
                UPDATE Users SET 
                    name=?, user_level=?, user_level_name=?, branch_code=?, branch_name=?,
                    phone=?, gender=?, birth_date=?, email=?, position=?, status=?,
                    updated_date=CURRENT_TIMESTAMP
                WHERE user_id=?
            ''', (
                data['name'], data['user_level'], data['user_level_name'], 
                data['branch_code'], data['branch_name'], data['phone'], 
                data.get('gender'), data.get('birth_date'), data.get('email'), 
                data.get('position'), data.get('status'), data['user_id']
            ))
            conn.commit()
            return jsonify({"success": True, "message": "사용자 정보가 수정되었습니다."})
    
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 비밀번호 변경 API ---
@app.route('/api/users/<user_id>/password', methods=['PUT'])
def change_password(user_id):
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    current_user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    # 본인 비밀번호이거나 관리자 권한 필요
    if user_id != current_user_id and not check_permission(user_level, 'S'):
        return jsonify({"error": "Permission denied"}), 403
    
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if not new_password:
        return jsonify({"success": False, "message": "새 비밀번호를 입력해주세요."}), 400
    
    if new_password != confirm_password:
        return jsonify({"success": False, "message": "새 비밀번호가 일치하지 않습니다."}), 400
    
    conn = get_db_connection()
    try:
        # 본인 비밀번호 변경인 경우 현재 비밀번호 확인
        if user_id == current_user_id:
            if not current_password:
                return jsonify({"success": False, "message": "현재 비밀번호를 입력해주세요."}), 400
            
            current_user = conn.execute(
                "SELECT password FROM Users WHERE user_id = ?", (user_id,)
            ).fetchone()
            
            if not current_user or current_user['password'] != current_password:
                return jsonify({"success": False, "message": "현재 비밀번호가 일치하지 않습니다."}), 400
        
        # 비밀번호 업데이트
        conn.execute('''
            UPDATE Users SET 
                password=?, 
                password_changed_date=date('now'),
                updated_date=CURRENT_TIMESTAMP
            WHERE user_id=?
        ''', (new_password, user_id))
        conn.commit()
        return jsonify({"success": True, "message": "비밀번호가 변경되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)