import sqlite3
import json
import os

db_path = 'company_database.db'

def get_stats():
    if not os.path.exists(db_path):
        return {"error": "Database not found"}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    stats = {}
    try:
        # 1. Total companies
        cursor.execute("SELECT COUNT(*) FROM Company_Basic")
        stats['total_companies'] = cursor.fetchone()[0]
        
        # 2. Total history records
        cursor.execute("SELECT COUNT(*) FROM Contact_History")
        stats['total_history'] = cursor.fetchone()[0]
        
        # 3. Companies by Region
        cursor.execute("SELECT region, COUNT(*) as count FROM Company_Basic WHERE region IS NOT NULL AND region != '' GROUP BY region ORDER BY count DESC LIMIT 5")
        stats['regions'] = [dict(row) for row in cursor.fetchall()]
        
        # 4. Recent History Activities (Last 30 days)
        cursor.execute("SELECT COUNT(*) FROM Contact_History")
        stats['recent_activities'] = cursor.fetchone()[0]
    except Exception as e:
        stats['error'] = str(e)
    
    conn.close()
    return stats

if __name__ == "__main__":
    print(json.dumps(get_stats(), ensure_ascii=False))
