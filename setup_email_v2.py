
import sqlite3
import re
import os

DB_PATH = 'g:/company_project_system/company_database.db'

def setup_enhanced_email_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("DB 스키마 강화 중...")

    # 1. Company_Basic 테이블 확장
    try:
        cursor.execute('ALTER TABLE Company_Basic ADD COLUMN email_usable INTEGER DEFAULT 0')
    except: pass
    try:
        cursor.execute('ALTER TABLE Company_Basic ADD COLUMN manage_category TEXT DEFAULT "법인기업"') # 1. 법인기업, 2. 관리기업, 3. 특별 개인
    except: pass

    # 2. 이메일 그룹 및 멤버 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # member_count 컬럼 추가 시도
    try:
        cursor.execute('ALTER TABLE email_groups ADD COLUMN member_count INTEGER DEFAULT 0')
    except: pass
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        biz_no TEXT,
        FOREIGN KEY(group_id) REFERENCES email_groups(id)
    )
    ''')

    # 3. 발송 이력 및 결과 관리 (확장)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_send_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        biz_no TEXT,
        email TEXT,
        group_name TEXT,
        subject TEXT,
        status TEXT, -- SUCCESS, FAIL, REJECTED
        error_msg TEXT,
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    print("스키마 설정 완료.")

def perform_batch_filtering_and_grouping():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("이메일 필터링 및 배치 그룹 생성 시작...")

    # 사용자 요청 SQL 필터
    exclude_domains = [
        'lycos.', 'yahoo.', 'empas.', 'empal.', 'paran.', 'freechal.', 
        'dreamwiz.', 'chol.', 'netian.', 'hanafos.', 'korea.com', 'hanmir.'
    ]
    email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    cursor.execute("SELECT biz_no, email FROM Company_Basic WHERE email IS NOT NULL AND email != ''")
    rows = cursor.fetchall()
    
    valid_list = []
    
    for row in rows:
        email = row['email'].strip()
        biz_no = row['biz_no']
        if not email_regex.match(email):
            continue
            
        is_excluded = False
        for domain in exclude_domains:
            if domain.lower() in email.lower():
                is_excluded = True
                break
        
        if not is_excluded:
            valid_list.append(biz_no)

    cursor.execute("UPDATE Company_Basic SET email_usable = 0")
    if valid_list:
        chunk_size = 500
        for i in range(0, len(valid_list), chunk_size):
            chunk = valid_list[i:i + chunk_size]
            placeholders = ','.join(['?'] * len(chunk))
            cursor.execute(f"UPDATE Company_Basic SET email_usable = 1 WHERE biz_no IN ({placeholders})", chunk)
    
    cursor.execute("DELETE FROM email_group_members")
    cursor.execute("DELETE FROM email_groups")
    
    group_size = 100
    for i in range(0, len(valid_list), group_size):
        chunk = valid_list[i:i + group_size]
        group_idx = (i // group_size) + 1
        group_name = f"서울그룹{group_idx}"
        
        cursor.execute("INSERT INTO email_groups (name, category, member_count) VALUES (?, ?, ?)", 
                       (group_name, '서울', len(chunk)))
        group_id = cursor.lastrowid
        
        member_data = [(group_id, biz_no) for biz_no in chunk]
        cursor.executemany("INSERT INTO email_group_members (group_id, biz_no) VALUES (?, ?)", member_data)

    conn.commit()
    conn.close()
    print(f"작업 완료: 총 {len(valid_list)}개 기업을 {((len(valid_list)-1)//100)+1}개 그룹으로 분할했습니다.")

if __name__ == '__main__':
    setup_enhanced_email_db()
    perform_batch_filtering_and_grouping()
