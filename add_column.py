import sqlite3
try:
    conn = sqlite3.connect('company_database.db')
    conn.execute("ALTER TABLE ys_questions ADD COLUMN type TEXT DEFAULT '네/아니오'")
    conn.commit()
    print("Added type column")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
