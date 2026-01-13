import sqlite3

def check():
    conn = sqlite3.connect('company_database.db')
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT id, date, time FROM ys_seminars').fetchall()
    with open('db_dump.txt', 'w', encoding='utf-8') as f:
        for row in rows:
            f.write(f"ID: {row['id']}, Date: '{row['date']}', Time: '{row['time']}'\n")
    print("Dumped to db_dump.txt")

if __name__ == '__main__':
    check()
