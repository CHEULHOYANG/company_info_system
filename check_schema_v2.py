import sqlite3
import os

db_path = 'g:/company_project_system/company_database.db'
with open('g:/company_project_system/company_basic_schema.txt', 'w', encoding='utf-8') as f:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Company_Basic'")
        row = cursor.fetchone()
        if row:
            f.write(row[0])
            f.write("\n\n-- Sample Data (Top 5) --\n")
            cursor.execute("SELECT * FROM Company_Basic LIMIT 5")
            cols = [d[0] for d in cursor.description]
            for row in cursor.fetchall():
                f.write(str(dict(zip(cols, row))) + "\n")
        else:
            f.write("Table Company_Basic not found.")
        conn.close()
    except Exception as e:
        f.write(f"Error: {str(e)}")
