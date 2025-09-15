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

    total_assets = float(latest_data.get('total_assets') or 0)
    total_liabilities = float(latest_data.get('total_liabilities') or 0)
    
    net_income_3y_avg = pd.to_numeric(df_financial['net_income'], errors='coerce').mean()
    if pd.isna(net_income_3y_avg):
        net_income_3y_avg = 0

    asset_value = total_assets - total_liabilities
    profit_value = net_income_3y_avg / 0.1
    
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

    stock_value = calculated_value / total_shares

    return {
        "asset_value": asset_value,
        "profit_value": profit_value,
        "calculated_value": calculated_value,
        "total_shares_issued": total_shares,
        "estimated_stock_value": stock_value
    }

# --- 데이터 처리 함수 (공통 로직) ---
def query_companies_data(filters):
    conn = get_db_connection()
    
    base_query = """
    SELECT
        cb.biz_no, cb.company_name, cb.representative_name, cb.company_size, 
        cb.address, cb.phone_number, cb.industry_name, cb.industry_code,
        cf.total_assets, cf.sales_revenue, cf.retained_earnings, cf.fiscal_year
    FROM
        Company_Basic AS cb
    LEFT JOIN (
        SELECT biz_no, MAX(fiscal_year) as max_year FROM Company_Financial GROUP BY biz_no
    ) AS latest_fy ON cb.biz_no = latest_fy.biz_no
    LEFT JOIN Company_Financial AS cf ON cb.biz_no = cf.biz_no AND cf.fiscal_year = latest_fy.max_year
    LEFT JOIN Company_Additional AS ca ON cb.biz_no = ca.biz_no
    """
    
    where_clauses, params = [], []
    if filters.get('company_name'): where_clauses.append("cb.company_name LIKE ?"); params.append(f"%{filters['company_name']}%")
    if filters.get('biz_no'): where_clauses.append("cb.biz_no LIKE ?"); params.append(f"%{filters['biz_no']}%")
    if filters.get('industry_code'): where_clauses.append("cb.industry_code LIKE ?"); params.append(f"%{filters['industry_code']}%")
    if filters.get('industry_name'): where_clauses.append("cb.industry_name LIKE ?"); params.append(f"%{filters['industry_name']}%")
    if filters.get('region'): where_clauses.append("cb.address LIKE ?"); params.append(f"%{filters['region']}%")
    
    company_size_filter = filters.get('company_size')
    if company_size_filter and company_size_filter != '전체':
        if company_size_filter == '기타':
            where_clauses.append("(cb.company_size IS NULL OR TRIM(cb.company_size) = '')")
        else:
            where_clauses.append("cb.company_size = ?")
            params.append(company_size_filter)

    if filters.get('ret_min'): where_clauses.append("cf.retained_earnings >= ?"); params.append(float(filters['ret_min']) * 1000000)
    if filters.get('ret_max'): where_clauses.append("cf.retained_earnings <= ?"); params.append(float(filters['ret_max']) * 1000000)
    if filters.get('research_institute') and filters['research_institute'] != '전체': 
        where_clauses.append("ca.has_research_institute = ?"); params.append('1' if filters['research_institute'] == '유' else '0')

    query = base_query
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    query += " ORDER BY cb.company_name"

    try:
        df = pd.read_sql_query(query, conn, params=params)
    except sqlite3.OperationalError as e:
        print(f"Query failed: {query}\nParams: {params}\nError: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    return df

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
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page
        all_data = query_companies_data(request.args)
        total_rows = len(all_data)
        total_pages = math.ceil(total_rows / per_page) if total_rows > 0 else 1
        paginated_data = all_data.iloc[offset : offset + per_page].where(pd.notnull(all_data), None)
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
    except Exception as e:
        print(f"Error in export_excel: {e}")
        return "엑셀 파일 생성 중 오류가 발생했습니다.", 500

@app.route('/company/<biz_no>')
def company_detail(biz_no):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    
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
    contact_history = conn.execute("SELECT * FROM Contact_History WHERE biz_no = ? ORDER BY contact_datetime DESC", (biz_no,)).fetchall()
    
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
    return render_template('detail.html', company=company_data)

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
        submitted_dt = datetime.fromisoformat(contact_datetime_str)
        if submitted_dt > datetime.now():
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
        
        if request.method == 'POST': # 신규 등록
            conn.execute(
                """INSERT INTO Contact_History (biz_no, contact_datetime, contact_type, contact_person, memo, registered_by) VALUES (?, ?, ?, ?, ?, ?)""",
                (biz_no, formatted_datetime, contact_type, contact_person, memo, user_id)
            )
            new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
            return jsonify({"success": True, "message": "추가되었습니다.", "new_history_id": new_id})
        
        elif request.method == 'PUT': # 수정
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
