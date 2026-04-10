import sqlite3
import os

DB_PATH = r"g:\company_project_system\company_database.db"

def check_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables = ["Company_Basic", "Company_Representative", "Company_Shareholder", "Company_Additional"]

    for table in tables:
        print(f"Schema for {table}:")
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})") 
        except Exception as e:
            print(f"  Error: {e}")
        print("-" * 20)

    conn.close()

if __name__ == "__main__":
    check_schema()
