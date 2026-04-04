
import sqlite3

DB_PATH = 'g:/company_project_system/company_database.db'

def setup_email_groups():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create email_groups table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 2. Create email_group_members table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        biz_no TEXT,
        FOREIGN KEY(group_id) REFERENCES email_groups(id)
    )
    ''')

    # Reset
    cursor.execute('DELETE FROM email_group_members')
    cursor.execute('DELETE FROM email_groups')

    # 3. Fetch all valid emails
    cursor.execute("SELECT biz_no FROM Company_Basic WHERE email_usable = 1")
    rows = cursor.fetchall()
    
    # 4. Group by 100
    group_size = 100
    total_groups = 0
    for i in range(0, len(rows), group_size):
        group_idx = (i // group_size) + 1
        group_name = f"서울그룹{group_idx}"
        
        cursor.execute("INSERT INTO email_groups (name, category) VALUES (?, ?)", (group_name, f"그룹{group_idx}"))
        group_id = cursor.lastrowid
        
        members = []
        for r in rows[i:i+group_size]:
            members.append((group_id, r[0]))
            
        cursor.executemany("INSERT INTO email_group_members (group_id, biz_no) VALUES (?, ?)", members)
        total_groups += 1

    conn.commit()
    conn.close()
    print(f"Created {total_groups} groups and assigned {len(rows)} businesses.")

if __name__ == '__main__':
    setup_email_groups()
