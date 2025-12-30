import sqlite3
import os

DB_PATH = 'company_database.db'

def verify_db():
    print(f"Verifying database at {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check table existence
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='individual_business_owners';")
    if cursor.fetchone():
        print("[PASS] Table 'individual_business_owners' exists.")
    else:
        print("[FAIL] Table 'individual_business_owners' does NOT exist.")
        conn.close()
        return

    # Check columns (simple check)
    cursor.execute("PRAGMA table_info(individual_business_owners)")
    columns = [row[1] for row in cursor.fetchall()]
    expected_cols = ['company_name', 'representative_name', 'business_number', 'financial_year']
    missing = [col for col in expected_cols if col not in columns]
    
    if not missing:
        print("[PASS] Required columns present.")
    else:
        print(f"[FAIL] Missing columns: {missing}")

    # Check data count
    cursor.execute("SELECT COUNT(*) FROM individual_business_owners")
    count = cursor.fetchone()[0]
    print(f"[INFO] Current row count: {count}")

    conn.close()

if __name__ == "__main__":
    verify_db()
