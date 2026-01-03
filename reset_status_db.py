#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check and update database status values
DB에 "완료"로 저장된 것들을 NULL로 변경
"""
import sqlite3

# Connect to DB
conn = sqlite3.connect('g:/company_project_system/company_database.db')
cursor = conn.cursor()

# Check current status distribution
print("=" * 80)
print("현재 상태 분포:")
print("=" * 80)
cursor.execute("""
    SELECT 
        CASE WHEN status IS NULL THEN '(NULL)' 
             WHEN status = '' THEN '(빈 문자열)'
             ELSE status END as status_value,
        COUNT(*) as count
    FROM individual_business_owners
    GROUP BY status
    ORDER BY count DESC
""")

for row in cursor.fetchall():
    status, count = row
    print(f"{status:15s}: {count:4d}건")

# Ask user if they want to reset
print("\n" + "=" * 80)
print("⚠️  주의: '완료' 상태를 모두 NULL로 초기화하시겠습니까?")
print("   이렇게 하면 프론트엔드에서 '접촉대기'가 자동 선택됩니다.")
print("=" * 80)

response = input("\n진행하려면 'YES' 입력: ")

if response.strip().upper() == 'YES':
    # Update all "완료" to NULL
    cursor.execute("""
        UPDATE individual_business_owners 
        SET status = NULL 
        WHERE status = '완료'
    """)
    
    affected = cursor.rowcount
    conn.commit()
    
    print(f"\n✅ {affected}건의 '완료' 상태를 NULL로 변경했습니다.")
    
    # Show new distribution
    print("\n" + "=" * 80)
    print("변경 후 상태 분포:")
    print("=" * 80)
    cursor.execute("""
        SELECT 
            CASE WHEN status IS NULL THEN '(NULL)' 
                 WHEN status = '' THEN '(빈 문자열)'
                 ELSE status END as status_value,
            COUNT(*) as count
        FROM individual_business_owners
        GROUP BY status
        ORDER BY count DESC
    """)
    
    for row in cursor.fetchall():
        status, count = row
        print(f"{status:15s}: {count:4d}건")
    
    print("\n🔄 브라우저에서 Ctrl+Shift+R로 새로고침하세요!")
else:
    print("\n❌ 취소되었습니다.")

conn.close()
