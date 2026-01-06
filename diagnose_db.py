
import sqlite3
import os
import json

DB_PATH = 'g:/company_project_system/company_database.db'

def diagnose():
    print(f"Checking database at {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("❌ DB file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Check individual_business_owners schema
    print("\n--- Checking 'individual_business_owners' schema ---")
    cursor.execute("PRAGMA table_info(individual_business_owners)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Columns found: {columns}")
    
    required_cols = ['memo', 'status', 'assigned_user_id']
    for col in required_cols:
        if col in columns:
            print(f"✅ Column '{col}' exists.")
        else:
            print(f"❌ Column '{col}' is MISSING! Attempting to add...")
            try:
                cursor.execute(f"ALTER TABLE individual_business_owners ADD COLUMN {col} TEXT")
                conn.commit()
                print(f"   Column '{col}' added successfully.")
            except Exception as e:
                print(f"   Failed to add column '{col}': {e}")

    # 2. Check individual_business_history table
    print("\n--- Checking 'individual_business_history' table ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='individual_business_history'")
    if cursor.fetchone():
        print("✅ Table 'individual_business_history' exists.")
        cursor.execute("PRAGMA table_info(individual_business_history)")
        h_columns = [col[1] for col in cursor.fetchall()]
        print(f"   Columns: {h_columns}")
        
        # Check for required history columns
        req_h_cols = ['created_by', 'type', 'content', 'business_id']
        for col in req_h_cols:
            if col not in h_columns:
                print(f"❌ Column '{col}' is MISSING in history table! Adding...")
                try:
                    cursor.execute(f"ALTER TABLE individual_business_history ADD COLUMN {col} TEXT")
                    conn.commit()
                    print(f"   Column '{col}' added.")
                except Exception as e:
                    print(f"   Failed to add '{col}': {e}")
    else:
        print("❌ Table 'individual_business_history' is MISSING! Attempting to create...")
        try:
            cursor.execute('''
                CREATE TABLE individual_business_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_id INTEGER NOT NULL,
                    type TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    FOREIGN KEY (business_id) REFERENCES individual_business_owners(id)
                )
            ''')
            conn.commit()
            print("   Table created successfully.")
        except Exception as e:
            print(f"   Failed to create table: {e}")

    # 3. Test Insert into History
    print("\n--- Testing History Insert ---")
    try:
        # Create dummy business
        cursor.execute("INSERT INTO individual_business_owners (company_name) VALUES ('History Test Corp')")
        test_biz_id = cursor.lastrowid
        print(f"Created test business ID: {test_biz_id}")

        # Insert history
        cursor.execute('''
            INSERT INTO individual_business_history (business_id, type, content, created_by)
            VALUES (?, ?, ?, ?)
        ''', (test_biz_id, '방문', '테스트 방문 기록', 'tester'))
        conn.commit()
        print("History insert executed.")

        # Verify
        cursor.execute("SELECT * FROM individual_business_history WHERE business_id = ?", (test_biz_id,))
        rows = cursor.fetchall()
        print(f"Rows found: {len(rows)}")
        for row in rows:
            print(f" - {row['type']}: {row['content']} (by {row['created_by']})")
        
        if len(rows) > 0:
            print("✅ History test successful!")
        else:
            print("❌ History insert FAILED (no rows found).")
            
    except Exception as e:
        print(f"❌ Error during history test: {e}")
    finally:
        # Cleanup
        if 'test_biz_id' in locals():
            cursor.execute("DELETE FROM individual_business_owners WHERE id = ?", (test_biz_id,))
            cursor.execute("DELETE FROM individual_business_history WHERE business_id = ?", (test_biz_id,))
            conn.commit()
            print("Cleanup done.")
        conn.close()

if __name__ == "__main__":
    diagnose()
