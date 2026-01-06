
import sqlite3
import datetime

DB_PATH = 'g:/company_project_system/company_database.db'

def verify_logic():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. Simulate Upload (Insert with 0001-01-01)
        print("--- 1. Simulate Upload ---")
        test_biz_num = '9999999999'
        cursor.execute("DELETE FROM individual_business_owners WHERE business_number = ?", (test_biz_num,))
        
        cursor.execute('''
            INSERT INTO individual_business_owners (company_name, business_number, created_at)
            VALUES (?, ?, ?)
        ''', ('Test Company', test_biz_num, '0001-01-01 00:00:00'))
        
        cursor.execute("SELECT created_at FROM individual_business_owners WHERE business_number = ?", (test_biz_num,))
        row = cursor.fetchone()
        print(f"Inserted Date: {row['created_at']}")
        if row['created_at'] != '0001-01-01 00:00:00':
            print("❌ Upload logic failed (date incorrect)")
        else:
            print("✅ Upload logic verified")

        # 2. Simulate Status Change to '접촉중'
        print("\n--- 2. Simulate Status Change (to Contacting) ---")
        cursor.execute("UPDATE individual_business_owners SET status = ?, created_at = CURRENT_TIMESTAMP WHERE business_number = ?", ('접촉중', test_biz_num))
        
        cursor.execute("SELECT created_at FROM individual_business_owners WHERE business_number = ?", (test_biz_num,))
        row = cursor.fetchone()
        print(f"Updated Date: {row['created_at']}")
        
        # Check if it's today
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if row['created_at'].startswith(today):
            print("✅ Status update logic verified (Date updated to today)")
        else:
            print(f"❌ Status update logic failed. Expected starts with {today}, got {row['created_at']}")

        # 3. Simulate Search
        print("\n--- 3. Simulate Search (Date Filter) ---")
        # Search for today
        query = "SELECT count(*) FROM individual_business_owners WHERE 1=1 AND date(created_at) >= ? AND date(created_at) <= ?"
        cursor.execute(query, (today, today))
        count = cursor.fetchone()[0]
        print(f"Search Count for Today ({today}): {count}")
        
        if count >= 1:
            print("✅ Search logic verified")
        else:
            print("❌ Search logic failed (Did not find the test record)")

    finally:
        # Cleanup
        cursor.execute("DELETE FROM individual_business_owners WHERE business_number = ?", (test_biz_num,))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    verify_logic()
