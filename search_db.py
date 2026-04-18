import sqlite3

def search_db(db_path, term):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            tname = table[0]
            try:
                cursor.execute(f"SELECT * FROM {tname}")
                rows = cursor.fetchall()
                for row in rows:
                    if str(term) in str(row):
                        print(f"MATCH in {tname}: {str(row)[:300]}")
            except Exception as e:
                pass
        conn.close()
    except Exception as e:
        print(f"Failed to connect: {e}")

print("Searching for 58378")
search_db('f:/company_project_system/company_database.db', '58378')
print("Searching for 3000")
search_db('f:/company_project_system/company_database.db', '3000')
print("Searching for settlement")
search_db('f:/company_project_system/company_database.db', 'settlement')
