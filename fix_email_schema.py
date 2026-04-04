import sqlite3, json
DB = 'G:/company_project_system/company_database.db'
conn = sqlite3.connect(DB)
c = conn.cursor()
cols_cb = [r[1] for r in c.execute('PRAGMA table_info(Company_Basic)').fetchall()]
added = []

# 필요 컬럼 추가
if 'email_fix_status' not in cols_cb:
    c.execute("ALTER TABLE Company_Basic ADD COLUMN email_fix_status INTEGER DEFAULT 0")
    added.append('email_fix_status')

if 'last_send_at' not in cols_cb:
    c.execute("ALTER TABLE Company_Basic ADD COLUMN last_send_at TEXT")
    added.append('last_send_at')

if 'last_send_status' not in cols_cb:
    c.execute("ALTER TABLE Company_Basic ADD COLUMN last_send_status TEXT")
    added.append('last_send_status')

if 'email_usable' not in cols_cb:
    c.execute("ALTER TABLE Company_Basic ADD COLUMN email_usable INTEGER DEFAULT 1")
    added.append('email_usable')

if 'category' not in cols_cb:
    c.execute("ALTER TABLE Company_Basic ADD COLUMN category TEXT DEFAULT 'GENERAL'")
    added.append('category')

conn.commit()

final = [r[1] for r in c.execute('PRAGMA table_info(Company_Basic)').fetchall()]
print(json.dumps({'added': added, 'Company_Basic': final}, ensure_ascii=False, indent=2))
conn.close()
