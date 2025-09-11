import os
import sqlite3
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, Response
from datetime import datetime
import pandas as pd
import math
import io

# --- 기본 설정 ---
app = Flask(__name__)
app.secret_key = 'your_very_secret_key_12345'
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "company_database.db")

# --- 사용자 정보 ---
USERS = { 'ct0001': 'ych1123!', 'ct0002': None, 'ct0003': None, 'ct0004': None, 'ct0005': None }

def get_dynamic_password():
    return f"ctlove{datetime.now().strftime('%m%d')}"

# --- 데이터베이스 연결 ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- 비상장 주식 가치 계산 ---
def calculate_unlisted_stock_value(financial_data):
    if not financial_data: return {}
    df_financial = pd.DataFrame(financial_data)
    if df_financial.empty: return {}

    latest_data = df_financial.sort_values(by='fiscal_year', ascending=False).iloc[0]

    total_assets = float(latest_data.get('total_assets', 0) or 0)
    total_liabilities = float(latest_data.get('total_liabilities', 0) or 0)
    net_income_3y_avg = df_financial['net_income'].astype(float).mean()
    
    asset_value = total_assets - total_liabilities
    profit_value = net_income_3y_avg / 0.1
    
    calculated_value = (asset_value * 2 + profit_value * 3) / 5
    
    total_shares = float(latest_data.get('shares_issued_count', 1) or 1)
    
    stock_value = calculated_value / total_shares if total_shares else 0

    return {
        "asset_value": asset_value,
        "profit_value": profit_value,
        "calculated_value": calculated_value,
        "total_shares_issued": total_shares,
        "estimated_stock_value": stock_value
    }

# --- 데이터 처리 함수 (공통 로직) ---
def query_companies_data(args):
    conn = get_db_connection()
    
    base_query = "SELECT biz_no, company_name, representative_name, company_size, region, phone_number, industry_name FROM Company_Basic"
    
    where_clauses = []
    params = {}
    
    if company_name := args.get('company_name'):
        where_clauses.append("company_name LIKE :company_name")
        params['company_name'] = f"%{company_name}%"
    if biz_no := args.get('biz_no'):
        where_clauses.append("biz_no LIKE :biz_no")
        params['biz_no'] = f"%{biz_no}%"
    if industry_code := args.get('industry_code'):
        where_clauses.append("industry_code LIKE :industry_code")
        params['industry_code'] = f"%{industry_code}%"
    if industry_name := args.get('industry_name'):
        where_clauses.append("industry_name LIKE :industry_name")
        params['industry_name'] = f"%{industry_name}%"
    if region := args.get('region'):
        where_clauses.append("region LIKE :region")
        params['region'] = f"%{region}%"
    if (company_size := args.get('company_size')) and company_size != "전체":
        where_clauses.append("company_size = :company_size")
        params['company_size'] = company_size

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)
        
    df_basic = pd.read_sql_query(base_query, conn, params=params)

    if df_basic.empty:
        conn.close()
        return pd.DataFrame()

    biz_nos = df_basic['biz_no'].tolist()
    
    if not biz_nos:
        conn.close()
        return df_basic

    financial_query = f"SELECT * FROM Company_Financial WHERE biz_no IN ({','.join('?' for _ in biz_nos)})"
    df_financial = pd.read_sql_query(financial_query, conn, params=biz_nos)
    conn.close()

    if not df_financial.empty:
        df_financial_sorted = df_financial.sort_values('fiscal_year', ascending=False)
        latest_financials = df_financial_sorted.drop_duplicates('biz_no')
        
        df_merged = pd.merge(df_basic, latest_financials, on='biz_no', how='left')

        conditions = pd.Series([True] * len(df_merged))
        if ret_min := args.get('ret_min', type=int):
            conditions = conditions & (df_merged['retained_earnings'].fillna(0) >= ret_min * 1000000)
        if ret_max := args.get('ret_max', type=int):
            conditions = conditions & (df_merged['retained_earnings'].fillna(0) <= ret_max * 1000000)
        
        df_final = df_merged[conditions]

    else:
        df_final = df_basic
        if args.get('ret_min') or args.get('ret_max'):
            return pd.DataFrame()

    return df_final.sort_values('company_name')


# --- 라우팅 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        
        dynamic_password = get_dynamic_password()
        
        if user_id in USERS and (USERS[user_id] == password or password == dynamic_password):
            session['logged_in'] = True
            session['user_id'] = user_id
            return redirect(url_for('index'))
        else:
            error = '아이디 또는 비밀번호가 올바르지 않습니다.'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))
    
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/api/companies')
def get_companies():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
        
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    try:
        all_data = query_companies_data(request.args)
        
        total_rows = len(all_data)
        total_pages = math.ceil(total_rows / per_page) if total_rows > 0 else 1
        
        paginated_data = all_data.iloc[offset : offset + per_page]
        
        paginated_data = paginated_data.where(pd.notnull(paginated_data), None)

        return jsonify({
            'companies': paginated_data.to_dict('records'),
            'currentPage': page,
            'totalPages': total_pages,
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
        df = query_companies_data(request.args)
        
        df.rename(columns={
            'biz_no': '사업자번호', 'company_name': '기업명', 'representative_name': '대표자명', 'phone_number': '전화번호',
            'company_size': '기업규모', 'region': '지역', 'industry_name': '업종명', 'fiscal_year': '최신결산년도',
            'total_assets': '자산총계', 'sales_revenue': '매출액', 'retained_earnings': '이익잉여금',
            'net_income': '당기순이익'
        }, inplace=True)
        
        excel_cols = ['사업자번호', '기업명', '대표자명', '전화번호', '기업규모', '지역', '업종명', '최신결산년도', '자산총계', '매출액', '이익잉여금', '당기순이익']
        df_excel = df[[col for col in excel_cols if col in df.columns]]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='기업정보')
        
        output.seek(0)
        
        return Response(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": "attachment;filename=company_data.xlsx"})
    except Exception as e:
        print(f"Error in export_excel: {e}")
        return "엑셀 파일 생성 중 오류가 발생했습니다.", 500


@app.route('/company/<biz_no>')
def company_detail(biz_no):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    query = """
    SELECT cb.*, cf.rating1 
    FROM Company_Basic cb
    LEFT JOIN (
        SELECT biz_no, rating1, fiscal_year FROM Company_Financial
        ORDER BY fiscal_year DESC
    ) AS cf ON cb.biz_no = cf.biz_no
    WHERE cb.biz_no = ?
    GROUP BY cb.biz_no
    """
    basic_info = conn.execute(query, (biz_no,)).fetchone()
    
    financial_info = conn.execute("""
        SELECT 
            fiscal_year, sales_revenue, net_income, total_assets, total_equity, 
            retained_earnings, corporate_tax, undistributed_retained_earnings, 
            advances_paid, advances_received, shares_issued_count, total_liabilities
        FROM Company_Financial 
        WHERE biz_no = ? 
        ORDER BY fiscal_year DESC 
        LIMIT 3
    """, (biz_no,)).fetchall()
    
    representatives = conn.execute("SELECT * FROM Company_Representative WHERE biz_no = ?", (biz_no,)).fetchall()
    shareholders = conn.execute("SELECT * FROM Company_Shareholder WHERE biz_no = ?", (biz_no,)).fetchall()
    contact_history = conn.execute("SELECT * FROM Contact_History WHERE biz_no = ? ORDER BY contact_datetime DESC", (biz_no,)).fetchall()

    try:
        patents = conn.execute("SELECT * FROM Company_Patent WHERE biz_no = ?", (biz_no,)).fetchall()
    except sqlite3.OperationalError:
        patents = []

    conn.close()

    financial_data_for_calc = [dict(row) for row in financial_info] if financial_info else []
    stock_valuation = calculate_unlisted_stock_value(financial_data_for_calc)
    
    processed_financials = []
    for row in financial_info:
        new_row = dict(row)
        if 'fiscal_year' in new_row:
            new_row['year'] = new_row.pop('fiscal_year')
        processed_financials.append(new_row)

    company_data = {
        'basic': dict(basic_info) if basic_info else {},
        'financials': processed_financials,
        'representatives': [dict(row) for row in representatives],
        'shareholders': [dict(row) for row in shareholders],
        'history': [dict(row) for row in contact_history],
        'patents': [dict(row) for row in patents],
        'stock_valuation': stock_valuation
    }

    return render_template('detail.html', company=company_data)


# --- API (접촉이력 관리) ---
@app.route('/api/contact_history', methods=['POST'])
def add_contact_history():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    user_id = session.get('user_id', 'unknown')
    contact_datetime_str = data.get('contact_datetime')

    if not contact_datetime_str:
        return jsonify({"success": False, "message": "접촉일시를 입력해주세요."}), 400
    try:
        submitted_dt = datetime.fromisoformat(contact_datetime_str)
        if submitted_dt > datetime.now():
            return jsonify({"success": False, "message": "미래 날짜 및 시간으로 이력을 등록할 수 없습니다."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "잘못된 날짜 형식입니다."}), 400

    formatted_datetime = contact_datetime_str.replace('T', ' ')
    conn = get_db_connection()
    try:
        biz_no = data.get('biz_no')
        contact_type = data.get('contact_type')
        contact_person = data.get('contact_person')
        memo = data.get('memo')
        
        # [수정됨] DB 테이블 구조에 맞게 registration_date 컬럼 제거
        conn.execute(
            """INSERT INTO Contact_History (biz_no, contact_datetime, contact_type, contact_person, memo, registered_by) VALUES (?, ?, ?, ?, ?, ?)""",
            (biz_no, formatted_datetime, contact_type, contact_person, memo, user_id)
        )
        conn.commit()
        history_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return jsonify({"success": True, "new_history": {"history_id": history_id, "contact_datetime": submitted_dt.strftime('%Y-%m-%d %H:%M:%S'), "contact_type": contact_type, "contact_person": contact_person, "memo": memo, "registered_by": user_id}})
    except Exception as e:
        conn.rollback()
        # 오류 메시지를 클라이언트에게 더 명확하게 전달
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/contact_history/<int:history_id>', methods=['PUT'])
def update_contact_history(history_id):
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    user_id = session.get('user_id', 'unknown')
    contact_datetime_str = data.get('contact_datetime')
    if not contact_datetime_str:
        return jsonify({"success": False, "message": "접촉일시를 입력해주세요."}), 400
    try:
        submitted_dt = datetime.fromisoformat(contact_datetime_str)
        if submitted_dt > datetime.now():
            return jsonify({"success": False, "message": "미래 날짜 및 시간으로 이력을 수정할 수 없습니다."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "잘못된 날짜 형식입니다."}), 400
        
    formatted_datetime = contact_datetime_str.replace('T', ' ')
    conn = get_db_connection()
    try:
        contact_type = data.get('contact_type')
        contact_person = data.get('contact_person')
        memo = data.get('memo')
        
        conn.execute("UPDATE Contact_History SET contact_datetime=?, contact_type=?, contact_person=?, memo=?, registered_by=? WHERE history_id = ?", 
                     (formatted_datetime, contact_type, contact_person, memo, user_id, history_id))
        conn.commit()
        return jsonify({"success": True})
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)