
import sqlite3
import os

DB_PATH = 'g:/company_project_system/company_database.db'

def check_and_setup():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. SMTP Configs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS smtp_configs (
            config_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            config_name TEXT,
            smtp_server TEXT,
            smtp_port INTEGER,
            sender_email TEXT,
            sender_password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Send Batches
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS send_batches (
            batch_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            smtp_config_id INTEGER,
            subject TEXT,
            body TEXT,
            total_count INTEGER,
            sent_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            group_name TEXT,
            last_error TEXT
        )
    ''')
    
    # 3. Email Send Log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_send_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT,
            biz_no TEXT,
            email TEXT,
            group_name TEXT,
            subject TEXT,
            status TEXT, -- SUCCESS, FAIL
            error_msg TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (batch_id) REFERENCES send_batches(batch_id)
        )
    ''')
    
    # 4. Check email_usable in Company_Basic
    cursor.execute("PRAGMA table_info(Company_Basic)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'email_usable' not in cols:
        print("Adding email_usable column to Company_Basic")
        cursor.execute("ALTER TABLE Company_Basic ADD COLUMN email_usable INTEGER DEFAULT 1")
    
    if 'region' not in cols:
        print("Adding region column to Company_Basic")
        cursor.execute("ALTER TABLE Company_Basic ADD COLUMN region TEXT")

    if 'category' not in cols:
        print("Adding category column to Company_Basic")
        cursor.execute("ALTER TABLE Company_Basic ADD COLUMN category TEXT DEFAULT 'GENERAL'")

    # 5. Index for region
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_region ON Company_Basic(region)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_email_usable ON Company_Basic(email_usable)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_category ON Company_Basic(category)")


    conn.commit()
    conn.close()
    print("Database tables for email system setup successfully.")

if __name__ == "__main__":
    check_and_setup()

