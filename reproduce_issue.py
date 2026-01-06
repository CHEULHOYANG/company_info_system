
import sqlite3
import os

DB_PATH = 'g:/company_project_system/company_database.db'

def reproduce():
    if not os.path.exists(DB_PATH):
        print(f"DB file not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Check if table and column exist
    try:
        cursor.execute("PRAGMA table_info(individual_business_owners)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Columns: {columns}")
        if 'memo' not in columns:
            print("❌ 'memo' column is MISSING!")
            # Add it if missing (to simulate what web_app.py does)
            print("Adding 'memo' column...")
            cursor.execute("ALTER TABLE individual_business_owners ADD COLUMN memo TEXT")
            conn.commit()
        else:
            print("✅ 'memo' column exists.")
    except Exception as e:
        print(f"Error checking schema: {e}")
        return

    # 2. Insert a test record
    try:
        cursor.execute("INSERT INTO individual_business_owners (company_name, status) VALUES ('Test Company', '접촉중')")
        test_id = cursor.lastrowid
        conn.commit()
        print(f"Inserted test company with ID: {test_id}")
    except Exception as e:
        print(f"Error inserting test record: {e}")
        return

    # 3. Update memo (simulate save_individual_business_memo)
    try:
        memo_content = "테스트 메모 내용입니다."
        updates = ["memo = ?"]
        params = [memo_content]
        
        # Simulate status same (no update)
        
        params.append(test_id)
        
        print(f"Executing: UPDATE individual_business_owners SET {', '.join(updates)} WHERE id = ?")
        print(f"Params: {params}")
        
        cursor.execute(f"UPDATE individual_business_owners SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        print("Update executed.")
        
    except Exception as e:
        print(f"Error updating memo: {e}")
        return

    # 4. Verify update
    try:
        cursor.execute("SELECT memo FROM individual_business_owners WHERE id = ?", (test_id,))
        row = cursor.fetchone()
        saved_memo = row['memo']
        print(f"Saved memo: '{saved_memo}'")
        
        if saved_memo == memo_content:
            print("✅ Memo saved successfully!")
        else:
            print(f"❌ Memo NOT saved! Expected '{memo_content}', got '{saved_memo}'")
            
    except Exception as e:
        print(f"Error verifying: {e}")
        return
    finally:
        # Cleanup
        cursor.execute("DELETE FROM individual_business_owners WHERE id = ?", (test_id,))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    reproduce()
