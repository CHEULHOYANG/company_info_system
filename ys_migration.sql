BEGIN TRANSACTION;

-- Schema for ys_team_members
CREATE TABLE IF NOT EXISTS ys_team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                phone TEXT,
                bio TEXT,
                photo_url TEXT,
                display_order INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

-- Data for ys_team_members
INSERT OR REPLACE INTO ys_team_members (id, name, position, phone, bio, photo_url, display_order, created_at, updated_at) VALUES (1, '양철호', '(수석팀장) Senior Team Leader', '010-2730-6236', '삼성SDS, 하나은행, 삼성카드 재직, IT, 매출, 회계 및 포인트 경력, 물리적 기술적 보안관리, LMS 시스템 개발, 홈페이지 등 각종 플랫폼 구축가능', '/uploads/1767743091899-양.png', 1, '2025-12-22 14:15:43', '2026-01-10 11:19:22');
INSERT OR REPLACE INTO ys_team_members (id, name, position, phone, bio, photo_url, display_order, created_at, updated_at) VALUES (2, '서은정', '(팀장) Team Leader', '010-3310-3519', 'HSBC, 삼성생명, 삼성화재 재무설계 20년 경력, 변액연금, 펀드, M&A 전문 자격증 보유', '/uploads/1767743103076-서.png', 2, '2025-12-22 14:15:43', '2026-01-10 11:19:22');

-- Schema for ys_news
CREATE TABLE IF NOT EXISTS ys_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT,
                summary TEXT,
                link_url TEXT,
                publish_date DATE,
                display_order INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            , thumbnail_url TEXT);

-- Data for ys_news
INSERT OR REPLACE INTO ys_news (id, title, category, summary, link_url, publish_date, display_order, created_at, updated_at, thumbnail_url) VALUES (2, '감액배당의 명과 암: 소득세 절세 수단에서 규제 대상', '', '성공적인 가업승계를 위한 필수 요소: 의지와 역량', 'https://blog.naver.com/ssneobiz/223860455825', '', 1, '2025-12-25 14:28:45', '2026-01-10 11:19:22', 'https://postfiles.pstatic.net/MjAyNTA1MTRfMjE1/MDAxNzQ3MTg2Nzk1MTc2.bE9HOZ-DpvFtqT0RJPbSCsyY32V26Kj9EJdbqD2URugg.XSLWapW9imyu_Cevc9-Ozw8tBybvKbH5jPjLs0dstaYg.PNG/%EA%B0%80%EC%97%85%EC%8A%B9%EA%B3%84%EC%99%80_%EC%9E%90%EC%82%B0_%EC%9D%B4%EC%A0%84%EC%9D%98_%EB%B3%B5%EC%9E%A1%EC%84%B1.png?type=w966');
INSERT OR REPLACE INTO ys_news (id, title, category, summary, link_url, publish_date, display_order, created_at, updated_at, thumbnail_url) VALUES (3, '부모님이 자녀 증여세 대신 내주면?', '', '증여세 대납'' 행위는 또 다른 증여로 간주되어 추가적인 증여세가 부과될 수 있습니다. ', 'https://blog.naver.com/ssneobiz/223870597269', '', 1, '2025-12-25 14:33:36', '2026-01-10 11:19:22', 'https://postfiles.pstatic.net/MjAyNTA1MTlfMTY4/MDAxNzQ3NjM2NTc3OTE5.SLofwh-dRtE2os1ZxnnePTjHG-UhXVPAxFoxwVvqCy8g.90eF3uv97TGxYCVCr5q-BdPtoikg25BPOuhhJ5jmksYg.PNG/%EC%84%B8%EA%B8%88%EB%8C%80%EB%82%A9.png?type=w966');
INSERT OR REPLACE INTO ys_news (id, title, category, summary, link_url, publish_date, display_order, created_at, updated_at, thumbnail_url) VALUES (4, '유상감자, 함부로 했다간 세금 폭탄! ', '', '증여세 피하는 완벽 가이드 ', 'https://blog.naver.com/ssneobiz/223924451047', '', 1, '2025-12-25 14:36:01', '2026-01-10 11:19:22', 'https://postfiles.pstatic.net/MjAyNTA3MDdfMTUy/MDAxNzUxODQ3OTQ5NzI4.ar1a6jJHFuaJ0U08KEX4pJDIEQnMUMqoTyCn0oLFHTUg.YUdI_lf1p1Cz-RD9KZHD4zszWQByNwrOYBoKh4A78kUg.PNG/%EC%9C%A0%EC%83%81%EA%B0%90%EC%9E%90.png?type=w966');
INSERT OR REPLACE INTO ys_news (id, title, category, summary, link_url, publish_date, display_order, created_at, updated_at, thumbnail_url) VALUES (5, '왜 배당 전략이 비상장기업에게 중요할까요?', '', '누적 이익잉여금 해소: 과도한 이익잉여금을 주주에게 환원하여 재무구조를 건전하게 만듭니다.

비상장주식 가치 관리: 배당을 통해 순자산가치를 낮춰, 상속·증여·양도 시 세법상 주식 평가액을 절감할 수 있습니다.

주주 이익 실현: 기업 성장의 과실을 주주와 직접 공유합니다.', 'https://blog.naver.com/ssneobiz/223866096231', '', 1, '2025-12-25 14:38:48', '2026-01-10 11:19:22', 'https://postfiles.pstatic.net/MjAyNTA1MTVfMTk3/MDAxNzQ3MjYzMDMxNzEy.ysWtVVUn7LDzksf9WH6YEICiXk31nWKw3hNY13jooYAg.DZAOrKjkLIO4UwY5brLSpBVsc14cwymP_9hhQSX7M_Qg.PNG/%EB%B9%84%EC%83%81%EC%9E%A5%EC%A3%BC%EC%8B%9D.png?type=w966');
INSERT OR REPLACE INTO ys_news (id, title, category, summary, link_url, publish_date, display_order, created_at, updated_at, thumbnail_url) VALUES (7, '장농속 금팔면 세금 낼까? ', '', '소득이 있는 곳에 세금이 있다"고 말합니다.', 'https://blog.naver.com/ssneobiz/223862608068', '', 1, '2026-01-10 09:59:40', '2026-01-10 11:19:22', 'https://postfiles.pstatic.net/MjAyNTA1MTNfMTQ2/MDAxNzQ3MTE4Mzc0Mzk5.GwOXLXDU25rKRpVxSQWL0ZOM40s2TfshR1GCX3ZRARQg.pG_nxV_joZ9bkpRD1oOPmRUwK-UWgpVd-8hKp8n1eQ0g.PNG/gold.png?type=w966');

-- Schema for ys_inquiries
CREATE TABLE IF NOT EXISTS ys_inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT,
                phone TEXT NOT NULL,
                checklist TEXT,
                content TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

-- Data for ys_inquiries
INSERT OR REPLACE INTO ys_inquiries (id, name, company, phone, checklist, content, status, created_at) VALUES (1, '양철호', '데일리콤프', '01043681001', '["누적된 이익잉여금의 효과적인 활용법(급여, 배당)을 고민중이십니까?", "퇴직금제도 운영으로 안정적인 노후 자금을 마련하고자 하십니까?", "중대재해처벌법, 대비하고 계십니까?", "대표님 유고시 발생할 수 있는 리스크헷지 방법에 대해 준비하고 계십니까?"]', '꼭와주세요', 'read', '2025-12-22 14:23:52');
INSERT OR REPLACE INTO ys_inquiries (id, name, company, phone, checklist, content, status, created_at) VALUES (2, '양철호', '쉬즈홈마켓', '01043681001', '["대표님 유고시 발생할 수 있는 리스크헷지 방법에 대해 준비하고 계십니까?"]', '정말 오실꺼죠
시간이 없어요', 'read', '2025-12-22 14:30:11');
INSERT OR REPLACE INTO ys_inquiries (id, name, company, phone, checklist, content, status, created_at) VALUES (4, '양철호', '기린', '01043681001', '["대표이사 가지급금의 적절한 활용 및 처리 문제로 고민하고 계십니까?", "누적된 이익잉여금의 효과적인 활용법(급여, 배당)을 고민중이십니까?", "퇴직금제도 운영으로 안정적인 노후 자금을 마련하고자 하십니까?", "Final Test Question"]', '', 'read', '2026-01-08 04:28:38');

-- Schema for ys_questions
CREATE TABLE IF NOT EXISTS ys_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                display_order INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            , type TEXT DEFAULT '네/아니오');

-- Data for ys_questions
INSERT OR REPLACE INTO ys_questions (id, question_text, display_order, is_active, created_at, updated_at, type) VALUES (20, '법인 설립 시 발기인수를 맞추기 위해 타인을 주주로 등록 하셨습니까?', 1, 1, '2026-01-10 12:00:10', '2026-01-10 12:00:10', '네/아니오');
INSERT OR REPLACE INTO ys_questions (id, question_text, display_order, is_active, created_at, updated_at, type) VALUES (21, '대표이사 가지급금의 적절한 활용 및 처리 문제로 고민하고 계십니까?', 2, 1, '2026-01-10 12:00:10', '2026-01-10 12:00:10', '네/아니오');
INSERT OR REPLACE INTO ys_questions (id, question_text, display_order, is_active, created_at, updated_at, type) VALUES (22, '누적된 이익잉여금의 효과적인 활용법(급여, 배당)을 고민중이십니까?', 3, 1, '2026-01-10 12:00:10', '2026-01-10 12:00:10', '네/아니오');
INSERT OR REPLACE INTO ys_questions (id, question_text, display_order, is_active, created_at, updated_at, type) VALUES (23, '자녀에게 가업승계를 준비하고 계십니까?', 4, 1, '2026-01-10 12:00:10', '2026-01-10 12:00:10', '네/아니오');
INSERT OR REPLACE INTO ys_questions (id, question_text, display_order, is_active, created_at, updated_at, type) VALUES (24, '퇴직금제도 운영으로 안정적인 노후 자금을 마련하고자 하십니까?', 5, 1, '2026-01-10 12:00:10', '2026-01-10 12:00:10', '네/아니오');
INSERT OR REPLACE INTO ys_questions (id, question_text, display_order, is_active, created_at, updated_at, type) VALUES (25, '중소기업 인증제도(기업부설연구소, 이노비즈 등)를 활용하고 계십니까?', 6, 1, '2026-01-10 12:00:10', '2026-01-10 12:00:10', '네/아니오');
INSERT OR REPLACE INTO ys_questions (id, question_text, display_order, is_active, created_at, updated_at, type) VALUES (26, '중대재해처벌법, 대비하고 계십니까?', 7, 1, '2026-01-10 12:00:10', '2026-01-10 12:00:10', '네/아니오');
INSERT OR REPLACE INTO ys_questions (id, question_text, display_order, is_active, created_at, updated_at, type) VALUES (27, '대표님 유고시 발생할 수 있는 리스크헷지 방법에 대해 준비하고 계십니까?', 8, 1, '2026-01-10 12:00:10', '2026-01-10 12:00:10', '네/아니오');
INSERT OR REPLACE INTO ys_questions (id, question_text, display_order, is_active, created_at, updated_at, type) VALUES (28, 'Final Test Question', 9, 1, '2026-01-10 12:00:10', '2026-01-10 12:00:10', '네/아니오');

-- Schema for ys_seminars
CREATE TABLE IF NOT EXISTS ys_seminars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            , max_attendees INTEGER DEFAULT 0);

-- Data for ys_seminars
INSERT OR REPLACE INTO ys_seminars (id, title, date, time, location, description, created_at, max_attendees) VALUES (2, '법인 결산 후 필수점검 세미나', '1월 27일 (화)', '10:00 - 11:50', '삼성생명 서초사옥 35층', '법인 결산 후 필수점검 세미나<br>법인 결산 후 필수점검 세미나2', '2026-01-10 08:21:52', 0);
INSERT OR REPLACE INTO ys_seminars (id, title, date, time, location, description, created_at, max_attendees) VALUES (3, '세법개정 리뷰 및 결산 후 법인 필수 점검 사항', '1월 29일 (목)', '14:00 - 16:00', '강남 FP 센터', '미 국 세 법 의 이 해 와 활 용<br>미국 시민권자 소득세신고 및 해외 금융 계좌 보고', '2026-01-10 08:21:52', 0);
INSERT OR REPLACE INTO ys_seminars (id, title, date, time, location, description, created_at, max_attendees) VALUES (4, '2026년 세법개정안 ', '1월30일', '10:30 ~ 12: 30', '거시기 거기 어디야', '잉어
자갈치
놀래미
망고보드', '2026-01-10 08:28:22', 0);

-- Schema for ys_seminar_sessions
CREATE TABLE IF NOT EXISTS ys_seminar_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seminar_id INTEGER NOT NULL,
                time_range TEXT NOT NULL,
                title TEXT NOT NULL,
                speaker TEXT,
                description TEXT,
                location_note TEXT,
                display_order INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seminar_id) REFERENCES ys_seminars (id) ON DELETE CASCADE
            );

-- Data for ys_seminar_sessions
INSERT OR REPLACE INTO ys_seminar_sessions (id, seminar_id, time_range, title, speaker, description, location_note, display_order, created_at) VALUES (43, 4, '10:30~11:30', '법인세 소득공제 구간', '이세동 FO 세무전문가', '법인 2억미만 구간의 세율인상 에 따른 절세전략', '', 1, '2026-01-10 11:19:22');
INSERT OR REPLACE INTO ys_seminar_sessions (id, seminar_id, time_range, title, speaker, description, location_note, display_order, created_at) VALUES (44, 4, '11:30 ~ 12:30', '법인세 는 환원의 의미', '김미성 FI', '자기 주장과 Fo 세무 법률대리인의 첨예한 대립', '', 2, '2026-01-10 11:19:22');

-- Schema for SeminarRegistrations
CREATE TABLE IF NOT EXISTS SeminarRegistrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seminar_title TEXT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                company_name TEXT,
                position TEXT,
                biz_no TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

COMMIT;
