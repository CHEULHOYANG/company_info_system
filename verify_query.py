
import sqlite3
import os

DB_PATH = 'g:/company_project_system/company_database.db'

def check_query():
    if not os.path.exists(DB_PATH):
        print("❌ DB not found")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("--- 1. Check Total Count ---")
    cursor.execute("SELECT COUNT(*) FROM individual_business_owners")
    print(f"Total rows: {cursor.fetchone()[0]}")

    print("\n--- 2. Simulate Search Query (Current Logic) ---")
    # This mimics the current web_app.py logic
    query = "SELECT * FROM individual_business_owners WHERE 1=1"
    params = []
    
    # User ID simulation (assuming general user or admin)
    user_id = 'test_user' 
    # Logic: AND (assigned_user_id IS NULL OR assigned_user_id = ? OR status = '접촉해제')
    query += " AND (assigned_user_id IS NULL OR assigned_user_id = ? OR status = '접촉해제')"
    params.append(user_id)
    
    # Financial Year simulation
    financial_year = '2024' # User wants this default
    # Current code has: AND financial_year = ?
    # But user complained it's not showing. Maybe because data is NULL or not 2024?
    
    print(f"Testing Financial Year = '{financial_year}'")
    test_query = query + " AND financial_year = ?"
    test_params = params + [financial_year]
    
    cursor.execute(test_query, test_params)
    rows = cursor.fetchall()
    print(f"Rows with exact match '2024': {len(rows)}")

    print("\n--- 3. Test proposed logic (>= 2024) ---")
    # Proposed: AND CAST(financial_year AS INTEGER) >= ?
    prop_query = query + " AND CAST(financial_year AS INTEGER) >= ?"
    prop_params = params + [2024]
    
    cursor.execute(prop_query, prop_params)
    rows = cursor.fetchall()
    print(f"Rows with >= 2024: {len(rows)}")
    
    # Show some sample financial years
    print("\n--- Sample Financial Years in DB ---")
    cursor.execute("SELECT id, company_name, financial_year FROM individual_business_owners LIMIT 10")
    for r in cursor.fetchall():
        print(f"ID: {r['id']}, Name: {r['company_name']}, FY: {r['financial_year']}")

    conn.close()

if __name__ == "__main__":
    check_query()
