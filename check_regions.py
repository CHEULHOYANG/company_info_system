import sqlite3
import os

db_path = 'g:/company_project_system/company_database.db'
with open('g:/company_project_system/distinct_regions.txt', 'w', encoding='utf-8') as f:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT region FROM Company_Basic WHERE region IS NOT NULL AND region != ''")
        regions = [r[0] for r in cursor.fetchall() if r[0]]
        f.write(", ".join(regions))
        conn.close()
    except Exception as e:
        f.write(f"Error: {str(e)}")
