-- 사용자 관리 테이블 생성
CREATE TABLE IF NOT EXISTS Users (
    user_id TEXT PRIMARY KEY,           -- 사용자 ID (예: ct0001, dt0003)
    password TEXT NOT NULL,             -- 비밀번호 (해시화)
    name TEXT NOT NULL,                 -- 이름
    user_level TEXT NOT NULL CHECK (user_level IN ('V', 'S', 'M', 'N')), -- 권한등급
    user_level_name TEXT NOT NULL,      -- 권한등급명 (메인관리자, 서브관리자, 매니저, 일반담당자)
    branch_code TEXT NOT NULL,          -- 지점코드 (EA3000, EA3100, EA3200)
    branch_name TEXT NOT NULL,          -- 지점명 (중앙지점, 선진지점, 명중지점)
    phone TEXT NOT NULL,                -- 연락처 (010-4444-2445)
    gender TEXT CHECK (gender IN ('M', 'F')), -- 성별 (M: 남성, F: 여성)
    birth_date TEXT,                    -- 생년월일 (YYYY-MM-DD)
    email TEXT,                         -- 이메일
    position TEXT,                      -- 직급/직책
    hire_date TEXT DEFAULT (date('now')), -- 입사일
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')), -- 상태
    last_login DATETIME,                -- 마지막 로그인
    password_changed_date TEXT DEFAULT (date('now')), -- 비밀번호 변경일
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP, -- 생성일
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP  -- 수정일
);

-- 지점 코드 테이블
CREATE TABLE IF NOT EXISTS Branches (
    branch_code TEXT PRIMARY KEY,
    branch_name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    manager_id TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 기본 지점 데이터 삽입
INSERT OR REPLACE INTO Branches (branch_code, branch_name, address, phone) VALUES
('EA3000', '중앙지점', '서울시 중구', '02-1234-5678'),
('EA3100', '선진지점', '서울시 강남구', '02-2345-6789'),
('EA3200', '명중지점', '서울시 서초구', '02-3456-7890');

-- 기존 사용자 데이터 마이그레이션 (예시)
INSERT OR REPLACE INTO Users (user_id, password, name, user_level, user_level_name, branch_code, branch_name, phone, gender, birth_date, position) VALUES
('ct0001', 'ych1123!', '양철호', 'V', '메인관리자', 'EA3000', '중앙지점', '010-1234-5678', 'M', '1980-01-15', '대표이사'),
('ct0002', 'temp_password', '서은정', 'S', '서브관리자', 'EA3000', '중앙지점', '010-2345-6789', 'F', '1985-03-20', '부장'),
('dt0003', 'temp_password', '김영희', 'M', '매니저', 'EA3100', '선진지점', '010-3456-7890', 'F', '1990-07-10', '차장'),
('dt0004', 'temp_password', '지은영', 'N', '일반담당자', 'EA3100', '선진지점', '010-4567-8901', 'F', '1992-11-25', '대리'),
('dt0005', 'temp_password', '구자균', 'N', '일반담당자', 'EA3200', '명중지점', '010-5678-9012', 'M', '1988-05-30', '과장'),
('dt0006', 'temp_password', '이영창', 'M', '매니저', 'EA3200', '명중지점', '010-6789-0123', 'M', '1983-09-18', '차장'),
('dt0007', 'temp_password', '정재승', 'N', '일반담당자', 'EA3000', '중앙지점', '010-7890-1234', 'M', '1991-12-05', '대리'),
('ma0001', 'temp_password', '전재휘', 'S', '서브관리자', 'EA3000', '중앙지점', '010-8901-2345', 'M', '1987-04-22', '부장');