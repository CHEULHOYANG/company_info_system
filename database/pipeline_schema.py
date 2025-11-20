"""
영업 파이프라인 관리 테이블 생성 SQL
"""

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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (biz_reg_no) REFERENCES Company_Basic(biz_no)
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

# 인덱스 생성
CREATE_INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_managed_companies_biz_no ON managed_companies(biz_reg_no);',
    'CREATE INDEX IF NOT EXISTS idx_managed_companies_manager ON managed_companies(manager_id);',
    'CREATE INDEX IF NOT EXISTS idx_managed_companies_status ON managed_companies(status);',
    'CREATE INDEX IF NOT EXISTS idx_managed_companies_next_contact ON managed_companies(next_contact_date);',
    'CREATE INDEX IF NOT EXISTS idx_managed_companies_last_contact ON managed_companies(last_contact_date);',
    'CREATE INDEX IF NOT EXISTS idx_contact_history_company ON contact_history(managed_company_id);',
    'CREATE INDEX IF NOT EXISTS idx_contact_history_date ON contact_history(contact_date);'
]

def create_pipeline_tables(conn):
    """파이프라인 관련 테이블 생성"""
    try:
        cursor = conn.cursor()
        
        # 테이블 생성
        cursor.execute(CREATE_MANAGED_COMPANIES_TABLE)
        cursor.execute(CREATE_CONTACT_HISTORY_TABLE)
        
        # 인덱스 생성
        for index_sql in CREATE_INDEXES:
            cursor.execute(index_sql)
        
        conn.commit()
        print("? 영업 파이프라인 테이블 생성 완료")
        return True
        
    except Exception as e:
        print(f"? 테이블 생성 실패: {str(e)}")
        conn.rollback()
        return False

# 샘플 데이터 삽입
SAMPLE_DATA_SQL = '''
-- 샘플 관심 기업 데이터
INSERT INTO managed_companies (biz_reg_no, manager_id, status, keyman_name, keyman_phone, keyman_position, registration_reason, next_contact_date, last_contact_date, notes, expected_amount, priority_level) VALUES
('123-45-67890', 'user1', 'proposal', '김영업', '010-1234-5678', '대표이사', '세미나 참석', '2025-11-25', '2025-11-15', '세무 컨설팅 관심 높음', 5000000, 5),
('234-56-78901', 'user1', 'contacted', '이재무', '010-2345-6789', '재무팀장', '지인 소개', '2025-11-22', '2025-11-10', '내년 법인세 신고 문의', 3000000, 4),
('345-67-89012', 'user2', 'negotiation', '박관리', '010-3456-7890', '총무부장', '홈페이지 문의', '2025-11-21', '2025-11-18', '급여 아웃소싱 검토중', 8000000, 5),
('456-78-90123', 'user1', 'prospect', '최신규', '010-4567-8901', '이사', '전화 영업', '2025-11-30', '2025-10-28', '초기 관심 단계', 2000000, 2);

-- 샘플 접촉 이력 데이터
INSERT INTO contact_history (managed_company_id, contact_date, contact_type, content, cost, follow_up_required, follow_up_date) VALUES
(1, '2025-11-15', 'visit', '사무실 방문하여 서비스 설명. 긍정적 반응', 0, 1, '2025-11-25'),
(1, '2025-11-10', 'phone', '초기 상담 전화. 세무 관련 문의사항 확인', 0, 1, '2025-11-15'),
(2, '2025-11-10', 'meeting', '카페에서 미팅. 서비스 소개 자료 전달', 15000, 1, '2025-11-22'),
(2, '2025-11-05', 'phone', '지인 소개로 첫 연락. 관심사 파악', 0, 1, '2025-11-10'),
(3, '2025-11-18', 'email', '제안서 및 견적서 이메일 발송', 0, 1, '2025-11-21'),
(3, '2025-11-12', 'visit', '회사 방문하여 현황 파악 및 니즈 분석', 0, 1, '2025-11-18'),
(4, '2025-10-28', 'phone', '텔레마케팅으로 첫 접촉. 추후 연락 약속', 0, 1, '2025-11-30');
'''