
import sqlite3
import re
import os

DB_PATH = 'g:/company_project_system/company_database.db'

def setup_email_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Add email_usable column if it doesn't exist
    try:
        cursor.execute('ALTER TABLE Company_Basic ADD COLUMN email_usable INTEGER DEFAULT 0')
    except: pass

    # 2. Add company_type to Company_Basic (for distinction)
    try:
        cursor.execute('ALTER TABLE Company_Basic ADD COLUMN company_type TEXT DEFAULT "법인기업"')
    except: pass

    # 3. Create smtp_configs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS smtp_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        smtp_server TEXT DEFAULT "smtp.gmail.com",
        smtp_port INTEGER DEFAULT 587,
        sender_email TEXT NOT NULL,
        sender_password TEXT NOT NULL,
        display_name TEXT,
        is_default INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 4. Create send_batches table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS send_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT UNIQUE,
        user_id TEXT,
        smtp_config_id INTEGER,
        subject TEXT,
        body TEXT,
        total_count INTEGER DEFAULT 0,
        sent_count INTEGER DEFAULT 0,
        success_count INTEGER DEFAULT 0,
        fail_count INTEGER DEFAULT 0,
        sent_at DATETIME,
        completed_at DATETIME,
        status TEXT,
        group_name TEXT,
        last_error TEXT
    )
    ''')

    # 5. Create email_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        biz_no TEXT,
        batch_id TEXT,
        recipient_email TEXT,
        sent_at DATETIME,
        status TEXT,
        result TEXT,
        error_message TEXT
    )
    ''')
    
    conn.commit()
    
    # 6. Run SQL to update email_usable based on criteria
    # SQLite doesn't have REGEXP by default, but we can register one if needed or use LIKE patterns.
    # We will fetch and update via script for better control.
    
    cursor.execute("SELECT biz_no, email FROM Company_Basic WHERE email IS NOT NULL AND email != ''")
    rows = cursor.fetchall()
    
    email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    exclude_domains = [
        'lycos.', 'yahoo.', 'empas.', 'empal.', 'paran.', 'freechal.', 
        'dreamwiz.', 'chol.', 'netian.', 'hanafos.', 'korea.com', 'hanmir.'
    ]
    
    valid_biz_nos = []
    
    for biz_no, email in rows:
        email = email.strip()
        # 1. Regex check
        if not email_regex.match(email):
            continue
        # 2. Domain check
        if any(domain in email.lower() for domain in exclude_domains):
            continue
        valid_biz_nos.append(biz_no)
    
    # Update email_usable for valid ones (batch update)
    if valid_biz_nos:
        cursor.execute("UPDATE Company_Basic SET email_usable = 0") # Reset
        cursor.executemany("UPDATE Company_Basic SET email_usable = 1 WHERE biz_no = ?", [(b,) for b in valid_biz_nos])
    
    conn.commit()
    conn.close()
    print(f'Email DB Setup complete. Found {len(valid_biz_nos)} valid emails.')

if __name__ == '__main__':
    setup_email_db()
