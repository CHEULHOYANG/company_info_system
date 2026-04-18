import sqlite3

conn = sqlite3.connect('company_database.db')
cursor = conn.cursor()

# Check order-related tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = cursor.fetchall()
print("All Tables:")
for t in all_tables:
    tname = t[0]
    if any(k in tname.lower() for k in ['order', 'naver', 'settlement', 'ship', 'deliver', 'payment', 'store']):
        print(f"  MATCH: {tname}")
    else:
        print(f"  {tname}")
conn.close()
