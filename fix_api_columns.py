import sqlite3
import re

# 파일 읽기
with open(r'g:\company_project_system\web_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# contact_history 테이블 스키마 확인
conn = sqlite3.connect(r'g:\company_project_system\company_database.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(contact_history)")
columns = [col[1] for col in cursor.fetchall()]
conn.close()

print(f"contact_history 테이블 컬럼: {columns}")
print(f"'registered_date' 컬럼 존재: {'registered_date' in columns}")

if 'registered_date' not in columns:
    print("\n✅ registered_date 컬럼이 없으므로 SQL에서 제거해야 합니다.")
    
    # registered_date를 제거하는 패턴
    # SELECT ... registered_by, registered_date
    content = re.sub(
        r'(registered_by),\s*registered_date(\s+FROM\s+Contact_History)',
        r'\1\2',
        content
    )
    
    # 딕셔너리에서 'registered_date': history[7] 제거
    content = re.sub(
        r"'registered_by':\s*history\[6\],\s*\n\s+'registered_date':\s*history\[7\]",
        r"'registered_by': history[6]",
        content
    )
    
    # 파일 저장
    with open(r'g:\company_project_system\web_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ web_app.py 파일이 수정되었습니다!")
else:
    print("\n✅ registered_date 컬럼이 존재합니다. 수정 불필요.")
