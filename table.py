import sqlite3

db_path = "g:/company_project/company_database.db"
history_id = input("삭제할 history_id를 입력하세요: ")

conn = sqlite3.connect(db_path)
try:
    cur = conn.execute("DELETE FROM Contact_History WHERE history_id = ?", (history_id,))
    conn.commit()
    if cur.rowcount > 0:
        print("삭제되었습니다!")
    else:
        print("해당 ID의 데이터가 없습니다.")
except Exception as e:
    print("삭제 실패:", e)
finally:
    conn.close()