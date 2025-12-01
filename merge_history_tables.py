import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect(r'g:\company_project_system\company_database.db')
c = conn.cursor()

print("=== 테이블 통합 시작 ===\n")

# 1. history 테이블 구조 확인
print("1. history 테이블 확인")
c.execute("PRAGMA table_info(history)")
history_cols = [col[1] for col in c.fetchall()]
print(f"   history 컬럼: {history_cols}")

c.execute("SELECT COUNT(*) FROM history")
history_count = c.fetchone()[0]
print(f"   history 레코드 수: {history_count}")

# 2. Contact_History 테이블 구조 확인
print("\n2. Contact_History 테이블 확인")
c.execute("PRAGMA table_info(Contact_History)")
contact_history_cols = [col[1] for col in c.fetchall()]
print(f"   Contact_History 컬럼: {contact_history_cols}")

c.execute("SELECT COUNT(*) FROM Contact_History")
contact_history_count = c.fetchone()[0]
print(f"   Contact_History 레코드 수: {contact_history_count}")

# 3. history 테이블에 데이터가 있다면 Contact_History로 이동
if history_count > 0:
    print("\n3. history 데이터를 Contact_History로 복사")
    # 공통 컬럼 찾기
    common_cols = [col for col in history_cols if col in contact_history_cols]
    print(f"   공통 컬럼: {common_cols}")
    
    # 데이터 복사
    cols_str = ', '.join(common_cols)
    c.execute(f"INSERT INTO Contact_History ({cols_str}) SELECT {cols_str} FROM history")
    print(f"   ✅ {c.rowcount}건 복사 완료")
else:
    print("\n3. history 테이블이 비어있음 - 복사 불필요")

# 4. history 테이블 삭제
print("\n4. history 테이블 삭제")
c.execute("DROP TABLE IF EXISTS history")
print("   ✅ history 테이블 삭제 완료")

# 5. 변경사항 저장
conn.commit()
print("\n✅ 테이블 통합 완료!")
print(f"   최종 레코드 수: {contact_history_count + history_count}건")

conn.close()
