# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
영업 파이프라인 관리 시스템 데이터베이스 초기화
"""

import sqlite3
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.pipeline_schema import create_pipeline_tables, CREATE_MANAGED_COMPANIES_TABLE, CREATE_CONTACT_HISTORY_TABLE, CREATE_INDEXES

def init_pipeline_database(db_path='company_database.db'):
    """파이프라인 관리 테이블 초기화"""
    
    print(f"? 파이프라인 데이터베이스 초기화 시작: {db_path}")
    
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("? 기존 테이블 확인...")
        
        # 기존 테이블 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='managed_companies'")
        if cursor.fetchone():
            print("??  managed_companies 테이블이 이미 존재합니다.")
            response = input("기존 테이블을 삭제하고 새로 만들까요? (y/N): ")
            if response.lower() == 'y':
                cursor.execute("DROP TABLE IF EXISTS contact_history")
                cursor.execute("DROP TABLE IF EXISTS managed_companies")
                print("??  기존 테이블 삭제 완료")
            else:
                print("? 초기화를 취소했습니다.")
                return False
        
        print("??  새 테이블 생성 중...")
        
        # 1. managed_companies 테이블 생성
        cursor.execute(CREATE_MANAGED_COMPANIES_TABLE)
        print("? managed_companies 테이블 생성 완료")
        
        # 2. contact_history 테이블 생성
        cursor.execute(CREATE_CONTACT_HISTORY_TABLE)
        print("? contact_history 테이블 생성 완료")
        
        # 3. 인덱스 생성
        for i, index_sql in enumerate(CREATE_INDEXES, 1):
            cursor.execute(index_sql)
            print(f"? 인덱스 {i}/{len(CREATE_INDEXES)} 생성 완료")
        
        # 4. 샘플 데이터 삽입 (선택적)
        response = input("샘플 데이터를 삽입할까요? (y/N): ")
        if response.lower() == 'y':
            insert_sample_data(cursor)
        
        conn.commit()
        print("\n? 파이프라인 데이터베이스 초기화 완료!")
        
        # 테이블 정보 출력
        print_table_info(cursor)
        
        return True
        
    except Exception as e:
        print(f"? 초기화 실패: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def insert_sample_data(cursor):
    """샘플 데이터 삽입"""
    
    print("? 샘플 데이터 삽입 중...")
    
    # 기존 Company_Basic 테이블에서 몇 개 기업 정보 가져오기
    cursor.execute("SELECT biz_no FROM Company_Basic LIMIT 5")
    companies = cursor.fetchall()
    
    if not companies:
        print("??  Company_Basic 테이블에 데이터가 없어 샘플 관심기업을 생성할 수 없습니다.")
        return
    
    # 샘플 관심 기업 등록
    sample_companies = [
        (companies[0][0] if len(companies) > 0 else '123-45-67890', 'user1', 'proposal', '김영업', '010-1234-5678', '대표이사', 'kim@company.com', '세미나 참석', '2025-11-25', '2025-11-15', '세무 컨설팅 관심 높음', 5000000, 5),
        (companies[1][0] if len(companies) > 1 else '234-56-78901', 'user1', 'contacted', '이재무', '010-2345-6789', '재무팀장', 'lee@company.com', '지인 소개', '2025-11-22', '2025-11-10', '내년 법인세 신고 문의', 3000000, 4),
        (companies[2][0] if len(companies) > 2 else '345-67-89012', 'user2', 'negotiation', '박관리', '010-3456-7890', '총무부장', 'park@company.com', '홈페이지 문의', '2025-11-21', '2025-11-18', '급여 아웃소싱 검토중', 8000000, 5),
        (companies[3][0] if len(companies) > 3 else '456-78-90123', 'user1', 'prospect', '최신규', '010-4567-8901', '이사', 'choi@company.com', '전화 영업', '2025-11-30', '2025-10-28', '초기 관심 단계', 2000000, 2),
        (companies[4][0] if len(companies) > 4 else '567-89-01234', 'user2', 'contract', '정성공', '010-5678-9012', '대표이사', 'jung@company.com', '기존 고객 소개', '2025-12-01', '2025-11-19', '계약 체결 완료', 12000000, 5)
    ]
    
    for company_data in sample_companies:
        try:
            cursor.execute('''
                INSERT INTO managed_companies 
                (biz_reg_no, manager_id, status, keyman_name, keyman_phone, keyman_position, 
                 keyman_email, registration_reason, next_contact_date, last_contact_date, 
                 notes, expected_amount, priority_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', company_data)
        except Exception as e:
            print(f"??  샘플 기업 데이터 삽입 실패: {e}")
    
    # 관심 기업 ID 가져오기
    cursor.execute("SELECT id FROM managed_companies ORDER BY id")
    company_ids = [row[0] for row in cursor.fetchall()]
    
    # 샘플 접촉 이력
    if company_ids:
        sample_contacts = [
            (company_ids[0], '2025-11-15', 'visit', '사무실 방문하여 서비스 설명. 긍정적 반응', 0, 1, '2025-11-25'),
            (company_ids[0], '2025-11-10', 'phone', '초기 상담 전화. 세무 관련 문의사항 확인', 0, 1, '2025-11-15'),
            (company_ids[1], '2025-11-10', 'meeting', '카페에서 미팅. 서비스 소개 자료 전달', 15000, 1, '2025-11-22'),
            (company_ids[1], '2025-11-05', 'phone', '지인 소개로 첫 연락. 관심사 파악', 0, 1, '2025-11-10'),
        ]
        
        if len(company_ids) > 2:
            sample_contacts.extend([
                (company_ids[2], '2025-11-18', 'email', '제안서 및 견적서 이메일 발송', 0, 1, '2025-11-21'),
                (company_ids[2], '2025-11-12', 'visit', '회사 방문하여 현황 파악 및 니즈 분석', 0, 1, '2025-11-18'),
            ])
        
        if len(company_ids) > 3:
            sample_contacts.append(
                (company_ids[3], '2025-10-28', 'phone', '텔레마케팅으로 첫 접촉. 추후 연락 약속', 0, 1, '2025-11-30')
            )
        
        if len(company_ids) > 4:
            sample_contacts.extend([
                (company_ids[4], '2025-11-19', 'contract', '정식 계약서 체결 완료', 0, 0, None),
                (company_ids[4], '2025-11-15', 'proposal', '최종 제안서 제출 및 협상', 0, 1, '2025-11-19'),
                (company_ids[4], '2025-11-10', 'gift', '추석 선물 전달', 50000, 1, '2025-11-15'),
            ])
        
        for contact_data in sample_contacts:
            try:
                cursor.execute('''
                    INSERT INTO contact_history 
                    (managed_company_id, contact_date, contact_type, content, cost, 
                     follow_up_required, follow_up_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', contact_data)
            except Exception as e:
                print(f"??  샘플 접촉 이력 삽입 실패: {e}")
    
    print("? 샘플 데이터 삽입 완료")

def print_table_info(cursor):
    """테이블 정보 출력"""
    
    print("\n? 생성된 테이블 정보:")
    print("=" * 50)
    
    # managed_companies 테이블 정보
    cursor.execute("SELECT COUNT(*) FROM managed_companies")
    mc_count = cursor.fetchone()[0]
    print(f"? managed_companies: {mc_count}개 레코드")
    
    # contact_history 테이블 정보
    cursor.execute("SELECT COUNT(*) FROM contact_history")
    ch_count = cursor.fetchone()[0]
    print(f"? contact_history: {ch_count}개 레코드")
    
    # 상태별 통계
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM managed_companies 
        GROUP BY status 
        ORDER BY count DESC
    """)
    
    print(f"\n? 관심 기업 상태별 현황:")
    for row in cursor.fetchall():
        status_names = {
            'prospect': '잠재고객',
            'contacted': '접촉중', 
            'proposal': '제안단계',
            'negotiation': '협상중',
            'contract': '계약완료',
            'hold': '보류'
        }
        status_name = status_names.get(row[0], row[0])
        print(f"  ? {status_name}: {row[1]}개")
    
    print("=" * 50)

if __name__ == "__main__":
    print("? 영업 파이프라인 관리 시스템 데이터베이스 초기화")
    print("=" * 60)
    
    # 현재 디렉터리의 데이터베이스 파일 확인
    db_path = "company_database.db"
    
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
        print(f"? 기존 데이터베이스 파일: {db_path} ({file_size:.1f}MB)")
    else:
        print(f"? 새 데이터베이스 파일 생성: {db_path}")
    
    print()
    
    # 초기화 실행
    success = init_pipeline_database(db_path)
    
    if success:
        print("\n? 다음 단계:")
        print("1. Flask 앱을 실행하세요: python web_app.py")
        print("2. 브라우저에서 /pipeline 경로로 접속하세요")
        print("3. 영업 파이프라인 관리 기능을 사용해보세요!")
    else:
        print("\n? 초기화에 실패했습니다. 오류를 확인하고 다시 시도해주세요.")
    
    print("\n" + "=" * 60)