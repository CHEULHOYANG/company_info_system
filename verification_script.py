
import os
import sqlite3

from flask import session
import web_app

# --- Configuration ---
TEST_DB = f'test_access_control_{os.getpid()}.db'
# No need to remove checking since it's unique


# Override DB Path
web_app.DB_PATH = os.path.abspath(TEST_DB)

# Ensure DB directory exists
os.makedirs(os.path.dirname(web_app.DB_PATH), exist_ok=True)

# Helper to verify standard tables exist
def init_db():
    print("Populating Test DB...")
    # Initialize implementation tables
    web_app.init_user_tables()
    web_app.init_pipeline_tables()
    web_app.init_business_tables()
    
    conn = web_app.get_db_connection()
    c = conn.cursor()
    
    # Force Create Users Table (Fall back if init failed)
    c.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            user_level TEXT NOT NULL,
            user_level_name TEXT NOT NULL,
            branch_code TEXT NOT NULL,
            branch_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            gender TEXT,
            birth_date TEXT,
            status TEXT DEFAULT 'ACTIVE',
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            password_changed_date TEXT,
            updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT,
            email TEXT
        )
    ''')
    
    # Force Create Company_Basic Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Company_Basic (
            biz_no TEXT PRIMARY KEY,
            company_name TEXT,
            representative_name TEXT,
            establish_date TEXT,
            company_size TEXT,
            industry_name TEXT,
            region TEXT,
            address TEXT
        )
    ''')
    
    # Force Create Contact_History Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Contact_History (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            biz_no TEXT,
            contact_datetime TEXT,
            contact_type TEXT,
            contact_person TEXT,
            memo TEXT,
            registered_by TEXT,
            registered_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Force Create Company_Financial Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Company_Financial (
            biz_no TEXT,
            fiscal_year TEXT,
            total_assets INTEGER,
            sales_revenue INTEGER,
            retained_earnings INTEGER
        )
    ''')
    
    # 1. Create Users
    users = [
        ('ct0001', 'pass', 'Partner1', 'N'),
        ('ct0002', 'pass', 'Partner2', 'N'),
        ('ct0003', 'pass', 'Loner', 'N')
    ]
    for uid, pw, name, lvl in users:
        c.execute("INSERT OR IGNORE INTO Users (user_id, password, name, user_level, user_level_name, branch_code, branch_name, phone) VALUES (?, ?, ?, ?, 'General', 'B1', 'Main', '010-0000-0000')", (uid, pw, name, lvl))
        
    # 2. Create Companies (Basic Info)
    # biz_no: 101 (Partner1's Pipe), 102 (Partner2's Pipe), 103 (Loner's Pipe), 104 (Free)
    companies = [
        ('101', 'CompanyA_P1'),
        ('102', 'CompanyB_P2'),
        ('103', 'CompanyC_L3'),
        ('104', 'CompanyD_Free')
    ]
    for bno, name in companies:
        c.execute("INSERT OR IGNORE INTO Company_Basic (biz_no, company_name) VALUES (?, ?)", (bno, name))
        # Need also Companies table for search? query_companies_data uses Company_Basic.
        # But wait, query_companies_data selects from Company_Basic b.
        pass

    # 3. Register Pipeline (managed_companies)
    # 101 -> ct0001
    # 102 -> ct0002
    # 103 -> ct0003
    # 104 -> None
    pipeline = [
        ('101', 'ct0001'),
        ('102', 'ct0002'),
        ('103', 'ct0003')
    ]
    for bno, mgr in pipeline:
        c.execute('''
            INSERT INTO managed_companies (biz_reg_no, manager_id, status, keyman_name, created_at, updated_at)
            VALUES (?, ?, 'prospect', 'Keyman', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (bno, mgr))
        
    # 4. Contact History
    # ct0001 registers contact for 101
    c.execute("INSERT INTO Contact_History (biz_no, contact_person, registered_by, contact_datetime) VALUES ('101', 'PersonA', 'ct0001', '2025-01-01 10:00:00')")
    
    conn.commit()
    conn.close()
    print("Test DB Populated.")

def test_pipeline_logic():
    client = web_app.app.test_client()
    
    print("\n--- Testing Pipeline Visibility ---")
    
    # Case A: ct0001 (should see 101 and 102)
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_id'] = 'ct0001'
        sess['user_level'] = 'N'
        
    resp = client.get('/api/pipeline/dashboard')
    data = resp.json['data']['all_companies']
    biz_nos = [item['biz_reg_no'] for item in data]
    print(f"ct0001 sees: {biz_nos}")
    
    if '101' in biz_nos and '102' in biz_nos:
        print("[PASS] ct0001 sees both own and partner's companies.")
    else:
        print("[FAIL] ct0001 missing companies.")
        
    if '103' not in biz_nos:
        print("[PASS] ct0001 does not see ct0003's company.")
    else:
        print("[FAIL] ct0001 sees ct0003's company!")

    # Case B: ct0003 (should see only 103)
    with client.session_transaction() as sess:
        sess['user_id'] = 'ct0003'
        
    resp = client.get('/api/pipeline/dashboard')
    data = resp.json['data']['all_companies']
    biz_nos = [item['biz_reg_no'] for item in data]
    print(f"ct0003 sees: {biz_nos}")
    
    if '103' in biz_nos and len(biz_nos) == 1:
        print("[PASS] ct0003 sees only own company.")
    else:
        print(f"[FAIL] ct0003 has unexpected visibility: {biz_nos}")

def test_search_exclusion():
    client = web_app.app.test_client()
    print("\n--- Testing Search Exclusion ---")
    
    # Case A: ct0003 searching
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_id'] = 'ct0003'
        sess['user_level'] = 'N'
        
    # Search for Co A (101) -> Should be hidden
    resp = client.get('/api/companies?company_name=CompanyA_P1')
    # Response structure: {'companies': [...], ...}
    # Note: get_companies returns json.
    results = resp.json.get('companies', [])
    print(f"ct0003 search for CompanyA_P1 result count: {len(results)}")
    
    if len(results) == 0:
        print("[PASS] CompanyA_P1 is hidden from ct0003.")
    else:
        print("[FAIL] ct0003 found CompanyA_P1!")
        
    # Search for Co C (103 - Own) -> Should be visible
    resp = client.get('/api/companies?company_name=CompanyC_L3')
    results = resp.json.get('companies', [])
    print(f"ct0003 search for CompanyC_L3 result count: {len(results)}")
    if len(results) > 0:
        print("[PASS] ct0003 found own company.")
    else:
        print("[FAIL] ct0003 cannot find own company!")

    # Search for Co D (104 - Free) -> Should be visible
    resp = client.get('/api/companies?company_name=CompanyD_Free')
    results = resp.json.get('companies', [])
    if len(results) > 0:
        print("[PASS] Free company is visible.")
    else:
        print("[FAIL] Free company not found.")
        
def test_contact_history():
    client = web_app.app.test_client()
    print("\n--- Testing Contact History ---")
    
    # Case: ct0002 checks contact history (registered by ct0001)
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_id'] = 'ct0002'
        sess['user_level'] = 'N'
        
    # Endpoint: /api/history_search
    # No filters -> default behavior
    resp = client.get('/api/history_search')
    data = resp.json
    # Should see record by ct0001
    registrants = [item['registered_by'] for item in data]
    print(f"ct0002 history sees registrants: {registrants}")
    
    if 'ct0001' in registrants:
         print("[PASS] ct0002 sees ct0001's history.")
    else:
         print("[FAIL] ct0002 cannot see ct0001's history.")

if __name__ == "__main__":
    try:
        init_db()
        test_pipeline_logic()
        test_search_exclusion()
        test_contact_history()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
            pass
