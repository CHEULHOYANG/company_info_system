# -*- coding: utf-8 -*-

import sqlite3
import os
import sys

def init_pipeline_database(db_path='company_database.db'):
    """파이프라인 관리 테이블 초기화"""
    
    print(f"파이프라인 데이터베이스 초기화 시작: {db_path}")
    
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("기존 테이블 확인...")
        
        # 관심 기업 관리 테이블
        CREATE_MANAGED_COMPANIES_TABLE = '''
        CREATE TABLE IF NOT EXISTS managed_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            biz_reg_no TEXT NOT NULL,
            manager_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'prospect' CHECK (status IN ('prospect', 'contacted', 'proposal', 'negotiation', 'contract', 'hold')),
            keyman_name TEXT NOT NULL,
            keyman_phone TEXT,
            keyman_position TEXT,
            keyman_email TEXT,
            registration_reason TEXT,
            next_contact_date DATE,
            last_contact_date DATE,
            notes TEXT,
            expected_amount INTEGER DEFAULT 0,
            priority_level INTEGER DEFAULT 1 CHECK (priority_level BETWEEN 1 AND 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''

        # 접촉 이력 테이블
        CREATE_CONTACT_HISTORY_TABLE = '''
        CREATE TABLE IF NOT EXISTS contact_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            managed_company_id INTEGER NOT NULL,
            contact_date DATE NOT NULL,
            contact_type TEXT NOT NULL CHECK (contact_type IN ('phone', 'visit', 'email', 'message', 'gift', 'consulting', 'meeting', 'proposal', 'contract')),
            content TEXT NOT NULL,
            cost INTEGER DEFAULT 0,
            attachment TEXT,
            follow_up_required BOOLEAN DEFAULT 0,
            follow_up_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (managed_company_id) REFERENCES managed_companies(id) ON DELETE CASCADE
        );
        '''
        
        # 테이블 생성
        cursor.execute(CREATE_MANAGED_COMPANIES_TABLE)
        print("managed_companies 테이블 생성 완료")
        
        cursor.execute(CREATE_CONTACT_HISTORY_TABLE)
        print("contact_history 테이블 생성 완료")
        
        # 인덱스 생성
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_managed_companies_biz_no ON managed_companies(biz_reg_no);',
            'CREATE INDEX IF NOT EXISTS idx_managed_companies_manager ON managed_companies(manager_id);',
            'CREATE INDEX IF NOT EXISTS idx_managed_companies_status ON managed_companies(status);',
            'CREATE INDEX IF NOT EXISTS idx_managed_companies_next_contact ON managed_companies(next_contact_date);',
            'CREATE INDEX IF NOT EXISTS idx_managed_companies_last_contact ON managed_companies(last_contact_date);',
            'CREATE INDEX IF NOT EXISTS idx_contact_history_company ON contact_history(managed_company_id);',
            'CREATE INDEX IF NOT EXISTS idx_contact_history_date ON contact_history(contact_date);'
        ]
        
        for i, index_sql in enumerate(indexes, 1):
            cursor.execute(index_sql)
            print(f"인덱스 {i}/{len(indexes)} 생성 완료")
        
        conn.commit()
        print("\n파이프라인 데이터베이스 초기화 완료!")
        
        # 테이블 정보 출력
        cursor.execute("SELECT COUNT(*) FROM managed_companies")
        mc_count = cursor.fetchone()[0]
        print(f"managed_companies: {mc_count}개 레코드")
        
        cursor.execute("SELECT COUNT(*) FROM contact_history")
        ch_count = cursor.fetchone()[0]
        print(f"contact_history: {ch_count}개 레코드")
        
        return True
        
    except Exception as e:
        print(f"초기화 실패: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("영업 파이프라인 관리 시스템 데이터베이스 초기화")
    print("=" * 60)
    
    # 현재 디렉터리의 데이터베이스 파일 확인
    db_path = "company_database.db"
    
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
        print(f"기존 데이터베이스 파일: {db_path} ({file_size:.1f}MB)")
    else:
        print(f"새 데이터베이스 파일 생성: {db_path}")
    
    print()
    
    # 초기화 실행
    success = init_pipeline_database(db_path)
    
    if success:
        print("\n다음 단계:")
        print("1. Flask 앱을 실행하세요: python web_app.py")
        print("2. 브라우저에서 /pipeline 경로로 접속하세요")
        print("3. 영업 파이프라인 관리 기능을 사용해보세요!")
    else:
        print("\n초기화에 실패했습니다. 오류를 확인하고 다시 시도해주세요.")
    
    print("\n" + "=" * 60)