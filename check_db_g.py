import sqlite3
import os

db_path = 'company_database.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

with open('check_db_out.txt', 'w', encoding='utf-8') as f:
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    f.write(f"Tables: {tables}\n\n")

    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        f.write(f"Columns for {table_name}: {columns}\n")

with open('check_db_out.txt', 'a', encoding='utf-8') as f:
    f.write("\n--- Users Table Content ---\n")
    cursor.execute("SELECT user_id, name, user_level, user_level_name FROM Users")
    users = cursor.fetchall()
    for user in users:
        f.write(f"User: {user}\n")

    f.write("\nDistinct User Levels:\n")
    cursor.execute("SELECT DISTINCT user_level, user_level_name FROM Users")
    levels = cursor.fetchall()
    f.write(f"Levels: {levels}\n")

conn.close()
print("Check complete. Results appended to check_db_out.txt")
