import sqlite3
conn = sqlite3.connect('company_database.db')
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Signup_Requests'")
result = cur.fetchone()
if result:
    print(result[0])
else:
    print("Signup_Requests 테이블이 없습니다.")
conn.close()
