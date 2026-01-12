# -*- coding: utf-8 -*-
# Company Management System
import os
import sqlite3
import io
import time
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, Response, send_file, send_from_directory
from datetime import datetime
import pytz
import pandas as pd
import math
import csv
from werkzeug.utils import secure_filename
from jinja2 import FileSystemLoader, TemplateNotFound
import requests
from bs4 import BeautifulSoup

# .env 파일에서 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()  # .env 파일이 있으면 자동으로 환경 변수로 로드

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_kst_now():
    """한국 시간 현재 시각을 반환합니다."""
    return datetime.now(KST)
import pytz
from datetime import timezone, timedelta

# --- 커스텀 템플릿 로더 (UTF-8 우선, CP949 폴백) ---
class UTF8FileSystemLoader(FileSystemLoader):
    def get_source(self, environment, template):
        # 파일 경로 찾기
        for searchpath in self.searchpath:
            filename = os.path.join(searchpath, template)
            if os.path.exists(filename):
                # UTF-8로 먼저 시도, 실패하면 CP949로 시도
                source = None
                for encoding in ['utf-8', 'cp949']:
                    try:
                        with open(filename, 'r', encoding=encoding) as f:
                            source = f.read()
                        break  # 성공하면 루프 종료
                    except UnicodeDecodeError:
                        continue
                
                if source is None:
                    raise UnicodeDecodeError(f"Cannot decode template {template} with UTF-8 or CP949")
                
                mtime = os.path.getmtime(filename)
                def uptodate():
                    try:
                        return os.path.getmtime(filename) == mtime
                    except OSError:
                        return False
                return source, filename, uptodate
        
        raise TemplateNotFound(template)

# --- 기본 설정 ---
app = Flask(__name__)
app.secret_key = 'your_very_secret_key_12345'

# 한글 인코딩 설정 - JSON 응답에서 한글 깨짐 방지
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# 모든 응답에 UTF-8 강제 설정
@app.before_request
def before_request():
    """모든 요청 전에 실행"""
    pass

@app.after_request
def after_request(response):
    """모든 응답 후에 UTF-8 헤더를 강제로 설정"""
    if response.content_type.startswith('text/html'):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
    elif response.content_type.startswith('application/json'):
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    elif response.content_type.startswith('text/'):
        response.headers['Content-Type'] = response.content_type + '; charset=utf-8'
    return response

# 업로드 폴더 설정
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

# 현재 한국 시간을 반환하는 함수
def get_kst_now():
    """현재 한국 시간을 반환합니다."""
    return datetime.now(KST)

def format_kst_datetime(dt_str=None):
    """한국 시간대로 포맷팅된 현재 시간 문자열을 반환합니다."""
    if dt_str:
        # 입력된 시간이 있으면 한국 시간대로 변환
        try:
            if isinstance(dt_str, str):
                # ISO 형식 문자열 파싱
                if 'T' in dt_str:
                    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                    dt = dt.replace(tzinfo=pytz.UTC)
                
                # UTC에서 KST로 변환
                kst_dt = dt.astimezone(KST)
                return kst_dt.strftime('%Y-%m-%d %H:%M:%S')
            return dt_str
        except:
            return dt_str
    else:
        # 현재 한국 시간 반환
        return get_kst_now().strftime('%Y-%m-%d %H:%M:%S')

# 커스텀 템플릿 로더 설정
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.jinja_loader = UTF8FileSystemLoader(template_dir)

# DB 경로 설정 (Render Persistent Disk 사용)
app_dir = os.path.dirname(os.path.abspath(__file__))

# render.com에서는 환경변수 RENDER가 설정됨
if os.environ.get('RENDER'):
    # render.com 서버 환경 - 다양한 경로 확인
    print("=== RENDER 서버 환경 감지 ===")
    print(f"현재 작업 디렉터리: {os.getcwd()}")
    print(f"앱 디렉터리: {app_dir}")
    print(f"HOME 환경변수: {os.environ.get('HOME', 'N/A')}")
    print(f"USER 환경변수: {os.environ.get('USER', 'N/A')}")
    
    # 루트 디렉터리 확인
    print("\n=== 루트 디렉터리 구조 확인 ===")
    try:
        root_items = os.listdir('/')
        print(f"/ 디렉터리 내용: {root_items}")
    except Exception as e:
        print(f"루트 디렉터리 확인 실패: {e}")
    
    # 가능한 경로들 확인
    possible_paths = [
        '/var/data',
        '/opt/render/project/data', 
        '/opt/render/data',
        '/data',
        '/tmp/data',
        '/app/data',
        os.path.join(app_dir, 'data')
    ]
    
    print(f"\n=== 가능한 데이터 경로들 확인 ===")
    persistent_disk_path = None
    for path in possible_paths:
        print(f"경로 확인 중: {path}")
        if os.path.exists(path):
            print(f"? 발견: {path}")
            
            # 디렉터리 내용 확인
            try:
                contents = os.listdir(path)
                print(f"  내용: {contents}")
            except Exception as e:
                print(f"  내용 확인 실패: {e}")
            
            # 디렉터리에 쓰기 권한이 있는지 확인
            try:
                test_file = os.path.join(path, 'test_write.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                persistent_disk_path = path
                print(f"? 쓰기 권한 확인: {path}")
                break
            except Exception as e:
                print(f"? 쓰기 권한 없음: {path} - {e}")
        else:
            print(f"? 없음: {path}")
    
    # Persistent Disk 디렉터리 확인 및 생성
    if persistent_disk_path:
        # Persistent Disk가 마운트된 경우
        DB_PATH = os.path.join(persistent_disk_path, 'company_database.db')
        print(f"\n? 사용할 DB 경로: {DB_PATH}")
        
        # 기존 DB 파일 확인
        if os.path.exists(DB_PATH):
            print(f"? 기존 DB 파일 발견: {DB_PATH}")
        else:
            print(f"새 DB 파일 생성 예정: {DB_PATH}")
        
        # 디렉터리 생성 시도
        try:
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            print(f"? DB 디렉터리 준비 완료: {os.path.dirname(DB_PATH)}")
        except Exception as e:
            print(f"? DB 디렉터리 생성 실패: {e}")
    else:
        print("\n? 사용 가능한 Persistent Disk 경로를 찾을 수 없음")
        # Persistent Disk가 없는 경우 (기존 로직 유지)
        # 1순위: 기존 DB 파일이 있으면 계속 사용 (데이터 보존)
        existing_db = os.path.join(app_dir, 'company_database.db')
        if os.path.exists(existing_db):
            DB_PATH = existing_db
            print(f"Using existing DB (no persistent disk): {DB_PATH}")
        else:
            # 2순위: 기존 DB가 없으면 data 폴더에 새로 생성
            db_dir = os.path.join(app_dir, 'data')
            os.makedirs(db_dir, exist_ok=True)
            DB_PATH = os.path.join(db_dir, 'company_info.db')
            print(f"Creating new DB (no persistent disk): {DB_PATH}")
else:
    # 로컬 개발 환경 - 기존 파일 사용
    DB_PATH = os.path.join(app_dir, 'company_database.db')
    print(f"Local DB: {DB_PATH}")

# --- DB 연결 함수 및 사용자 계정 ---
def get_db_connection():
    """데이터베이스 연결을 반환합니다. Persistent Disk 지원"""
    try:
        # 데이터베이스 디렉터리가 없으면 생성
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created DB directory: {db_dir}")
        
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # 연결 테스트 및 기본 테이블 확인
        try:
            conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1").fetchone()
            return conn
        except Exception as table_error:
            print(f"Database table check failed: {table_error}")
            conn.close()
            raise table_error
            
    except Exception as e:
        print(f"Database connection error: {e}")
        print(f"DB_PATH was: {DB_PATH}")
        
        # 연결 실패 시 강제로 새 DB 생성 시도
        try:
            # 임시 DB 경로로 재시도
            temp_db_path = os.path.join(app_dir, 'emergency_database.db')
            print(f"Attempting emergency DB creation at: {temp_db_path}")
            
            conn = sqlite3.connect(temp_db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            
            # 기본 테이블들 생성
            init_emergency_database(conn)
            
            return conn
            
        except Exception as emergency_error:
            print(f"Emergency DB creation failed: {emergency_error}")
            # 최후의 수단: 메모리 DB + 기본 테이블 생성
            print("Using in-memory database with basic tables")
            conn = sqlite3.connect(':memory:', check_same_thread=False)
            conn.row_factory = sqlite3.Row
            init_emergency_database(conn)
            return conn

def init_emergency_database(conn):
    """응급 상황용 기본 데이터베이스 테이블들을 생성합니다."""
    try:
        # Users 테이블 생성
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                user_level TEXT NOT NULL DEFAULT 'N',
                user_level_name TEXT NOT NULL DEFAULT '일반담당자',
                branch_code TEXT NOT NULL DEFAULT 'DEFAULT',
                branch_name TEXT NOT NULL DEFAULT '기본지점',
                phone TEXT,
                email TEXT,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
        ''')
        
        # 기본 관리자 계정 삽입 (하드코딩된 것과 별도로)
        conn.execute('''
            INSERT OR IGNORE INTO Users 
            (user_id, password, name, user_level, user_level_name, branch_code, branch_name, phone)
            VALUES ('admin', 'admin123!', '시스템관리자', 'V', '메인관리자', 'SYSTEM', '시스템', '010-0000-0000')
        ''')
        
        # 기본적인 다른 테이블들도 생성
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Company_Basic (
                biz_no TEXT PRIMARY KEY,
                company_name TEXT,
                representative_name TEXT,
                establish_date TEXT,
                company_size TEXT,
                industry_name TEXT,
                region TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Contact_History (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                biz_no TEXT,
                contact_datetime TEXT,
                contact_type TEXT,
                contact_person TEXT,
                memo TEXT,
                registered_by TEXT,
                registered_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("Emergency database tables created successfully")
        
    except Exception as e:
        print(f"Error creating emergency database: {e}")

# 구독 정보 조회 함수
def get_user_subscription_info(user_id):
    """사용자의 구독 정보를 조회합니다."""
    conn = get_db_connection()
    try:
        subscription = conn.execute('''
            SELECT subscription_type, subscription_start_date, subscription_end_date
            FROM User_Subscriptions 
            WHERE user_id = ?
        ''', (user_id,)).fetchone()
        
        if subscription:
            from datetime import datetime
            import pytz
            
            # 한국 시간대로 현재 날짜 계산
            korea_tz = pytz.timezone('Asia/Seoul')
            now = datetime.now(korea_tz)
            end_date = datetime.strptime(subscription['subscription_end_date'], '%Y-%m-%d')
            end_date = korea_tz.localize(end_date.replace(hour=23, minute=59, second=59))
            
            days_remaining = (end_date - now).days
            
            return {
                'subscription_type': subscription['subscription_type'],
                'start_date': subscription['subscription_start_date'],
                'end_date': subscription['subscription_end_date'],
                'days_remaining': days_remaining
            }
        else:
            return None
    finally:
        conn.close()

# 사용자 테이블 초기화 함수
def init_user_tables():
    """사용자 관리 테이블들을 초기화합니다. (기존 데이터 보존)"""
    conn = get_db_connection()
    try:
        # 기존 Users 테이블 존재 여부 확인
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Users';")
        users_exists = cursor.fetchone()
        
        if users_exists:
            # 기존 사용자 데이터가 있는지 확인
            cursor.execute("SELECT COUNT(*) FROM Users")
            user_count = cursor.fetchone()[0]
            if user_count > 0:
                print("User tables already exist with data - skipping initialization")
                # Signup_Requests와 Password_History 테이블만 생성 (없는 경우)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS Signup_Requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        email TEXT NOT NULL,
                        branch_code TEXT NOT NULL,
                        branch_name TEXT NOT NULL,
                        birth_date TEXT,
                        gender TEXT CHECK (gender IN ('M', 'F')),
                        position TEXT DEFAULT '팀장',
                        purpose TEXT,
                        status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
                        requested_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        processed_date DATETIME,
                        processed_by TEXT,
                        admin_notes TEXT
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS Password_History (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        password TEXT NOT NULL,
                        created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES Users(user_id)
                    )
                ''')
                
                # 구독 관리 테이블 생성
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS User_Subscriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        subscription_start_date DATE,
                        subscription_end_date DATE,
                        subscription_type TEXT DEFAULT 'MONTHLY' CHECK (subscription_type IN ('MONTHLY', 'YEARLY', 'FREE')),
                        total_paid_amount INTEGER DEFAULT 0,
                        is_first_month_free BOOLEAN DEFAULT 1,
                        created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES Users(user_id)
                    )
                ''')
                
                # 결제 이력 테이블 생성
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS Payment_History (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        payment_date DATE NOT NULL,
                        amount INTEGER NOT NULL,
                        payment_type TEXT NOT NULL CHECK (payment_type IN ('MONTHLY', 'YEARLY', 'SIGNUP')),
                        payment_method TEXT,
                        notes TEXT,
                        created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES Users(user_id)
                    )
                ''')
                conn.commit()
                print("User tables initialized successfully")
                return
        
        # SQL 파일이 있으면 사용, 없으면 기본 테이블 생성
        sql_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_user_table.sql')
        if os.path.exists(sql_file_path):
            try:
                # CP949 인코딩으로 먼저 시도
                with open(sql_file_path, 'r', encoding='cp949') as f:
                    sql_script = f.read()
            except UnicodeDecodeError:
                # UTF-8로 재시도
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
            
            # 각 SQL 문을 분리하여 실행
            for statement in sql_script.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        conn.execute(statement)
                    except Exception as e:
                        print(f"SQL execution warning: {e}")
            conn.commit()
            print("User tables initialized successfully")
        else:
            print("SQL file not found, creating minimal user tables")
            # 기본 테이블들 생성 (기존 데이터 보존)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Users (
                    user_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    user_level TEXT NOT NULL CHECK (user_level IN ('V', 'S', 'M', 'N')),
                    user_level_name TEXT NOT NULL,
                    branch_code TEXT NOT NULL,
                    branch_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    gender TEXT CHECK (gender IN ('M', 'F')),
                    birth_date TEXT,
                    status TEXT DEFAULT 'ACTIVE',
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    password_changed_date TEXT,
                    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Password_History (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    password TEXT NOT NULL,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Signup_Requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT NOT NULL,
                    branch_code TEXT NOT NULL,
                    branch_name TEXT NOT NULL,
                    birth_date TEXT,
                    gender TEXT CHECK (gender IN ('M', 'F')),
                    position TEXT DEFAULT '팀장',
                    purpose TEXT,
                    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
                    requested_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed_date DATETIME,
                    processed_by TEXT,
                    admin_notes TEXT
                )
            ''')
            
            conn.commit()
            print("User tables initialized successfully")
    except Exception as e:
        print(f"Error initializing user tables: {e}")
    finally:
        conn.close()

# 영업 파이프라인 테이블 초기화 함수
def init_pipeline_tables():
    """영업 파이프라인 관리 테이블 초기화"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 관심 기업 관리 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS managed_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            biz_reg_no TEXT NOT NULL,
            company_name TEXT,
            representative TEXT,
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
        )
        ''')
        
        # 접촉 이력 테이블 (파이프라인용)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_contact_history (
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
        )
        ''')
        
        # 인덱스 생성
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_managed_companies_biz_no ON managed_companies(biz_reg_no)',
            'CREATE INDEX IF NOT EXISTS idx_managed_companies_manager ON managed_companies(manager_id)',
            'CREATE INDEX IF NOT EXISTS idx_managed_companies_status ON managed_companies(status)',
            'CREATE INDEX IF NOT EXISTS idx_managed_companies_next_contact ON managed_companies(next_contact_date)',
            'CREATE INDEX IF NOT EXISTS idx_managed_companies_last_contact ON managed_companies(last_contact_date)',
            'CREATE INDEX IF NOT EXISTS idx_pipeline_contact_history_company ON pipeline_contact_history(managed_company_id)',
            'CREATE INDEX IF NOT EXISTS idx_pipeline_contact_history_date ON pipeline_contact_history(contact_date)'
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        print("영업 파이프라인 테이블 초기화 완료")
        
    except Exception as e:
        print(f"영업 파이프라인 테이블 초기화 실패: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

# YS Honers 테이블 초기화 함수
def init_ys_honers_tables():
    """YS Honers 관련 테이블들을 초기화합니다."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 팀원 관리 테이블
        cursor.execute('''
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
            )
        ''')
        
        # 뉴스 관리 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ys_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT,
                summary TEXT,
                link_url TEXT,
                thumbnail_url TEXT,
                publish_date DATE,
                display_order INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if thumbnail_url column exists in ys_news (migration)
        try:
            cursor.execute("SELECT thumbnail_url FROM ys_news LIMIT 1")
        except:
            print("Adding thumbnail_url column to ys_news")
            cursor.execute("ALTER TABLE ys_news ADD COLUMN thumbnail_url TEXT")
        
        # 상담 문의 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ys_inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT,
                phone TEXT NOT NULL,
                checklist TEXT,
                content TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 질문 관리 테이블 (새로 추가)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ys_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                display_order INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 세미나 관리 테이블 (수정: max_attendees 추가)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ys_seminars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT,
                max_attendees INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 세미나 세션(스케줄) 테이블 (새로 추가)
        cursor.execute('''
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
            )
        ''')
        
        # Check if max_attendees column exists in ys_seminars (migration)
        try:
            cursor.execute("SELECT max_attendees FROM ys_seminars LIMIT 1")
        except:
            cursor.execute("ALTER TABLE ys_seminars ADD COLUMN max_attendees INTEGER DEFAULT 0")

        
        # 세미나 참가 신청 테이블 (보강)
        # 세미나 참가 신청 테이블 (보강)
        # 세미나 참가 신청 테이블 (보강)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SeminarRegistrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seminar_title TEXT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                company_name TEXT,
                position TEXT,
                biz_no TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # SeminarRegistrations 테이블 마이그레이션 (컬럼 확인 및 추가)
        try:
            cursor.execute("SELECT created_at FROM SeminarRegistrations LIMIT 1")
        except:
            print("Adding created_at column to SeminarRegistrations")
            cursor.execute("ALTER TABLE SeminarRegistrations ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
        try:
            cursor.execute("SELECT seminar_title FROM SeminarRegistrations LIMIT 1")
        except:
            print("Adding seminar_title column to SeminarRegistrations")
            cursor.execute("ALTER TABLE SeminarRegistrations ADD COLUMN seminar_title TEXT")
            
        try:
            cursor.execute("SELECT company_name FROM SeminarRegistrations LIMIT 1")
        except:
            print("Adding company_name column to SeminarRegistrations")
            cursor.execute("ALTER TABLE SeminarRegistrations ADD COLUMN company_name TEXT")
            
        try:
            cursor.execute("SELECT position FROM SeminarRegistrations LIMIT 1")
        except:
            print("Adding position column to SeminarRegistrations")
            cursor.execute("ALTER TABLE SeminarRegistrations ADD COLUMN position TEXT")
            
        try:
            cursor.execute("SELECT biz_no FROM SeminarRegistrations LIMIT 1")
        except:
            print("Adding biz_no column to SeminarRegistrations")
            cursor.execute("ALTER TABLE SeminarRegistrations ADD COLUMN biz_no TEXT")
    
    # 초기 팀원 데이터 삽입 (없는 경우)
        cursor.execute("SELECT COUNT(*) FROM ys_team_members")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO ys_team_members (name, position, phone, bio, display_order)
                VALUES 
                ('양철호', '(수석팀장) Senior Team Leader', '010-0000-0000', 
                 '삼성SDS, 하나은행, 삼성카드 재직, IT, 매출, 회계 및 포인트 경력, 물리적 기술적 보안관리, LMS 시스템 개발, 홈페이지 등 각종 플랫폼 구축가능', 1),
                ('서은정', '(팀장) Team Leader', '010-0000-0000',
                 'HSBC, 삼성생명, 삼성화재 재무설계 20년 경력, 변액연금, 펀드, M&A 전문 자격증 보유, 미스코리아 마포 진', 2)
            ''')
        
        # 초기 세미나 데이터 삽입 (없는 경우)
        cursor.execute("SELECT COUNT(*) FROM ys_seminars")
        if cursor.fetchone()[0] == 0:
            initial_seminars = [
                ('세법 법인 대표 CEO 절세를 위한', '1월 27일 (화)', '10:00 - 11:50', '삼성생명 서초사옥 35층', '법인 증여 상속 누가 먼저 하나<br>정말 혁신적이고 국세청 세무조사 무조건 따른다'),
                ('법인 결산 후 필수점검 세미나', '1월 27일 (화)', '10:00 - 11:50', '삼성생명 서초사옥 35층', '법인 결산 후 필수점검 세미나<br>법인 결산 후 필수점검 세미나2'),
                ('세법개정 리뷰 및 결산 후 법인 필수 점검 사항', '1월 29일 (목)', '14:00 - 16:00', '강남 FP 센터', '미 국 세 법 의 이 해 와 활 용<br>미국 시민권자 소득세신고 및 해외 금융 계좌 보고')
            ]
            
            for s in initial_seminars:
                cursor.execute('''
                    INSERT INTO ys_seminars (title, date, time, location, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', s)
        
        # 초기 질문 데이터 삽입 (없는 경우)
        cursor.execute("SELECT COUNT(*) FROM ys_questions")
        if cursor.fetchone()[0] == 0:
            questions = [
                "법인 설립 시 발기인수를 맞추기 위해 타인을 주주로 등록 하셨습니까?",
                "대표이사 가지급금의 적절한 활용 및 처리 문제로 고민하고 계십니까?",
                "누적된 이익잉여금의 효과적인 활용법(급여, 배당)을 고민중이십니까?",
                "자녀에게 가업승계를 준비하고 계십니까?",
                "퇴직금제도 운영으로 안정적인 노후 자금을 마련하고자 하십니까?",
                "중소기업 인증제도(기업부설연구소, 이노비즈 등)를 활용하고 계십니까?",
                "중대재해처벌법, 대비하고 계십니까?",
                "대표님 유고시 발생할 수 있는 리스크헷지 방법에 대해 준비하고 계십니까?"
            ]
            for i, q in enumerate(questions, 1):
                cursor.execute('''
                    INSERT INTO ys_questions (question_text, display_order, is_active)
                    VALUES (?, ?, 1)
                ''', (q, i))
        
        conn.commit()
        print("YS Honers 테이블 초기화 완료")
        
    except Exception as e:
        print(f"YS Honers 테이블 초기화 실패: {e}")
        conn.rollback()
    finally:
        conn.close()

# 메인 비즈니스 테이블 초기화 함수
def init_business_tables():
    """메인 비즈니스 테이블들을 초기화합니다. (기존 데이터 보존)"""
    conn = get_db_connection()
    try:
        # 기존 테이블 존재 여부 확인
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Company_Basic';")
        company_basic_exists = cursor.fetchone()
        
        if company_basic_exists:
            print("Business tables already exist with data - skipping initialization")
            return
        
        # 테이블이 없는 경우에만 생성
        print("Creating new business tables...")
        
        # 기업정보 테이블 생성
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                business_number TEXT UNIQUE,
                representative_name TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                business_type TEXT,
                established_date TEXT,
                employee_count INTEGER,
                capital_amount INTEGER,
                annual_revenue INTEGER,
                main_products TEXT,
                website TEXT,
                notes TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                updated_by TEXT
            )
        ''')
        
        # 연락처 테이블 생성
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                name TEXT NOT NULL,
                position TEXT,
                department TEXT,
                phone TEXT,
                mobile TEXT,
                email TEXT,
                notes TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                updated_by TEXT,
                FOREIGN KEY (company_id) REFERENCES Companies (id)
            )
        ''')
        
        # 비용등록 테이블 생성
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_date DATE NOT NULL,
                biz_no TEXT,
                expense_type TEXT NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                description TEXT,
                receipt_file TEXT,
                registered_by TEXT NOT NULL,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (registered_by) REFERENCES Users(user_id)
            )
        ''')
        
        # C-Level 개척관리 테이블 생성
        conn.execute('''
            CREATE TABLE IF NOT EXISTS CLevel_Targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                biz_no TEXT,
                target_name TEXT NOT NULL,
                target_position TEXT,
                contact_info TEXT,
                target_date DATE,
                approach_method TEXT,
                status TEXT DEFAULT 'PLANNED' CHECK (status IN ('PLANNED', 'IN_PROGRESS', 'CONTACTED', 'COMPLETED', 'CANCELLED')),
                notes TEXT,
                registered_by TEXT NOT NULL,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (registered_by) REFERENCES Users(user_id)
            )
        ''')
        
        # 개척대상 기업 테이블 생성
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Pioneering_Targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                biz_no TEXT NOT NULL,
                visit_date DATE NOT NULL,
                visitor_id TEXT NOT NULL,
                is_visited BOOLEAN DEFAULT 0,
                visited_date DATETIME,
                notes TEXT,
                registered_by TEXT NOT NULL,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (visitor_id) REFERENCES Users(user_id),
                FOREIGN KEY (registered_by) REFERENCES Users(user_id)
            )
        ''')
        
        # 영업비용 테이블 생성
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Sales_Expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_date DATE NOT NULL,
                expense_type TEXT NOT NULL CHECK (expense_type IN ('식대', '교통비', '주차비', '경조사', '우편료', '기타')),
                amount INTEGER NOT NULL,
                payment_method TEXT NOT NULL CHECK (payment_method IN ('법인카드', '개인카드', '현금')),
                description TEXT,
                receipt_file TEXT,
                registered_by TEXT NOT NULL,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (registered_by) REFERENCES Users(user_id)
            )
        ''')
        
        conn.commit()
        print("Business tables initialized successfully")
        
    except Exception as e:
        print(f"Error initializing business tables: {e}")
    finally:
        conn.close()

# 개인사업자(전단계) 테이블 초기화 함수
def init_individual_business_tables():
    """개인사업자(전단계) 관리 테이블을 초기화합니다."""
    conn = get_db_connection()
    try:
        # 기존 테이블 존재 여부 확인
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='individual_business_owners';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("Individual business tables already exist - skipping initialization")
            return
            
        print("Creating individual business tables...")
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS individual_business_owners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,         -- 기업명
                representative_name TEXT,           -- 대표자명
                birth_year INTEGER,                 -- 출생년도
                establishment_year INTEGER,         -- 설립년도
                is_family_shareholder TEXT DEFAULT 'N', -- 가족주주 여부
                is_other_shareholder TEXT DEFAULT 'N',  -- 타인주주 여부
                industry_type TEXT,                 -- 업종
                financial_year INTEGER,             -- 재무제표 연도
                employee_count INTEGER,             -- 종업원수
                total_assets INTEGER,               -- 총자산 (억)
                total_capital INTEGER,              -- 자본총계 (억)
                revenue INTEGER,                    -- 매출액 (억)
                net_income INTEGER,                 -- 당기순이익 (억)
                address TEXT,                       -- 사업장주소
                business_number TEXT UNIQUE,        -- 사업자번호
                phone_number TEXT,                  -- 전화번호
                fax_number TEXT,                    -- fax번호
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("Individual business tables initialized successfully")
        
    except Exception as e:
        print(f"Error initializing individual business tables: {e}")
    finally:
        conn.close()

# 패스워드 규칙 검증 함수
def validate_password(password):
    """
    패스워드 규칙을 검증합니다.
    규칙: 8자 이상, 영문 대/소문자, 숫자, 특수문자 조합
    """
    import re
    
    if len(password) < 8:
        return False, "비밀번호는 8자 이상이어야 합니다."
    
    if len(password) > 20:
        return False, "비밀번호는 20자 이하여야 합니다."
    
    # 영문 대문자 포함 여부
    if not re.search(r'[A-Z]', password):
        return False, "비밀번호에 영문 대문자가 포함되어야 합니다."
    
    # 영문 소문자 포함 여부
    if not re.search(r'[a-z]', password):
        return False, "비밀번호에 영문 소문자가 포함되어야 합니다."
    
    # 숫자 포함 여부
    if not re.search(r'[0-9]', password):
        return False, "비밀번호에 숫자가 포함되어야 합니다."
    
    # 특수문자 포함 여부
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "비밀번호에 특수문자(!@#$%^&*(),.?\":{}|<>)가 포함되어야 합니다."
    
    return True, "유효한 비밀번호입니다."

# 패스워드 이력 확인 함수
def check_password_history(user_id, new_password, history_count=5):
    """
    사용자의 최근 패스워드 이력을 확인하여 중복 사용을 방지합니다.
    """
    conn = get_db_connection()
    try:
        # 최근 사용한 패스워드 조회 (최대 history_count개)
        recent_passwords = conn.execute('''
            SELECT password FROM Password_History 
            WHERE user_id = ? 
            ORDER BY created_date DESC 
            LIMIT ?
        ''', (user_id, history_count)).fetchall()
        
        # 현재 사용 중인 패스워드도 확인
        current_password = conn.execute('''
            SELECT password FROM Users WHERE user_id = ?
        ''', (user_id,)).fetchone()
        
        if current_password and current_password['password'] == new_password:
            return False, "현재 사용 중인 비밀번호와 동일합니다."
        
        for row in recent_passwords:
            if row['password'] == new_password:
                return False, f"최근 {history_count}개의 비밀번호 중 이미 사용한 비밀번호입니다."
        
        return True, "사용 가능한 비밀번호입니다."
    finally:
        conn.close()

# 패스워드 이력 저장 함수
def save_password_history(user_id, password):
    """
    패스워드 변경 시 이력을 저장합니다.
    """
    conn = get_db_connection()
    try:
        # 현재 패스워드를 이력에 저장
        current_password = conn.execute('''
            SELECT password FROM Users WHERE user_id = ?
        ''', (user_id,)).fetchone()
        
        if current_password:
            conn.execute('''
                INSERT INTO Password_History (user_id, password)
                VALUES (?, ?)
            ''', (user_id, current_password['password']))
        
        # 오래된 이력 정리 (최근 10개만 유지)
        conn.execute('''
            DELETE FROM Password_History 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM Password_History 
                WHERE user_id = ? 
                ORDER BY created_date DESC 
                LIMIT 10
            )
        ''', (user_id, user_id))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# 사용자 인증 함수
def authenticate_user(user_id, password):
    """사용자 인증을 수행합니다."""
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT * FROM Users WHERE user_id = ? AND status = 'ACTIVE'", 
            (user_id,)
        ).fetchone()
        
        if user and user['password'] == password:
            # 마지막 로그인 시간 업데이트
            conn.execute(
                "UPDATE Users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            return dict(user)
        return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    finally:
        conn.close()

# 사용자 정보 조회 함수
def get_user_info(user_id):
    """사용자 정보를 조회합니다."""
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT * FROM Users WHERE user_id = ? AND status = 'ACTIVE'", 
            (user_id,)
        ).fetchone()
        return dict(user) if user else None
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None
    finally:
        conn.close()

# 권한 확인 함수
def check_permission(user_level, required_level):
    """사용자 권한을 확인합니다."""
    level_hierarchy = {'V': 4, 'S': 3, 'M': 2, 'N': 1}
    return level_hierarchy.get(user_level, 0) >= level_hierarchy.get(required_level, 0)

# 앱 시작 시 데이터베이스 및 사용자 테이블 초기화
def initialize_application():
    """애플리케이션 초기화 함수"""
    print("=== Application Initialization ===")
    print(f"Environment: {'Render' if os.environ.get('RENDER') else 'Local'}")
    print(f"Database Path: {DB_PATH}")
    
    # Render 환경에서 Persistent Disk 상태 확인
    if os.environ.get('RENDER'):
        persistent_disk_path = '/var/data'
        if os.path.exists(persistent_disk_path):
            print("? Persistent Disk detected and mounted")
            # 디스크 용량 확인
            try:
                import shutil
                total, used, free = shutil.disk_usage(persistent_disk_path)
                print(f"  Disk space - Total: {total//1024**3}GB, Used: {used//1024**3}GB, Free: {free//1024**3}GB")
            except:
                pass
        else:
            print("? Persistent Disk not found - using fallback storage")
    
    # 데이터베이스 파일 존재 여부 확인
    if os.path.exists(DB_PATH):
        print(f"? Database file exists: {DB_PATH}")
        try:
            # 데이터베이스 연결 테스트
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
            conn.close()
            print("? Database connection successful")
        except Exception as e:
            print(f"? Database connection test failed: {e}")
    else:
        print(f"Creating new database: {DB_PATH}")
    
    # 사용자 테이블 초기화
    init_user_tables()
    print("=== Initialization Complete ===")

# 앱 시작 시 초기화 실행
initialize_application()

# --- 비상장 주식 가치 계산 ---
def calculate_unlisted_stock_value(financial_data):
    """
    필요한 재무 항목:
    - total_assets: 자산총계
    - total_liabilities: 부채총계
    - net_income: 순이익(최근 3년 평균)
    - shares_issued_count: 발행주식수(없으면 자본금/5000)
    - capital_stock_value: 자본금
    """
    if not financial_data:
        return {}
    df_financial = pd.DataFrame(financial_data)
    if df_financial.empty:
        return {}

    latest_data = df_financial.sort_values(by='fiscal_year', ascending=False).iloc[0]

    total_assets = float(latest_data.get('total_assets') or 0)
    total_liabilities = float(latest_data.get('total_liabilities') or 0)

    # 최근 3년 평균 순이익
    net_income_3y_avg = pd.to_numeric(df_financial['net_income'], errors='coerce').mean()
    if pd.isna(net_income_3y_avg):
        net_income_3y_avg = 0

    asset_value = total_assets - total_liabilities
    profit_value = net_income_3y_avg / 0.1 if net_income_3y_avg else 0

    calculated_value = (asset_value * 2 + profit_value * 3) / 5

    # 주식수 계산 - 계층적 fallback 적용
    total_shares = float(latest_data.get('shares_issued_count') or 0)
    
    # 1단계: shares_issued_count가 없거나 1 이하인 경우
    if total_shares <= 1:
        # 2단계: 주주 소유 주식수 합계 시도
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(CAST(total_shares_owned AS REAL)) 
                FROM Company_Shareholder 
                WHERE biz_no = ? AND total_shares_owned IS NOT NULL AND total_shares_owned != ''
            """, (latest_data.get('biz_no', ''),))
            total_owned_shares = cursor.fetchone()[0]
            conn.close()
            
            if total_owned_shares and total_owned_shares > 0:
                total_shares = total_owned_shares
            else:
                # 3단계: 자본금/5000 계산
                capital_stock = float(latest_data.get('capital_stock_value') or 0)
                if capital_stock > 0:
                    total_shares = capital_stock / 5000
                else:
                    total_shares = 1
        except Exception as e:
            print(f"주주 소유 주식수 합계 계산 오류: {e}")
            # 3단계: 자본금/5000 계산
            capital_stock = float(latest_data.get('capital_stock_value') or 0)
            if capital_stock > 0:
                total_shares = capital_stock / 5000
            else:
                total_shares = 1
    
    if total_shares == 0:
        total_shares = 1

    stock_value = calculated_value / total_shares if total_shares else 0

    return {
        "asset_value": asset_value,
        "profit_value": profit_value,
        "calculated_value": calculated_value,
        "total_shares_issued": total_shares,
        "estimated_stock_value": stock_value
    }

# --- 기업정보 데이터 조회 함수 추가 ---
def query_companies_data(args):
    conn = get_db_connection()
    query = """
        SELECT
            b.*,
            f.fiscal_year,
            f.total_assets,
            f.sales_revenue,
            f.retained_earnings
        FROM Company_Basic b
        LEFT JOIN (
            SELECT biz_no, fiscal_year, total_assets, sales_revenue, retained_earnings
            FROM Company_Financial
            WHERE (biz_no, fiscal_year) IN (
                SELECT biz_no, MAX(fiscal_year) FROM Company_Financial GROUP BY biz_no
            )
        ) f ON b.biz_no = f.biz_no
    """
    filters = []
    params = []
    if args.get('biz_no'):
        filters.append("b.biz_no LIKE ?")
        params.append(f"%{args.get('biz_no')}%")
    if args.get('company_name'):
        filters.append("b.company_name LIKE ?")
        params.append(f"%{args.get('company_name')}%")
    if args.get('industry_name'):
        filters.append("b.industry_name LIKE ?")
        params.append(f"%{args.get('industry_name')}%")
    if args.get('company_size') and args.get('company_size') != '전체':
        filters.append("b.company_size = ?")
        params.append(args.get('company_size'))
    
    # [ACCESS CONTROL] 파이프라인 등록 기업 제외 로직
    # 로그인한 사용자가 파이프라인에 등록하지 않은(혹은 파트너가 등록하지 않은) 기업은 검색에서 제외
    current_user_id = session.get('user_id')
    if current_user_id:
        allowed_managers = [current_user_id]
        if current_user_id in ['ct0001', 'ct0002']:
            allowed_managers = ['ct0001', 'ct0002']
            
        # 제외 대상: managed_companies에 있지만, manager_id가 allowed_managers에 없는 기업
        mgr_placeholders = ','.join(['?'] * len(allowed_managers))
        
        # NOT IN (SELECT biz_reg_no FROM managed_companies WHERE manager_id NOT IN (...))
        filters.append(f"""
            b.biz_no NOT IN (
                SELECT biz_reg_no FROM managed_companies 
                WHERE manager_id NOT IN ({mgr_placeholders})
            )
        """)
        # 주의: 이니셜라이징된 managed_companies 데이터가 없거나, 모두 내가 관리하는 경우 등
        # 로직: "다른 사람이 관리 중인 기업"을 제외.
        # 즉, managed_companies 테이블에 존재하면서, manager_id가 내 그룹(allowed_managers)에 속하지 않는 기업을 제외
        
        params.extend(allowed_managers) 

    # 지역(주소) 검색: 모든 키워드가 포함되어야 함
    if args.get('region'):
        region_keywords = [kw.strip() for kw in args.get('region').split() if kw.strip()]
        for kw in region_keywords:
            filters.append("b.address LIKE ?")
            params.append(f"%{kw}%")
    # 이익잉여금 min/max (retained_earnings, 백만단위 입력값을 실제 단위로 변환)
    if args.get('ret_min'):
        try:
            ret_min_val = int(args.get('ret_min')) * 1000000
            filters.append("f.retained_earnings >= ?")
            params.append(ret_min_val)
        except Exception:
            pass
    if args.get('ret_max'):
        try:
            ret_max_val = int(args.get('ret_max')) * 1000000
            filters.append("f.retained_earnings <= ?")
            params.append(ret_max_val)
        except Exception:
            pass
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY b.biz_no"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# --- 로그아웃 라우트 추가 ---
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

# --- 접촉이력 조회 라우트 추가 ---
@app.route('/history')
def history_search():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('history.html', user_name=session.get('user_name'))

# --- 로그인 라우트 추가 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        
        # DB 기반 사용자 인증
        user_info = authenticate_user(user_id, password)
        if user_info:
            session['logged_in'] = True
            session['user_id'] = user_id
            session['user_name'] = user_info['name']
            session['user_level'] = user_info['user_level']
            session['user_level_name'] = user_info['user_level_name']
            session['branch_code'] = user_info['branch_code']
            session['branch_name'] = user_info['branch_name']
            session['phone'] = user_info['phone']
            
            # 임시 비밀번호(password1!) 체크
            if password == 'password1!':
                return redirect(url_for('change_password_first_time'))
            
            return redirect(url_for('main'))
        else:
            error = '아이디 또는 비밀번호가 올바르지 않습니다.'
    return render_template('login.html', error=error)

@app.route('/change-password-first-time', methods=['GET', 'POST'])
def change_password_first_time():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 현재 비밀번호가 임시 비밀번호인지 확인
        if current_password != 'password1!':
            return render_template('change_password_first.html', 
                                 error='현재 비밀번호가 올바르지 않습니다.')
        
        # 새 비밀번호 확인
        if new_password != confirm_password:
            return render_template('change_password_first.html', 
                                 error='새 비밀번호가 일치하지 않습니다.')
        
        # 비밀번호 복잡성 검증
        if not validate_password(new_password):
            return render_template('change_password_first.html', 
                                 error='비밀번호는 8-20자리이며, 대문자, 소문자, 숫자, 특수문자를 각각 하나 이상 포함해야 합니다.')
        
        # 임시 비밀번호와 같으면 안됨
        if new_password == 'password1!':
            return render_template('change_password_first.html', 
                                 error='임시 비밀번호와 같은 비밀번호는 사용할 수 없습니다.')
        
        user_id = session.get('user_id')
        
        # 비밀번호 변경
        conn = get_db_connection()
        try:
            # 패스워드 이력 저장
            save_password_history(user_id, new_password)
            
            # 비밀번호 업데이트
            conn.execute('''
                UPDATE Users SET 
                    password=?, 
                    password_changed_date=date('now'),
                    updated_date=CURRENT_TIMESTAMP
                WHERE user_id=?
            ''', (new_password, user_id))
            conn.commit()
            
            return redirect(url_for('main'))
        except Exception as e:
            conn.rollback()
            return render_template('change_password_first.html', 
                                 error=f'비밀번호 변경 중 오류가 발생했습니다: {str(e)}')
        finally:
            conn.close()
    
    return render_template('change_password_first.html')

# --- index(홈) 페이지 라우트 추가 ---

# --- 구독 정보 조회 함수 ---
def get_user_subscription_info(user_id):
    """사용자의 구독 정보를 조회하고 남은 날짜를 계산하여 반환"""
    if not user_id:
        return None
    
    conn = get_db_connection()
    try:
        # 먼저 User_Subscriptions 테이블이 존재하는지 확인
        table_exists = conn.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='User_Subscriptions'
        ''').fetchone()
        
        if not table_exists:
            # 테이블이 없으면 기본값 반환
            print(f"User_Subscriptions 테이블이 없습니다. 기본 구독 정보를 반환합니다.")
            return {
                'subscription_type': 'Basic',
                'start_date': None,
                'end_date': None,
                'days_remaining': 365,  # 기본 1년
                'status': 'Active'
            }
        
        # 사용자 구독 정보 조회 (실제 테이블 스키마 사용)
        subscription_info = conn.execute('''
            SELECT subscription_type, subscription_start_date, subscription_end_date, created_date
            FROM User_Subscriptions 
            WHERE user_id = ?
            ORDER BY created_date DESC 
            LIMIT 1
        ''', (user_id,)).fetchone()
        
        if subscription_info:
            from datetime import datetime, date
            if subscription_info['subscription_end_date']:
                end_date = datetime.strptime(subscription_info['subscription_end_date'], '%Y-%m-%d').date()
                today = date.today()
                days_remaining = (end_date - today).days
                
                return {
                    'subscription_type': subscription_info['subscription_type'],
                    'start_date': subscription_info['subscription_start_date'],
                    'end_date': subscription_info['subscription_end_date'],
                    'days_remaining': days_remaining,
                    'status': 'Active' if days_remaining > 0 else 'Expired'
                }
        
        # 구독 정보가 없으면 기본값 반환
        return {
            'subscription_type': 'Basic',
            'start_date': None,
            'end_date': None,
            'days_remaining': 365,  # 기본 1년
            'status': 'Active'
        }
        
    except Exception as e:
        print(f"구독 정보 조회 오류: {e}")
        # 오류 발생 시 기본값 반환
        return {
            'subscription_type': 'Basic',
            'start_date': None,
            'end_date': None,
            'days_remaining': 365,
            'status': 'Active'
        }
    finally:
        conn.close()

# --- DB 관리 및 진단 라우트 ---
@app.route('/db_info')
def db_info():
    """데이터베이스 정보 확인"""
    try:
        conn = get_db_connection()
        
        # 테이블 목록 확인
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        table_names = [table[0] for table in tables]
        
        # DB 파일 정보
        import os
        db_path = DB_PATH
        db_exists = os.path.exists(db_path)
        db_size = os.path.getsize(db_path) if db_exists else 0
        
        conn.close()
        
        return jsonify({
            "database_path": db_path,
            "database_exists": db_exists,
            "database_size_mb": round(db_size / (1024*1024), 2),
            "tables": table_names,
            "render_environment": os.environ.get('RENDER', 'false'),
            "persistent_disk": os.path.exists('/var/data') if os.environ.get('RENDER') else 'N/A'
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/check_tables')
def check_tables():
    """각 테이블의 존재 여부와 데이터 개수 확인"""
    try:
        conn = get_db_connection()
        results = {}
        
        # 확인할 테이블 목록 (파이프라인 테이블 추가)
        tables_to_check = [
            'Users', 'User_Subscriptions', 'Company_Basic', 
            'Contact_History', 'Signup_Requests', 'Pioneering_Targets', 
            'Sales_Expenses', 'Company_Financial', 'Company_Shareholder',
            'managed_companies', 'pipeline_contact_history', 'history',
            'Password_History', 'Payment_History', 'Branches'
        ]
        
        for table_name in tables_to_check:
            try:
                # 테이블 존재 여부 확인
                table_exists = conn.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                ''', (table_name,)).fetchone()
                
                if table_exists:
                    # 데이터 개수 확인
                    count = conn.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]
                    results[table_name] = {
                        "exists": True,
                        "row_count": count,
                        "status": "?" if count > 0 else "Empty"
                    }
                else:
                    results[table_name] = {
                        "exists": False,
                        "row_count": 0,
                        "status": "? Missing"
                    }
            except Exception as e:
                results[table_name] = {
                    "exists": False,
                    "row_count": 0,
                    "status": f"Error: {str(e)}"
                }
        
        conn.close()
        
        return jsonify({
            "database_path": DB_PATH,
            "render_environment": os.environ.get('RENDER', 'false'),
            "tables": results
        })
        
    except Exception as e:
        return jsonify({
            "error": f"테이블 확인 실패: {str(e)}"
        }), 500

@app.route('/fix_db')
def fix_db():
    """Render 서버에서 누락된 테이블들을 생성"""
    if not os.environ.get('RENDER'):
        return jsonify({"error": "이 기능은 Render 서버에서만 사용 가능합니다."}), 403
    
    try:
        conn = get_db_connection()
        results = []
        
        # 누락된 테이블들 생성
        tables_to_create = [
            ("Users", '''
                CREATE TABLE IF NOT EXISTS Users (
                    user_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    user_level TEXT NOT NULL DEFAULT 'N',
                    user_level_name TEXT NOT NULL DEFAULT '일반담당자',
                    branch_code TEXT NOT NULL DEFAULT 'DEFAULT',
                    branch_name TEXT NOT NULL DEFAULT '기본지점',
                    phone TEXT,
                    gender TEXT,
                    birth_date TEXT,
                    email TEXT,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login TEXT
                )
            '''),
            ("User_Subscriptions", '''
                CREATE TABLE IF NOT EXISTS User_Subscriptions (
                    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    subscription_start_date DATE,
                    subscription_end_date DATE,
                    subscription_type TEXT DEFAULT 'Basic',
                    total_paid_amount INTEGER DEFAULT 0,
                    is_first_month_free BOOLEAN DEFAULT 0,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            '''),
            ("Company_Basic", '''
                CREATE TABLE IF NOT EXISTS Company_Basic (
                    biz_no TEXT PRIMARY KEY,
                    company_name TEXT,
                    representative_name TEXT,
                    establish_date TEXT,
                    company_size TEXT,
                    industry_name TEXT,
                    region TEXT,
                    address TEXT,
                    phone TEXT,
                    status TEXT DEFAULT 'ACTIVE'
                )
            '''),
            ("Contact_History", '''
                CREATE TABLE IF NOT EXISTS Contact_History (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    biz_no TEXT,
                    contact_datetime TEXT,
                    contact_type TEXT,
                    contact_person TEXT,
                    memo TEXT,
                    registered_by TEXT,
                    registered_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            '''),
            ("Signup_Requests", '''
                CREATE TABLE IF NOT EXISTS Signup_Requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    branch_code TEXT,
                    branch_name TEXT,
                    purpose TEXT,
                    status TEXT DEFAULT 'PENDING',
                    requested_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    processed_date TEXT,
                    processed_by TEXT
                )
            '''),
            ("Pioneering_Targets", '''
                CREATE TABLE IF NOT EXISTS Pioneering_Targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    biz_no TEXT,
                    visit_date TEXT,
                    visitor_id TEXT,
                    purpose TEXT,
                    result TEXT,
                    memo TEXT,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            '''),
            ("Sales_Expenses", '''
                CREATE TABLE IF NOT EXISTS Sales_Expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_date TEXT,
                    user_id TEXT,
                    expense_type TEXT,
                    amount INTEGER,
                    description TEXT,
                    receipt_url TEXT,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            '''),
            ("managed_companies", '''
                CREATE TABLE IF NOT EXISTS managed_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    biz_reg_no TEXT NOT NULL,
                    company_name TEXT,
                    representative TEXT,
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
                )
            '''),
            ("pipeline_contact_history", '''
                CREATE TABLE IF NOT EXISTS pipeline_contact_history (
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
                )
            ''')
        ]
        
        for table_name, create_sql in tables_to_create:
            try:
                conn.execute(create_sql)
                results.append(f"? {table_name} 테이블 생성 완료")
            except Exception as e:
                results.append(f"? {table_name} 테이블 생성 실패: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": "데이터베이스 수정 완료",
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"데이터베이스 수정 실패: {str(e)}"
        }), 500

@app.route('/upload_database', methods=['GET', 'POST'])
def upload_database():
    """데이터베이스 파일 업로드"""
    if request.method == 'GET':
        html_content = '''<!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>데이터베이스 업로드</title>
            <style>
                body { 
                    font-family: 'Malgun Gothic', sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0; padding: 20px; min-height: 100vh;
                }
                .container { 
                    max-width: 600px; margin: 50px auto; 
                    background: rgba(255,255,255,0.95);
                    border-radius: 15px; padding: 30px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }
                h2 { color: #333; text-align: center; margin-bottom: 30px; }
                .upload-area {
                    border: 2px dashed #ccc; padding: 40px; text-align: center;
                    border-radius: 10px; margin: 20px 0;
                    transition: all 0.3s ease;
                }
                .upload-area:hover { border-color: #667eea; background: #f8f9ff; }
                .upload-area.dragover { border-color: #667eea; background: #e8f0fe; }
                input[type="file"] { margin: 20px 0; }
                button {
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    color: white; border: none; padding: 12px 30px;
                    border-radius: 25px; cursor: pointer; font-size: 16px;
                    transition: all 0.3s ease;
                }
                button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
                .info { background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; }
                .warning { background: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0; }
                #progress { display: none; margin: 20px 0; }
                .progress-bar { 
                    width: 100%; height: 20px; background: #f0f0f0; 
                    border-radius: 10px; overflow: hidden;
                }
                .progress-fill { 
                    height: 100%; background: linear-gradient(45deg, #667eea, #764ba2);
                    width: 0%; transition: width 0.3s ease;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>데이터베이스 파일 업로드</h2>
                
                <div class="info">
                    <strong>업로드 안내:</strong><br>
                    ? 로컬 <code>company_database.db</code> 파일을 선택하세요<br>
                    ? 파일 크기: 약 75MB (66만+ 레코드)<br>
                    ? 업로드 후 기존 데이터베이스는 자동 백업됩니다
                </div>
                
                <div class="warning">
                    <strong>주의사항:</strong><br>
                    ? 업로드 중에는 페이지를 새로고침하지 마세요<br>
                    ? 네트워크 상태가 안정적인 곳에서 진행하세요<br>
                    ? 기존 데이터는 .backup 파일로 백업됩니다
                </div>
                
                <form id="uploadForm" method="post" enctype="multipart/form-data">
                    <div class="upload-area" id="uploadArea">
                        <p>파일을 여기에 드래그하거나 클릭하여 선택하세요</p>
                        <input type="file" name="database" accept=".db" required id="fileInput">
                        <p id="fileName" style="color: #666; margin-top: 10px;"></p>
                    </div>
                    
                    <div id="progress">
                        <p>업로드 중...</p>
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill"></div>
                        </div>
                    </div>
                    
                    <button type="submit">업로드 & 복원</button>
                </form>
                
                <div id="result" style="margin-top: 20px;"></div>
            </div>
            
            <script>
                const uploadArea = document.getElementById('uploadArea');
                const fileInput = document.getElementById('fileInput');
                const fileName = document.getElementById('fileName');
                const uploadForm = document.getElementById('uploadForm');
                const progress = document.getElementById('progress');
                const result = document.getElementById('result');
                
                // 드래그 앤 드롭 이벤트
                uploadArea.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    uploadArea.classList.add('dragover');
                });
                
                uploadArea.addEventListener('dragleave', () => {
                    uploadArea.classList.remove('dragover');
                });
                
                uploadArea.addEventListener('drop', (e) => {
                    e.preventDefault();
                    uploadArea.classList.remove('dragover');
                    fileInput.files = e.dataTransfer.files;
                    updateFileName();
                });
                
                uploadArea.addEventListener('click', () => {
                    fileInput.click();
                });
                
                fileInput.addEventListener('change', updateFileName);
                
                function updateFileName() {
                    if (fileInput.files.length > 0) {
                        const file = fileInput.files[0];
                        fileName.textContent = `선택된 파일: ${file.name} (${(file.size/1024/1024).toFixed(1)}MB)`;
                    }
                }
                
                // 폼 제출 처리
                uploadForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    if (!fileInput.files.length) {
                        alert('파일을 선택해주세요.');
                        return;
                    }
                    
                    progress.style.display = 'block';
                    result.innerHTML = '';
                    
                    const formData = new FormData();
                    formData.append('database', fileInput.files[0]);
                    
                    try {
                        const response = await fetch('/upload_database', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            result.innerHTML = `
                                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; color: #2e7d32;">
                                    <strong>? ${data.message}</strong><br>
                                    생성된 테이블: ${data.tables.join(', ')}
                                </div>
                            `;
                        } else {
                            result.innerHTML = `
                                <div style="background: #ffebee; padding: 15px; border-radius: 8px; color: #c62828;">
                                    <strong>? ${data.message}</strong>
                                </div>
                            `;
                        }
                    } catch (error) {
                        result.innerHTML = `
                            <div style="background: #ffebee; padding: 15px; border-radius: 8px; color: #c62828;">
                                <strong>업로드 실패: ${error.message}</strong>
                            </div>
                        `;
                    } finally {
                        progress.style.display = 'none';
                    }
                });
            </script>
        </body>
        </html>
        '''
        
        # 한글 인코딩 문제 해결을 위해 응답 헤더 설정
        from flask import Response
        return Response(html_content, content_type='text/html; charset=utf-8')
    
    if 'database' not in request.files:
        return jsonify({"success": False, "message": "파일이 선택되지 않았습니다"})
    
    file = request.files['database']
    if file.filename == '':
        return jsonify({"success": False, "message": "파일이 선택되지 않았습니다"})
    
    try:
        # 기존 데이터베이스 백업
        db_path = DB_PATH
        backup_path = db_path + '.backup'
        
        import shutil
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
        
        # 새 데이터베이스 파일 저장
        file.save(db_path)
        
        # 업로드된 파일 검증
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        success_response = jsonify({
            "success": True, 
            "message": f"데이터베이스 업로드 완료. {len(tables)}개 테이블 확인됨",
            "tables": [table[0] for table in tables]
        })
        success_response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return success_response
        
    except Exception as e:
        error_response = jsonify({"success": False, "message": f"업로드 실패: {str(e)}"})
        error_response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return error_response

@app.route('/download_database')
def download_database():
    """완전 백업: 데이터베이스 + 첨부파일을 압축하여 다운로드"""
    import zipfile
    import tempfile
    try:
        db_path = DB_PATH
        uploads_path = app.config['UPLOAD_FOLDER']
        
        if not os.path.exists(db_path):
            return jsonify({
                "success": False, 
                "message": "데이터베이스 파일이 존재하지 않습니다."
            }), 404
        
        # 현재 시간으로 파일명 생성
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 임시 ZIP 파일 생성
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 데이터베이스 파일 추가
            zipf.write(db_path, f"company_database_{timestamp}.db")
            
            # uploads 폴더의 모든 파일 추가 (있는 경우)
            if os.path.exists(uploads_path):
                for root, dirs, files in os.walk(uploads_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # ZIP 내부에서의 상대 경로 설정
                        arcname = os.path.join('uploads', os.path.relpath(file_path, uploads_path))
                        zipf.write(file_path, arcname)
        
        download_filename = f"company_system_backup_{timestamp}.zip"
        
        # ZIP 파일을 응답으로 전송하고 임시 파일 삭제
        def remove_temp_file(response):
            try:
                os.unlink(temp_zip.name)
            except:
                pass
            return response
        
        response = send_file(
            temp_zip.name,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/zip'
        )
        
        # 응답 완료 후 임시 파일 삭제를 위한 후처리
        response.call_on_close(lambda: os.unlink(temp_zip.name) if os.path.exists(temp_zip.name) else None)
        
        return response
        
    except Exception as e:
        error_response = jsonify({
            "success": False, 
            "message": f"백업 다운로드 실패: {str(e)}"
        })
        error_response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return error_response, 500

@app.route('/download_database_only')
def download_database_only():
    """데이터베이스 파일만 다운로드 (기존 기능)"""
    try:
        db_path = DB_PATH
        
        if not os.path.exists(db_path):
            return jsonify({
                "success": False, 
                "message": "데이터베이스 파일이 존재하지 않습니다."
            }), 404
        
        # 현재 시간으로 파일명 생성
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_filename = f"company_database_{timestamp}.db"
        
        return send_file(
            db_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        error_response = jsonify({
            "success": False, 
            "message": f"다운로드 실패: {str(e)}"
        })
        error_response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return error_response, 500

@app.route('/download')
def download_page():
    """데이터베이스 다운로드 페이지 (메인)"""
    try:
        db_path = DB_PATH
        
        if not os.path.exists(db_path):
            error_response = jsonify({
                "success": False, 
                "message": "데이터베이스 파일이 존재하지 않습니다."
            })
            error_response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return error_response, 404
        
        # 데이터베이스 정보 확인
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # 주요 테이블의 레코드 수 확인
        table_info = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                table_info[table[0]] = count
            except:
                table_info[table[0]] = 0
        
        conn.close()
        
        # 파일 크기 정보
        file_size = os.path.getsize(db_path)
        file_size_mb = round(file_size / (1024 * 1024), 2)
        
        # 현재 시간으로 파일명 생성
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_filename = f"company_database_{timestamp}.db"
        
        return send_file(
            db_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        error_response = jsonify({
            "success": False, 
            "message": f"다운로드 실패: {str(e)}"
        })
        error_response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return error_response, 500

@app.route('/download_info')
def download_database_info():
    """다운로드 전 데이터베이스 정보 확인 (API)"""
    try:
        db_path = DB_PATH
        
        if not os.path.exists(db_path):
            return jsonify({
                "success": False, 
                "message": "데이터베이스 파일이 존재하지 않습니다.",
                "file_exists": False
            })
        
        # 파일 정보
        file_size = os.path.getsize(db_path)
        file_size_mb = round(file_size / (1024 * 1024), 2)
        file_modified = datetime.fromtimestamp(os.path.getmtime(db_path)).strftime("%Y-%m-%d %H:%M:%S")
        
        # 데이터베이스 테이블 정보
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        table_info = {}
        total_records = 0
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                table_info[table[0]] = count
                total_records += count
            except:
                table_info[table[0]] = 0
        
        conn.close()
        
        response_data = {
            "success": True,
            "file_exists": True,
            "file_info": {
                "size_bytes": file_size,
                "size_mb": file_size_mb,
                "modified_date": file_modified,
                "total_tables": len(tables),
                "total_records": total_records
            },
            "table_info": table_info
        }
        
        # JSON 응답에서 한글 인코딩 문제 해결
        response = jsonify(response_data)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        error_response = jsonify({
            "success": False, 
            "message": f"정보 조회 실패: {str(e)}"
        })
        error_response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return error_response, 500

@app.route('/download_database_page')
def download_database_page():
    """데이터베이스 다운로드 페이지"""
    html_content = '''<!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>데이터베이스 다운로드</title>
        <style>
            body { 
                font-family: 'Malgun Gothic', sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; padding: 20px; min-height: 100vh;
            }
            .container { 
                max-width: 700px; margin: 50px auto; 
                background: rgba(255,255,255,0.95);
                border-radius: 15px; padding: 30px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            h2 { color: #333; text-align: center; margin-bottom: 30px; }
            .info-card {
                background: #f8f9fa; padding: 20px; border-radius: 10px;
                margin: 20px 0; border-left: 4px solid #667eea;
            }
            .table-grid {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px; margin: 15px 0;
            }
            .table-item {
                background: white; padding: 10px; border-radius: 5px;
                border: 1px solid #e0e0e0; font-size: 14px;
            }
            .download-area {
                text-align: center; padding: 30px; margin: 20px 0;
                background: linear-gradient(45deg, #e3f2fd, #f3e5f5);
                border-radius: 10px; border: 2px dashed #667eea;
            }
            .btn {
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white; border: none; padding: 15px 30px;
                border-radius: 25px; cursor: pointer; font-size: 16px;
                transition: all 0.3s ease; text-decoration: none;
                display: inline-block; margin: 10px;
            }
            .btn:hover { 
                transform: translateY(-2px); 
                box-shadow: 0 5px 15px rgba(0,0,0,0.2); 
                color: white; text-decoration: none;
            }
            .btn-secondary {
                background: linear-gradient(45deg, #78909c, #546e7a);
            }
            .loading { display: none; margin: 20px 0; text-align: center; }
            .status { margin: 20px 0; padding: 15px; border-radius: 8px; }
            .status.success { background: #e8f5e8; color: #2e7d32; }
            .status.error { background: #ffebee; color: #c62828; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
            .stat-item { 
                text-align: center; padding: 15px; background: white; 
                border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .stat-number { font-size: 24px; font-weight: bold; color: #667eea; }
            .stat-label { font-size: 12px; color: #666; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>데이터베이스 관리</h2>
            
            <div class="info-card">
                <h3>백업 다운로드 안내</h3>
                <ul>
                    <li><strong>완전백업 (권장)</strong>: 데이터베이스 + 첫부파일(영수증 등)을 ZIP으로 압축하여 다운로드</li>
                    <li><strong>DB만 백업</strong>: 데이터베이스 파일만 다운로드 (첫부파일 제외)</li>
                    <li>다운로드된 파일은 타임스탬프가 포함된 이름으로 저장됩니다</li>
                    <li>완전백업 형식: <code>company_system_backup_YYYYMMDD_HHMMSS.zip</code></li>
                    <li>DB만 백업 형식: <code>company_database_YYYYMMDD_HHMMSS.db</code></li>
                </ul>
            </div>
            
            <div id="loading" class="loading">
                <p>데이터베이스 정보를 조회 중...</p>
            </div>
            
            <div id="dbInfo" style="display: none;">
                <div class="stats" id="stats"></div>
                
                <div class="info-card">
                    <h4>테이블별 레코드 수</h4>
                    <div class="table-grid" id="tableGrid"></div>
                </div>
                
                <div class="download-area">
                    <h3>백업 다운로드</h3>
                    <p>위 정보를 확인한 후 다운로드를 진행하세요</p>
                    <button class="btn" onclick="downloadFullBackup()" style="background: linear-gradient(45deg, #4CAF50, #45a049);">
                        완전백업 (DB + 첫부파일)
                    </button>
                    <button class="btn" onclick="downloadDatabaseOnly()" style="background: linear-gradient(45deg, #2196F3, #1976D2);">
                        DB만 백업
                    </button>
                    <a href="/upload_database" class="btn btn-secondary">
                        데이터베이스 복원
                    </a>
                </div>
            </div>
            
            <div id="status" class="status" style="display: none;"></div>
        </div>
        
        <script>
            // 페이지 로드 시 데이터베이스 정보 조회
            window.addEventListener('load', async () => {
                await loadDatabaseInfo();
            });
            
            async function loadDatabaseInfo() {
                const loading = document.getElementById('loading');
                const dbInfo = document.getElementById('dbInfo');
                const status = document.getElementById('status');
                
                loading.style.display = 'block';
                dbInfo.style.display = 'none';
                status.style.display = 'none';
                
                try {
                    const response = await fetch('/download_info');
                    const data = await response.json();
                    
                    if (data.success) {
                        displayDatabaseInfo(data);
                        dbInfo.style.display = 'block';
                    } else {
                        showStatus('error', `${data.message}`);
                    }
                } catch (error) {
                    showStatus('error', `정보 조회 실패: ${error.message}`);
                } finally {
                    loading.style.display = 'none';
                }
            }
            
            function displayDatabaseInfo(data) {
                const stats = document.getElementById('stats');
                const tableGrid = document.getElementById('tableGrid');
                
                // 통계 정보 표시
                stats.innerHTML = `
                    <div class="stat-item">
                        <div class="stat-number">${data.file_info.size_mb}</div>
                        <div class="stat-label">MB</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${data.file_info.total_tables}</div>
                        <div class="stat-label">테이블</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${data.file_info.total_records.toLocaleString()}</div>
                        <div class="stat-label">레코드</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number" style="font-size: 14px;">${data.file_info.modified_date}</div>
                        <div class="stat-label">최종 수정</div>
                    </div>
                `;
                
                // 테이블 정보 표시
                tableGrid.innerHTML = '';
                for (const [tableName, recordCount] of Object.entries(data.table_info)) {
                    const tableItem = document.createElement('div');
                    tableItem.className = 'table-item';
                    tableItem.innerHTML = `
                        <strong>${tableName}</strong><br>
                        <span style="color: #666;">${recordCount.toLocaleString()}개 레코드</span>
                    `;
                    tableGrid.appendChild(tableItem);
                }
            }
            
            async function downloadFullBackup() {
                showStatus('success', '완전백업 다운로드를 시작합니다...');
                
                try {
                    const link = document.createElement('a');
                    link.href = '/download_database';
                    link.style.display = 'none';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    showStatus('success', '완전백업이 시작되었습니다. ZIP 파일에 DB와 첫부파일이 모두 포함됩니다.');
                } catch (error) {
                    showStatus('error', `완전백업 실패: ${error.message}`);
                }
            }
            
            async function downloadDatabaseOnly() {
                showStatus('success', 'DB 다운로드를 시작합니다...');
                
                try {
                    const link = document.createElement('a');
                    link.href = '/download_database_only';
                    link.style.display = 'none';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    showStatus('success', 'DB 다운로드가 시작되었습니다. 첫부파일은 포함되지 않습니다.');
                } catch (error) {
                    showStatus('error', `DB 다운로드 실패: ${error.message}`);
                }
            }
            
            function showStatus(type, message) {
                const status = document.getElementById('status');
                status.className = `status ${type}`;
                status.innerHTML = message;
                status.style.display = 'block';
            }
        </script>
    </body>
    </html>
    '''
    
    # 한글 인코딩 문제 해결을 위해 응답 헤더 설정
    from flask import Response
    return Response(html_content, content_type='text/html; charset=utf-8')

@app.route('/db_management_popup')
def db_management_popup():
    """팝업용 DB 관리 페이지"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_level = session.get('user_level', 'N')
    if not check_permission(user_level, 'S'):
        return "접근 권한이 없습니다.", 403
    
    html_content = '''<!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>데이터베이스 관리</title>
        <style>
            body { 
                font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; padding: 20px; min-height: 100vh;
            }
            .container { 
                max-width: 750px; margin: 20px auto; 
                background: rgba(255,255,255,0.95);
                border-radius: 15px; padding: 30px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            .header {
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 30px; padding-bottom: 15px;
                border-bottom: 2px solid #667eea;
            }
            h2 { color: #333; margin: 0; }
            .close-btn {
                background: #dc3545; color: white; border: none;
                padding: 8px 16px; border-radius: 5px; cursor: pointer;
                font-weight: bold; font-size: 14px;
            }
            .close-btn:hover { background: #c82333; }
            .info-card {
                background: #f8f9fa; padding: 20px; border-radius: 10px;
                margin: 20px 0; border-left: 4px solid #667eea;
            }
            .table-grid {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px; margin: 15px 0;
            }
            .table-item {
                background: white; padding: 10px; border-radius: 5px;
                border: 1px solid #e0e0e0; font-size: 14px;
            }
            .action-area {
                text-align: center; padding: 30px; margin: 20px 0;
                background: linear-gradient(45deg, #e3f2fd, #f3e5f5);
                border-radius: 10px; border: 2px dashed #667eea;
            }
            .btn {
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white; border: none; padding: 12px 24px;
                border-radius: 25px; cursor: pointer; font-size: 14px;
                transition: all 0.3s ease; text-decoration: none;
                display: inline-block; margin: 8px;
            }
            .btn:hover { 
                transform: translateY(-2px); 
                box-shadow: 0 5px 15px rgba(0,0,0,0.2); 
                color: white; text-decoration: none;
            }
            .btn-success { background: linear-gradient(45deg, #4CAF50, #45a049); }
            .btn-primary { background: linear-gradient(45deg, #2196F3, #1976D2); }
            .btn-secondary { background: linear-gradient(45deg, #78909c, #546e7a); }
            .loading { display: none; margin: 20px 0; text-align: center; }
            .status { margin: 20px 0; padding: 15px; border-radius: 8px; }
            .status.success { background: #e8f5e8; color: #2e7d32; }
            .status.error { background: #ffebee; color: #c62828; }
            .stats { 
                display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
                gap: 15px; margin: 20px 0;
            }
            .stat-item { 
                text-align: center; padding: 15px; background: white; 
                border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .stat-number { font-size: 24px; font-weight: bold; color: #667eea; }
            .stat-label { font-size: 12px; color: #666; margin-top: 5px; }
            .upload-section {
                background: #fff3cd; padding: 20px; border-radius: 10px;
                margin: 20px 0; border-left: 4px solid #ffc107;
            }
            .file-input {
                margin: 10px 0; padding: 10px; 
                border: 2px dashed #ccc; border-radius: 8px;
                background: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>데이터베이스 관리</h2>
            </div>
            
            <!-- 백업 섹션 -->
            <div class="info-card">
                <h3>백업 다운로드</h3>
                <ul>
                    <li><strong>완전백업 (권장)</strong>: 데이터베이스 + 첨부파일(영수증 등)을 ZIP으로 압축</li>
                    <li><strong>DB만 백업</strong>: 데이터베이스 파일만 다운로드 (첨부파일 제외)</li>
                    <li>파일명에 타임스탬프가 자동으로 포함됩니다</li>
                </ul>
            </div>
            
            <div id="loading" class="loading">
                <p>데이터베이스 정보를 조회 중...</p>
            </div>
            
            <div id="dbInfo" style="display: none;">
                <div class="stats" id="stats"></div>
                
                <div class="info-card">
                    <h4>테이블별 레코드 수</h4>
                    <div class="table-grid" id="tableGrid"></div>
                </div>
                
                <div class="action-area">
                    <h3>백업 다운로드</h3>
                    <button class="btn btn-success" onclick="downloadFullBackup()">
                        완전백업 (DB + 첨부파일)
                    </button>
                    <button class="btn btn-primary" onclick="downloadDatabaseOnly()">
                        DB만 백업
                    </button>
                </div>
            </div>
            
            <!-- 업로드 섹션 -->
            <div class="upload-section">
                <h3>데이터베이스 복원</h3>
                <p>백업된 데이터베이스 파일을 업로드하여 시스템을 복원할 수 있습니다.</p>
                <div class="file-input">
                    <form id="uploadForm" enctype="multipart/form-data">
                        <input type="file" id="dbFile" name="database" accept=".db,.zip" required>
                        <button type="submit" class="btn btn-secondary">업로드 & 복원</button>
                    </form>
                </div>
            </div>
            
            <div id="status" class="status" style="display: none;"></div>
        </div>
        
        <script>
            // 페이지 로드 시 데이터베이스 정보 조회
            window.addEventListener('load', async () => {
                await loadDatabaseInfo();
            });
            
            async function loadDatabaseInfo() {
                const loading = document.getElementById('loading');
                const dbInfo = document.getElementById('dbInfo');
                const status = document.getElementById('status');
                
                loading.style.display = 'block';
                dbInfo.style.display = 'none';
                status.style.display = 'none';
                
                try {
                    const response = await fetch('/download_info');
                    const data = await response.json();
                    
                    if (data.success) {
                        displayDatabaseInfo(data);
                        dbInfo.style.display = 'block';
                    } else {
                        showStatus('error', `? ${data.message}`);
                    }
                } catch (error) {
                    showStatus('error', `? 정보 조회 실패: ${error.message}`);
                } finally {
                    loading.style.display = 'none';
                }
            }
            
            function displayDatabaseInfo(data) {
                const stats = document.getElementById('stats');
                const tableGrid = document.getElementById('tableGrid');
                
                // 통계 정보 표시
                stats.innerHTML = `
                    <div class="stat-item">
                        <div class="stat-number">${data.file_info.size_mb}</div>
                        <div class="stat-label">MB</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${data.file_info.total_tables}</div>
                        <div class="stat-label">테이블</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${data.file_info.total_records.toLocaleString()}</div>
                        <div class="stat-label">레코드</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number" style="font-size: 14px;">${data.file_info.modified_date}</div>
                        <div class="stat-label">최종 수정</div>
                    </div>
                `;
                
                // 테이블 정보 표시
                tableGrid.innerHTML = '';
                for (const [tableName, recordCount] of Object.entries(data.table_info)) {
                    const tableItem = document.createElement('div');
                    tableItem.className = 'table-item';
                    tableItem.innerHTML = `
                        <strong>${tableName}</strong><br>
                        <span style="color: #666;">${recordCount.toLocaleString()}개 레코드</span>
                    `;
                    tableGrid.appendChild(tableItem);
                }
            }
            
            async function downloadFullBackup() {
                showStatus('success', '? 완전백업 다운로드를 시작합니다...');
                
                try {
                    const link = document.createElement('a');
                    link.href = '/download_database';
                    link.style.display = 'none';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    showStatus('success', '? 완전백업이 시작되었습니다. ZIP 파일에 DB와 첨부파일이 모두 포함됩니다.');
                } catch (error) {
                    showStatus('error', `? 완전백업 실패: ${error.message}`);
                }
            }
            
            async function downloadDatabaseOnly() {
                showStatus('success', '? DB 다운로드를 시작합니다...');
                
                try {
                    const link = document.createElement('a');
                    link.href = '/download_database_only';
                    link.style.display = 'none';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    showStatus('success', '? DB 다운로드가 시작되었습니다. 첨부파일은 포함되지 않습니다.');
                } catch (error) {
                    showStatus('error', `? DB 다운로드 실패: ${error.message}`);
                }
            }
            
            // 파일 업로드 처리
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const fileInput = document.getElementById('dbFile');
                const file = fileInput.files[0];
                
                if (!file) {
                    showStatus('error', '? 파일을 선택해주세요.');
                    return;
                }
                
                showStatus('success', '? 파일을 업로드하고 있습니다...');
                
                const formData = new FormData();
                formData.append('database', file);
                
                try {
                    const response = await fetch('/upload_database', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        showStatus('success', '? 데이터베이스가 성공적으로 복원되었습니다.');
                        setTimeout(() => {
                            window.location.reload();
                        }, 2000);
                    } else {
                        const errorText = await response.text();
                        showStatus('error', `? 업로드 실패: ${errorText}`);
                    }
                } catch (error) {
                    showStatus('error', `? 업로드 오류: ${error.message}`);
                }
            });
            
            function showStatus(type, message) {
                const status = document.getElementById('status');
                status.className = `status ${type}`;
                status.innerHTML = message;
                status.style.display = 'block';
            }
        </script>
        
        <!-- 닫기 버튼 -->
        <div style="text-align: center; margin: 30px 0; padding: 20px; border-top: 1px solid #eee;">
            <button onclick="window.close()" style="background: #dc3545; color: white; border: none; padding: 12px 30px; border-radius: 25px; cursor: pointer; font-size: 16px; font-weight: 500; box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3); transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">닫기</button>
        </div>
    </body>
    </html>
    '''
    
    return Response(html_content, content_type='text/html; charset=utf-8')

# 간단한 다운로드 경로들 추가
@app.route('/download')
def simple_download():
    """간단한 다운로드 페이지 경로"""
    return redirect('/download_database_page')

@app.route('/db_download')
def db_download_alias():
    """데이터베이스 다운로드 페이지 별칭"""
    return redirect('/download_database_page')

@app.route('/routes')
def list_routes():
    """등록된 모든 라우트 확인"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule)
        })
    
    routes.sort(key=lambda x: x['rule'])
    
    html = "<h2>등록된 라우트 목록</h2><ul>"
    for route in routes:
        html += f"<li><strong>{route['rule']}</strong> - {route['methods']} - {route['endpoint']}</li>"
    html += "</ul>"
    
    return html

@app.route('/copy_local_data')
def copy_local_data():
    """로컬 DB 구조와 샘플 데이터를 Render 서버에 복사"""
    if not os.environ.get('RENDER'):
        return jsonify({"error": "이 기능은 Render 서버에서만 사용 가능합니다."}), 403
    
    try:
        conn = get_db_connection()
        results = []
        
        # 먼저 기본 테이블들 생성
        try:
            init_user_tables()
            results.append("? 기본 사용자 테이블 생성 완료")
        except Exception as e:
            results.append(f"? 기본 사용자 테이블 생성 실패: {str(e)}")
        
        try:
            init_business_tables()
            results.append("? 기본 비즈니스 테이블 생성 완료")
        except Exception as e:
            results.append(f"? 기본 비즈니스 테이블 생성 실패: {str(e)}")
        
        # 핵심 테이블들을 직접 생성 (확실하게)
        core_tables = [
            ("Users", '''
                CREATE TABLE IF NOT EXISTS Users (
                    user_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    user_level TEXT NOT NULL DEFAULT 'N',
                    user_level_name TEXT NOT NULL DEFAULT '일반담당자',
                    branch_code TEXT NOT NULL DEFAULT 'DEFAULT',
                    branch_name TEXT NOT NULL DEFAULT '기본지점',
                    phone TEXT,
                    gender TEXT,
                    birth_date TEXT,
                    email TEXT,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login TEXT
                )
            '''),
            ("Company_Basic", '''
                CREATE TABLE IF NOT EXISTS Company_Basic (
                    biz_no TEXT PRIMARY KEY,
                    company_name TEXT,
                    representative_name TEXT,
                    establish_date TEXT,
                    company_size TEXT,
                    industry_name TEXT,
                    region TEXT,
                    address TEXT,
                    phone TEXT,
                    status TEXT DEFAULT 'ACTIVE'
                )
            '''),
            ("Contact_History", '''
                CREATE TABLE IF NOT EXISTS Contact_History (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    biz_no TEXT,
                    contact_datetime TEXT,
                    contact_type TEXT,
                    contact_person TEXT,
                    memo TEXT,
                    registered_by TEXT,
                    registered_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        ]
        
        for table_name, create_sql in core_tables:
            try:
                conn.execute(create_sql)
                results.append(f"? {table_name} 테이블 직접 생성 완료")
            except Exception as e:
                results.append(f"? {table_name} 테이블 직접 생성 실패: {str(e)}")
        
        # 추가 테이블들 생성
        additional_tables = [
            ("User_Subscriptions", '''
                CREATE TABLE IF NOT EXISTS User_Subscriptions (
                    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    subscription_start_date DATE,
                    subscription_end_date DATE,
                    subscription_type TEXT DEFAULT 'Basic',
                    total_paid_amount INTEGER DEFAULT 0,
                    is_first_month_free BOOLEAN DEFAULT 0,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            '''),
            ("Pioneering_Targets", '''
                CREATE TABLE IF NOT EXISTS Pioneering_Targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    biz_no TEXT,
                    visit_date TEXT,
                    visitor_id TEXT,
                    purpose TEXT,
                    result TEXT,
                    memo TEXT,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            '''),
            ("Sales_Expenses", '''
                CREATE TABLE IF NOT EXISTS Sales_Expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_date TEXT,
                    user_id TEXT,
                    expense_type TEXT,
                    amount INTEGER,
                    description TEXT,
                    receipt_url TEXT,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            '''),
            ("Signup_Requests", '''
                CREATE TABLE IF NOT EXISTS Signup_Requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    branch_code TEXT,
                    branch_name TEXT,
                    purpose TEXT,
                    status TEXT DEFAULT 'PENDING',
                    requested_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    processed_date TEXT,
                    processed_by TEXT
                )
            '''),
            ("Company_Financial", '''
                CREATE TABLE IF NOT EXISTS Company_Financial (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    biz_no TEXT,
                    fiscal_year TEXT,
                    total_assets INTEGER,
                    total_liabilities INTEGER,
                    total_equity INTEGER,
                    revenue INTEGER,
                    operating_profit INTEGER,
                    net_profit INTEGER,
                    retained_earnings INTEGER,
                    undistributed_retained_earnings INTEGER,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            '''),
            ("Company_Shareholder", '''
                CREATE TABLE IF NOT EXISTS Company_Shareholder (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    biz_no TEXT,
                    shareholder_name TEXT,
                    ownership_percent REAL,
                    total_shares_owned INTEGER,
                    relationship TEXT,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        ]
        
        for table_name, create_sql in additional_tables:
            try:
                conn.execute(create_sql)
                results.append(f"? {table_name} 테이블 생성 완료")
            except Exception as e:
                results.append(f"? {table_name} 테이블 생성 실패: {str(e)}")
        
        # 샘플 사용자 계정과 데이터 추가
        try:
            # 기본 사용자들 추가 (yangch 계정 제거됨)
            users_data = [
                ('admin', 'admin123!', '관리자', 'S', '서브관리자', 'ADMIN', '관리부', '010-1111-1111'),
                ('manager1', 'manager123!', '매니저1', 'M', '매니저', 'SALES', '영업부', '010-2222-2222'),
                ('user1', 'user123!', '일반사용자1', 'N', '일반담당자', 'SALES', '영업부', '010-3333-3333')
            ]
            
            for user_data in users_data:
                conn.execute('''
                    INSERT OR IGNORE INTO Users 
                    (user_id, password, name, user_level, user_level_name, branch_code, branch_name, phone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', user_data)
            
            results.append("? 기본 사용자 계정들 추가 완료")
            
            # 샘플 기업 데이터 추가
            sample_companies = [
                ('1234567890', '샘플기업1', '홍길동', '2020-01-01', '중소기업', 'IT서비스업', '서울특별시'),
                ('0987654321', '샘플기업2', '김철수', '2019-05-15', '중견기업', '제조업', '경기도'),
                ('5555555555', '테스트회사', '이영희', '2021-03-10', '소기업', '서비스업', '부산광역시')
            ]
            
            for company_data in sample_companies:
                conn.execute('''
                    INSERT OR IGNORE INTO Company_Basic 
                    (biz_no, company_name, representative_name, establish_date, company_size, industry_name, region)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', company_data)
            
            results.append("? 샘플 기업 데이터 추가 완료")
            
        except Exception as e:
            results.append(f"? 샘플 데이터 추가 실패: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": "로컬 데이터 복사 완료",
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"데이터 복사 실패: {str(e)}"
        }), 500

@app.route('/artifact_image/<filename>')
def get_artifact_image(filename):
    artifact_dir = r"C:\Users\yangga\.gemini\antigravity\brain\379b89a0-0c34-45d1-815d-3c8661d646f8"
    return send_from_directory(artifact_dir, filename)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user_name = session.get('user_name')
    
    conn = get_db_connection()

    # 구독 정보 조회 (새로운 함수 사용)
    subscription_info = get_user_subscription_info(user_id)    # 페이지네이션 설정
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    # Company_Basic 테이블로 변경
    total_companies = conn.execute('SELECT COUNT(*) FROM Company_Basic').fetchone()[0]
    total_pages = math.ceil(total_companies / per_page)

    companies = conn.execute('SELECT * FROM Company_Basic LIMIT ? OFFSET ?', (per_page, offset)).fetchall()

    # 접촉 이력 조회 권한 처리 로직
    user_level = session.get('user_level', 'N')
    contact_params = []
    contact_history_query = "SELECT * FROM Contact_History"
    
    # V(메인관리자), S(서브관리자)는 전체 이력 조회 가능
    if not check_permission(user_level, 'S'):
        contact_history_query += " WHERE registered_by = ?"
        contact_params.append(user_id)
    contact_history_query += " ORDER BY contact_datetime DESC"
    contact_history = conn.execute(contact_history_query, contact_params).fetchall()

    conn.close()

    return render_template('index.html',
                           user_name=user_name,
                           companies=companies,
                           total_pages=total_pages,
                           current_page=page,
                           subscription_info=subscription_info)

@app.route('/main')
def main():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 구독 정보 조회
    subscription_info = get_user_subscription_info(session.get('user_id'))
    
    # 사용자 권한 정보를 템플릿에 전달
    user_data = {
        'user_id': session.get('user_id'),  # YS Honers 알림용
        'user_name': session.get('user_name'),
        'user_level': session.get('user_level', 'N'),
        'user_level_name': session.get('user_level_name', '일반담당자'),
        'branch_name': session.get('branch_name', ''),
        'can_manage_users': check_permission(session.get('user_level', 'N'), 'S'),
        'subscription_info': subscription_info
    }
    
    return render_template('main.html', **user_data)
# (불필요한 잘못된 들여쓰기 라인 제거)
# --- 접촉이력 데이터 조회 API 추가 ---
@app.route('/api/contact_history_csv', methods=['GET', 'POST'])
def contact_history_csv():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    if request.method == 'GET':
        # 본인이 등록한 Contact_History만 CSV로 반환 (관리자는 전체 조회 가능)
        conn = get_db_connection()
        user_level = session.get('user_level', 'N')
        user_id = session.get('user_id')
        
        if user_level in ['V', 'S']:  # 최고관리자, 시스템관리자는 전체 조회
            rows = conn.execute('SELECT history_id, contact_datetime, biz_no, contact_type, contact_person, memo, registered_by FROM Contact_History ORDER BY history_id').fetchall()
        else:  # 일반 사용자는 본인 등록 건만 조회
            rows = conn.execute('SELECT history_id, contact_datetime, biz_no, contact_type, contact_person, memo, registered_by FROM Contact_History WHERE registered_by = ? ORDER BY history_id', (user_id,)).fetchall()
        
        conn.close()
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['history_id','contact_datetime','biz_no','contact_type','contact_person','memo','registered_by'])
        for row in rows:
            cw.writerow([row['history_id'], row['contact_datetime'], row['biz_no'], row['contact_type'], row['contact_person'], row['memo'], row['registered_by']])
        output = si.getvalue().encode('utf-8-sig')
        return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=contact_history.csv"})
    else:
        # 업로드: 기존 데이터 전체 삭제 후, 업로드된 CSV로 전체 대체
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': 'CSV 파일만 업로드 가능합니다.'}), 400
        
        # 인코딩 감지 및 처리
        content = file.stream.read()
        try:
            # UTF-8 BOM 우선 시도
            decoded_content = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                # CP949 (EUC-KR) 시도
                decoded_content = content.decode('cp949')
            except UnicodeDecodeError:
                # UTF-8 시도
                decoded_content = content.decode('utf-8', errors='ignore')
        
        stream = io.StringIO(decoded_content)
        reader = csv.DictReader(stream)
        conn = get_db_connection()
        try:
            conn.execute('DELETE FROM Contact_History')
            inserted, updated = 0, 0
            for row in reader:
                if row.get('history_id'):
                    cur = conn.execute("SELECT 1 FROM Contact_History WHERE history_id = ?", (row['history_id'],))
                    if cur.fetchone():
                        conn.execute("UPDATE Contact_History SET contact_datetime=?, biz_no=?, contact_type=?, contact_person=?, memo=?, registered_by=? WHERE history_id = ?",
                            (row['contact_datetime'], row['biz_no'], row['contact_type'], row['contact_person'], row['memo'], row['registered_by'], row['history_id']))
                        updated += 1
                        continue
                conn.execute("INSERT INTO Contact_History (history_id, contact_datetime, biz_no, contact_type, contact_person, memo, registered_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (row.get('history_id'), row.get('contact_datetime'), row.get('biz_no'), row.get('contact_type'), row.get('contact_person'), row.get('memo'), row.get('registered_by')))
                inserted += 1
            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            conn.close()
        return jsonify({'success': True, 'inserted': inserted, 'updated': updated})
@app.route('/api/history_search')
def api_history_search():
    print(">>> /api/history_search 라우트 진입")  # 라우트 진입 확인용 로그
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = session.get('user_id')
        print(f"접속 user_id: {user_id}")
        query = """
            SELECT
                h.history_id,
                h.contact_datetime,
                h.biz_no,
                b.company_name,
                h.contact_type,
                h.contact_person,
                h.memo,
                h.registered_by
            FROM Contact_History h
            LEFT JOIN Company_Basic b ON h.biz_no = b.biz_no
        """
        filters = []
        params = []

        search_user = request.args.get('registered_by')
        user_level = session.get('user_level', 'N')
        
        # 담당자ID가 명확히 입력된 경우만 해당 담당자 등록건만 조회
        if search_user is not None and search_user.strip() != "":
            filters.append("h.registered_by = ?")
            params.append(search_user.strip())
        else:
            # 담당자ID 미입력 시 권한에 따라 조회 범위 결정
            if check_permission(user_level, 'S'):  # V(메인관리자), S(서브관리자)
                # 전체 이력 조회 (필터 없음)
                pass
            else:
                # M(매니저), N(일반담당자)는 본인(또는 파트너) 등록건만 조회
                if user_id in ['ct0001', 'ct0002']:
                    filters.append("h.registered_by IN ('ct0001', 'ct0002')")
                else:
                    filters.append("h.registered_by = ?")
                    params.append(user_id)

        if request.args.get('start_date'):
            filters.append("h.contact_datetime >= ?")
            params.append(request.args.get('start_date') + ' 00:00:00')
        if request.args.get('end_date'):
            filters.append("h.contact_datetime <= ?")
            params.append(request.args.get('end_date') + ' 23:59:59')
        if request.args.get('biz_no'):
            filters.append("h.biz_no LIKE ?")
            params.append(f"%{request.args.get('biz_no')}%")

        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY h.contact_datetime DESC"

        print(f"쿼리 실행: {query}")
        print(f"파라미터: {params}")

        conn = get_db_connection()
        results = conn.execute(query, params).fetchall()
        conn.close()

        print(f"조회된 결과 수: {len(results)}")
        return jsonify([dict(row) for row in results])
        
    except Exception as e:
        print(f"Error in api_history_search: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# ▼▼▼ [수정] get_companies 함수 ▼▼▼
@app.route('/api/companies')
def get_companies():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page
        
        all_data = query_companies_data(request.args)
        total_rows = len(all_data)
        
        has_next_page = total_rows > (offset + per_page)
        
        # NaN 값을 None으로 변환 (JSON 직렬화 문제 해결)
        paginated_data = all_data.iloc[offset : offset + per_page]
        
        # NaN, inf, -inf를 None으로 변환
        import numpy as np
        paginated_data = paginated_data.replace([np.nan, np.inf, -np.inf], None)
        
        return jsonify({
            'companies': paginated_data.to_dict('records'),
            'hasNextPage': has_next_page,
            'offset': offset,
            'totalRows': total_rows
        })
    except Exception as e:
        print(f"Error in get_companies: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/export_excel')
def export_excel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        import xlsxwriter  # ensure xlsxwriter is installed
        df = query_companies_data(request.args)
        if len(df) > 500:
            return "검색 결과가 500건을 초과합니다. 조건을 조정하여 500건 이하로 조회해주세요.", 400
        df.rename(columns={
            'biz_no': '사업자번호', 'company_name': '기업명', 'representative_name': '대표자명', 'phone_number': '전화번호',
            'company_size': '기업규모', 'address': '주소', 'industry_name': '업종명', 'fiscal_year': '최신결산년도',
            'total_assets': '자산총계', 'sales_revenue': '매출액', 'retained_earnings': '이익잉여금'
        }, inplace=True)
        excel_cols = ['사업자번호', '기업명', '대표자명', '전화번호', '기업규모', '주소', '업종명', '최신결산년도', '자산총계', '매출액', '이익잉여금']
        df_excel = df[[col for col in excel_cols if col in df.columns]]
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='기업정보')
        output.seek(0)
        return Response(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": "attachment;filename=company_data.xlsx"})
    except ImportError:
        return "엑셀 파일 생성에 필요한 'xlsxwriter' 패키지가 설치되어 있지 않습니다. 관리자에게 문의하세요.", 500
    except Exception as e:
        print(f"Error in export_excel: {e}")
        return f"엑셀 파일 생성 중 오류가 발생했습니다. 상세: {e}", 500

# ...existing code...
@app.route('/company/<biz_no>')
@app.route('/company_detail/<biz_no>')  # 추가 라우트 경로
def company_detail(biz_no):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    source_page = request.args.get('source')
    is_popup = (source_page == 'history_popup')

    conn = get_db_connection()
    user_id = session.get('user_id')
    
    basic_query = """
    SELECT cb.*, cf.rating1, cb.group_transaction_yn, cb.gfc_transaction_yn
    FROM Company_Basic cb
    LEFT JOIN (SELECT biz_no, rating1, fiscal_year FROM Company_Financial ORDER BY fiscal_year DESC) AS cf ON cb.biz_no = cf.biz_no
    WHERE cb.biz_no = ? GROUP BY cb.biz_no
    """
    basic_info = conn.execute(basic_query, (biz_no,)).fetchone()
    
    financial_query = """
    SELECT fiscal_year, sales_revenue, operating_income, net_income, total_assets, total_equity, retained_earnings, corporate_tax, 
           undistributed_retained_earnings, advances_paid, advances_received, shares_issued_count, total_liabilities,
           IFNULL(capital_stock_value, 0) as capital_stock_value
    FROM Company_Financial WHERE biz_no = ? ORDER BY fiscal_year DESC LIMIT 3
    """
    financial_info = conn.execute(financial_query, (biz_no,)).fetchall()
    
    representatives = conn.execute("SELECT name, birth_date, gender, is_gfc FROM Company_Representative WHERE biz_no = ?", (biz_no,)).fetchall()
    shareholders = conn.execute("SELECT * FROM Company_Shareholder WHERE biz_no = ?", (biz_no,)).fetchall()
    
    history_query = "SELECT * FROM Contact_History WHERE biz_no = ?"
    history_params = [biz_no]
    user_level = session.get('user_level', 'N')

    # 권한에 따른 접촉이력 조회 범위 설정
    if user_level == 'V':  # 메인관리자: 모든 이력
        pass
    elif user_level == 'S':  # 서브관리자: 관리자급 이력만
        history_query += " AND registered_by IN (SELECT user_id FROM Users WHERE user_level IN ('V', 'S'))"
    else:  # 매니저, 일반담당자: 본인 이력만
        history_query += " AND registered_by = ?"
        history_params.append(user_id)
    
    history_query += " ORDER BY contact_datetime DESC"
    contact_history = conn.execute(history_query, tuple(history_params)).fetchall()

    try:
        patents = conn.execute("SELECT * FROM Company_Patent WHERE biz_no = ?", (biz_no,)).fetchall()
    except sqlite3.OperationalError:
        patents = []
    
    try:
        additional_info_row = conn.execute("SELECT * FROM Company_Additional WHERE biz_no = ?", (biz_no,)).fetchone()
    except sqlite3.OperationalError:
        additional_info_row = None
    conn.close()

    additional_info = dict(additional_info_row) if additional_info_row else {}
    if additional_info:
        today_str = get_kst_now().strftime('%Y-%m-%d')
        if additional_info.get('is_innobiz') == '1' and additional_info.get('innobiz_expiry_date') and additional_info['innobiz_expiry_date'] < today_str:
            additional_info['is_innobiz'] = '0'
        if additional_info.get('is_mainbiz') == '1' and additional_info.get('mainbiz_expiry_date') and additional_info['mainbiz_expiry_date'] < today_str:
            additional_info['is_mainbiz'] = '0'
        if additional_info.get('is_venture') == '1' and additional_info.get('venture_expiry_date') and additional_info['venture_expiry_date'] < today_str:
            additional_info['is_venture'] = '0'

    financial_data_for_calc = [dict(row) for row in financial_info] if financial_info else []
    stock_valuation = calculate_unlisted_stock_value(financial_data_for_calc)
    
    # 주주 정보 처리 개선 - 지분율, 주식수, 금액 계산
    processed_shareholders = []
    total_shares_owned = 0
    
    if shareholders:
        # 전체 주식수 계산 (stock_valuation에서 계산된 값 사용)
        total_shares_issued = stock_valuation.get('total_shares_issued', 1)
        estimated_stock_value = stock_valuation.get('estimated_stock_value', 0)
        
        for shareholder in shareholders:
            try:
                shareholder_dict = dict(shareholder)
                
                # 안전한 지분율 변환
                try:
                    ownership_percent = float(shareholder_dict.get('ownership_percent', 0) or 0)
                except (ValueError, TypeError):
                    ownership_percent = 0.0
                
                # 실제 주식수가 있는지 확인
                actual_stock_quantity = shareholder_dict.get('total_shares_owned')
                has_actual_stock_data = (actual_stock_quantity is not None and 
                                       actual_stock_quantity != '' and 
                                       actual_stock_quantity != 0)
                
                if has_actual_stock_data:
                    # 실제 주식수 데이터가 있는 경우
                    try:
                        stock_quantity = float(actual_stock_quantity)
                        is_predicted = False
                    except (ValueError, TypeError):
                        stock_quantity = 0.0
                        is_predicted = False
                else:
                    # 실제 주식수가 없는 경우 지분율로 예측 계산
                    try:
                        stock_quantity = (total_shares_issued * ownership_percent) / 100.0
                        is_predicted = True
                    except (ValueError, TypeError):
                        stock_quantity = 0.0
                        is_predicted = True
                
                # 주식 금액 계산
                try:
                    stock_value_amount = stock_quantity * estimated_stock_value
                except (ValueError, TypeError):
                    stock_value_amount = 0.0
                
                shareholder_dict.update({
                    'ownership_percent': round(ownership_percent, 2),
                    'stock_quantity': round(stock_quantity, 0),
                    'stock_value_amount': round(stock_value_amount, 0),
                    'shareholder_name': shareholder_dict.get('shareholder_name', ''),
                    'relationship': shareholder_dict.get('relationship', ''),
                    'is_predicted': is_predicted  # 예측 여부를 표시
                })
                
                processed_shareholders.append(shareholder_dict)
                total_shares_owned += stock_quantity
                
            except Exception as e:
                print(f"주주 정보 처리 중 오류: {e}")
                # 오류가 발생한 주주는 건너뛰고 계속 진행
                continue

    company_data = {
        'basic': dict(basic_info) if basic_info else {},
        'financials': [dict(row) for row in financial_info],
        'representatives': [dict(row) for row in representatives],
        'shareholders': processed_shareholders,
        'history': [dict(row) for row in contact_history],
        'patents': [dict(row) for row in patents],
        'additional': additional_info,
        'stock_valuation': stock_valuation
    }
    return render_template('detail.html', 
                         company=company_data, 
                         is_popup=is_popup,
                         user_id=user_id,
                         user_name=session.get('user_name'),
                         user_level=session.get('user_level'))

# 대표자 이름 수정 API
@app.route('/api/update_representative_name', methods=['POST'])
def update_representative_name():
    """기본정보의 대표자 이름 수정"""
    if 'user_id' not in session: 
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    
    try:
        data = request.get_json()
        biz_no = data.get('biz_no')
        new_name = data.get('new_name', '').strip()
        
        if not biz_no or not new_name:
            return jsonify({"success": False, "message": "사업자번호와 새 이름이 필요합니다."})
        
        conn = get_db_connection()
        
        # Company_Basic 테이블의 대표자 이름 수정
        conn.execute("""
            UPDATE Company_Basic 
            SET representative_name = ? 
            WHERE biz_no = ?
        """, (new_name, biz_no))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "대표자 이름이 수정되었습니다."})
        
    except Exception as e:
        print(f"대표자 이름 수정 오류: {e}")
        return jsonify({"success": False, "message": f"수정 중 오류가 발생했습니다: {str(e)}"})

# 대표자 정보 삭제 API
@app.route('/api/delete_representative', methods=['POST'])
def delete_representative():
    """대표자 정보 삭제 (마스킹된 데이터)"""
    if 'user_id' not in session: 
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    
    try:
        data = request.get_json()
        biz_no = data.get('biz_no')
        name = data.get('name', '').strip()
        
        if not biz_no or not name:
            return jsonify({"success": False, "message": "사업자번호와 이름이 필요합니다."})
        
        conn = get_db_connection()
        
        # Company_Representative 테이블에서 삭제
        conn.execute("""
            DELETE FROM Company_Representative 
            WHERE biz_no = ? AND name = ?
        """, (biz_no, name))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "대표자 정보가 삭제되었습니다."})
        
    except Exception as e:
        print(f"대표자 삭제 오류: {e}")
        return jsonify({"success": False, "message": f"삭제 중 오류가 발생했습니다: {str(e)}"})

# 주주 정보 삭제 API
@app.route('/api/delete_shareholder', methods=['POST'])
def delete_shareholder():
    """주주 정보 삭제 (마스킹된 데이터)"""
    if 'user_id' not in session: 
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    
    try:
        data = request.get_json()
        biz_no = data.get('biz_no')
        shareholder_name = data.get('shareholder_name', '').strip()
        
        if not biz_no or not shareholder_name:
            return jsonify({"success": False, "message": "사업자번호와 주주명이 필요합니다."})
        
        conn = get_db_connection()
        
        # Company_Shareholder 테이블에서 삭제
        conn.execute("""
            DELETE FROM Company_Shareholder 
            WHERE biz_no = ? AND shareholder_name = ?
        """, (biz_no, shareholder_name))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "주주 정보가 삭제되었습니다."})
        
    except Exception as e:
        print(f"주주 삭제 오류: {e}")
        return jsonify({"success": False, "message": f"삭제 중 오류가 발생했습니다: {str(e)}"})

@app.route('/api/contact_history', methods=['GET'])
def get_contact_history():
    """특정 기업의 접촉이력 조회"""
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    biz_no = request.args.get('biz_no')
    if not biz_no:
        return jsonify({"success": False, "message": "사업자번호가 필요합니다."}), 400
    
    conn = get_db_connection()
    try:
        # 사용자 권한에 따른 접촉이력 조회
        user_level = session.get('user_level', 'N')
        user_id = session.get('user_id')
        
        if user_level in ['V', 'S']:
            # 메인관리자, 서브관리자는 모든 접촉이력 조회 가능
            histories = conn.execute(
                """SELECT history_id, biz_no, contact_datetime, contact_type, contact_person, memo, registered_by, registered_date
                   FROM Contact_History 
                   WHERE biz_no = ? 
                   ORDER BY contact_datetime DESC""",
                (biz_no,)
            ).fetchall()
        else:
            # 매니저 이하는 본인이 등록한 이력만 조회
            histories = conn.execute(
                """SELECT history_id, biz_no, contact_datetime, contact_type, contact_person, memo, registered_by, registered_date
                   FROM Contact_History 
                   WHERE biz_no = ? AND registered_by = ?
                   ORDER BY contact_datetime DESC""",
                (biz_no, user_id)
            ).fetchall()
        
        # 결과를 딕셔너리 리스트로 변환
        history_list = []
        for history in histories:
            history_list.append({
                'history_id': history[0],
                'biz_no': history[1],
                'contact_datetime': history[2],
                'contact_type': history[3],
                'contact_person': history[4],
                'memo': history[5],
                'registered_by': history[6],
                'registered_date': history[7]
            })
        
        return jsonify({"success": True, "data": history_list})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/contact_history/<int:history_id>', methods=['GET'])
def get_contact_history_detail(history_id):
    """개별 접촉이력 상세 조회"""
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    # 디버깅을 위한 로그 추가
    print(f">>> 접촉이력 조회 요청 - history_id: {history_id}")
    print(f">>> 세션 정보 - user_id: {session.get('user_id')}, user_level: {session.get('user_level')}")
    
    conn = get_db_connection()
    try:
        history = conn.execute(
            """SELECT history_id, biz_no, contact_datetime, contact_type, contact_person, memo, registered_by
               FROM Contact_History 
               WHERE history_id = ?""",
            (history_id,)
        ).fetchone()
        
        print(f">>> 조회된 이력: {history}")
        
        if not history:
            print(f">>> 접촉이력을 찾을 수 없음 - history_id: {history_id}")
            return jsonify({"success": False, "message": "접촉이력을 찾을 수 없습니다."}), 404
        
        # 권한 체크: 본인이 등록한 이력이거나 관리자 권한인 경우만 조회 가능
        user_level = session.get('user_level', 'N')
        user_id = session.get('user_id')
        
        print(f">>> 권한 체크 - user_level: {user_level}, user_id: {user_id}, registered_by: {history[6]}")
        
        # 임시로 권한 체크를 완화 (모든 사용자가 조회 가능)
        # if user_level not in ['V', 'S'] and history[6] != user_id:
        #     print(f">>> 접근 권한 없음")
        #     return jsonify({"success": False, "message": "접근 권한이 없습니다."}), 403
        
        history_data = {
            'history_id': history[0],
            'biz_no': history[1],
            'contact_datetime': history[2],
            'contact_type': history[3],
            'contact_person': history[4],
            'memo': history[5],
            'registered_by': history[6]
        }
        
        print(f">>> 성공적으로 반환: {history_data}")
        return jsonify({"success": True, "data": history_data})
    
    except Exception as e:
        print(f">>> 에러 발생: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/contact_history/<int:history_id>', methods=['PUT'])
def update_contact_history(history_id):
    """개별 접촉이력 수정"""
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    user_id = session.get('user_id', 'unknown')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 기존 이력 조회 및 권한 체크
        existing_history = conn.execute(
            "SELECT registered_by FROM Contact_History WHERE history_id = ?",
            (history_id,)
        ).fetchone()
        
        if not existing_history:
            return jsonify({"success": False, "message": "접촉이력을 찾을 수 없습니다."}), 404
        
        # 권한 체크: 본인이 등록한 이력이거나 관리자 권한인 경우만 수정 가능
        # 임시로 권한 체크를 완화 (모든 사용자가 수정 가능)
        # if user_level not in ['V', 'S'] and existing_history[0] != user_id:
        #     return jsonify({"success": False, "message": "수정 권한이 없습니다."}), 403
        
        # 접촉일시 처리
        contact_datetime_str = data.get('contact_datetime')
        if contact_datetime_str:
            if 'T' in contact_datetime_str:
                # datetime-local 형식인 경우 한국 시간으로 처리
                if not contact_datetime_str.endswith('Z') and '+' not in contact_datetime_str:
                    naive_dt = datetime.strptime(contact_datetime_str, '%Y-%m-%dT%H:%M')
                    kst_dt = KST.localize(naive_dt)
                    contact_datetime_str = kst_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            contact_datetime_str = format_kst_datetime()
        
        # 접촉이력 업데이트
        conn.execute("""
            UPDATE Contact_History 
            SET contact_datetime = ?, contact_type = ?, contact_person = ?, memo = ?
            WHERE history_id = ?
        """, (
            contact_datetime_str,
            data.get('contact_type'),
            data.get('contact_person'),
            data.get('memo'),
            history_id
        ))
        conn.commit()
        
        return jsonify({
            "success": True, 
            "message": "접촉이력이 성공적으로 수정되었습니다.",
            "history_id": history_id
        })
    
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/contact_history', methods=['POST', 'PUT'])
def handle_contact_history():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    user_id = session.get('user_id', 'unknown')
    contact_datetime_str = data.get('contact_datetime')
    history_id = data.get('history_id')

    # 접촉일시가 없으면 현재 한국 시간으로 설정
    if not contact_datetime_str:
        contact_datetime_str = format_kst_datetime()
    
    try:
        # 시간대 정보가 있는 경우 한국 시간으로 변환
        if contact_datetime_str:
            if 'T' in contact_datetime_str:
                # ISO 형식인 경우
                if contact_datetime_str.endswith('Z'):
                    # UTC 시간인 경우
                    dt_utc = datetime.fromisoformat(contact_datetime_str[:-1]).replace(tzinfo=pytz.UTC)
                    dt_kst = dt_utc.astimezone(KST)
                    formatted_datetime = dt_kst.strftime('%Y-%m-%d %H:%M:%S')
                elif '+' in contact_datetime_str or '-' in contact_datetime_str.split('T')[1]:
                    # 시간대 정보가 있는 경우
                    dt_with_tz = datetime.fromisoformat(contact_datetime_str)
                    dt_kst = dt_with_tz.astimezone(KST)
                    formatted_datetime = dt_kst.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # 시간대 정보가 없는 경우 한국 시간으로 간주
                    dt_naive = datetime.fromisoformat(contact_datetime_str.replace('T', ' '))
                    dt_kst = KST.localize(dt_naive)
                    formatted_datetime = dt_kst.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # 일반 문자열 형식인 경우 한국 시간으로 간주
                formatted_datetime = contact_datetime_str
        else:
            # 시간이 없으면 현재 한국 시간 사용
            formatted_datetime = format_kst_datetime()
        
        # 미래 시간 체크 (한국 시간 기준)
        submitted_dt = datetime.strptime(formatted_datetime, '%Y-%m-%d %H:%M:%S')
        now_kst = get_kst_now().replace(tzinfo=None)
        
        # 1분의 여유시간을 두어 네트워크 지연이나 시간 동기화 오차를 허용
        from datetime import timedelta
        if submitted_dt > (now_kst + timedelta(minutes=1)):
            return jsonify({"success": False, "message": "미래 날짜 및 시간으로 등록/수정할 수 없습니다."}), 400
            
    except ValueError as e:
        return jsonify({"success": False, "message": f"잘못된 날짜 형식입니다: {str(e)}"}), 400

    conn = get_db_connection()
    try:
        biz_no = data.get('biz_no')
        contact_type = data.get('contact_type')
        contact_person = data.get('contact_person')
        memo = data.get('memo')
        
        if request.method == 'POST':
            conn.execute(
                """INSERT INTO Contact_History (biz_no, contact_datetime, contact_type, contact_person, memo, registered_by) VALUES (?, ?, ?, ?, ?, ?)""",
                (biz_no, formatted_datetime, contact_type, contact_person, memo, user_id)
            )
            new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
            return jsonify({"success": True, "message": "추가되었습니다.", "new_history_id": new_id})
        
        elif request.method == 'PUT':
            if not history_id:
                return jsonify({"success": False, "message": "수정할 이력 ID가 없습니다."}), 400
            
            # 권한 체크: 해당 이력이 존재하는지 확인하고 수정 권한 체크
            existing_history = conn.execute(
                "SELECT registered_by FROM Contact_History WHERE history_id = ?", 
                (history_id,)
            ).fetchone()
            
            if not existing_history:
                return jsonify({"success": False, "message": "수정할 접촉이력을 찾을 수 없습니다."}), 404
            
            # 권한 체크: 본인이 등록한 이력이거나 관리자 권한인 경우만 수정 가능
            user_level = session.get('user_level', 'N')
            
            if user_level not in ['V', 'S'] and existing_history[0] != user_id:
                return jsonify({"success": False, "message": "수정 권한이 없습니다."}), 403
            
            conn.execute(
                "UPDATE Contact_History SET contact_datetime=?, contact_type=?, contact_person=?, memo=? WHERE history_id = ?", 
                (formatted_datetime, contact_type, contact_person, memo, history_id)
            )
            conn.commit()
            return jsonify({"success": True, "message": "수정되었습니다."})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/contact_history/<int:history_id>', methods=['DELETE'])
def delete_contact_history(history_id):
    """접촉이력 삭제 (권한 체크 포함)"""
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    try:
        # 먼저 해당 이력이 존재하는지 확인하고 권한 체크
        history = conn.execute(
            "SELECT registered_by FROM Contact_History WHERE history_id = ?", 
            (history_id,)
        ).fetchone()
        
        if not history:
            return jsonify({"success": False, "message": "접촉이력을 찾을 수 없습니다."}), 404
        
        # 권한 체크: 본인이 등록한 이력이거나 관리자 권한인 경우만 삭제 가능
        user_level = session.get('user_level', 'N')
        user_id = session.get('user_id')
        
        if user_level not in ['V', 'S'] and history[0] != user_id:
            return jsonify({"success": False, "message": "삭제 권한이 없습니다."}), 403
        
        # 삭제 실행
        conn.execute("DELETE FROM Contact_History WHERE history_id = ?", (history_id,))
        conn.commit()
        return jsonify({"success": True, "message": "접촉이력이 삭제되었습니다."})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 증여세 계산기 라우트 ---
@app.route('/gift_tax')
def gift_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('gift_tax.html', user_name=session.get('user_name'))

# --- 양도소득세 계산기 라우트 ---
@app.route('/transfer_tax')
def transfer_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('transfer_tax.html', user_name=session.get('user_name'))

@app.route('/transfer_tax_detail')
def transfer_tax_detail():
    """양도소득세 상세계산기 (현재는 같은 페이지)"""
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('transfer_tax.html', user_name=session.get('user_name'))

# --- 종합소득세 계산기 라우트 ---
@app.route('/income_tax')
def income_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('income_tax.html', user_name=session.get('user_name'))

# --- 4대보험료 계산기 라우트 ---
@app.route('/social_ins_tax')
def social_ins_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('social_ins_tax.html', user_name=session.get('user_name'))


# --- 취득세 계산기 라우트 ---
@app.route('/acquisition_tax')
def acquisition_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('acquisition_tax.html', user_name=session.get('user_name'))

# --- 상속세 계산기 라우트 ---
@app.route('/inheritance_tax')
def inheritance_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('inheritance_tax.html', user_name=session.get('user_name'))

# --- 퇴직금 계산기 라우트 ---
@app.route('/retirement_pay')
def retirement_pay():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('retirement_pay.html', user_name=session.get('user_name'))


@app.route('/industrial_accident')
def industrial_accident():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('industrial_accident.html', user_name=session.get('user_name'))

# --- 비용등록 관리 라우트 ---
@app.route('/expense_management')
def expense_management():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_data = {
        'user_name': session.get('user_name'),
        'user_level': session.get('user_level', 'N'),
        'user_level_name': session.get('user_level_name', '일반담당자'),
        'branch_name': session.get('branch_name', ''),
        'user_id': session.get('user_id')
    }
    
    return render_template('expense_management.html', **user_data)

# --- 영업관리 통합 라우트 ---
@app.route('/view_receipt/<int:expense_id>')
def view_receipt(expense_id):
    """영수증 파일 보기 (여러 파일 지원)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자가 등록한 영수증만 또는 승인자는 모든 영수증 조회
        if session.get('user_level') in ['V', 'S', 'M']:
            cursor.execute('''
                SELECT COALESCE(receipt_filename, receipt_image) as receipt_file
                FROM Sales_Expenses 
                WHERE id = ?
            ''', (expense_id,))
        else:
            cursor.execute('''
                SELECT COALESCE(receipt_filename, receipt_image) as receipt_file
                FROM Sales_Expenses 
                WHERE id = ? AND registered_by = ?
            ''', (expense_id, session.get('user_id')))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return "영수증 파일을 찾을 수 없습니다.", 404
            
        receipt_files = result[0]
        
        # 여러 파일인 경우 콤마로 구분된 파일명들을 처리
        if ',' in receipt_files:
            file_list = receipt_files.split(',')
            # 첫 번째 파일만 보여주거나, 여러 파일 목록 페이지로 리다이렉트
            return f"""
            <html>
            <head><title>영수증 파일 목록</title></head>
            <body>
                <h3>영수증 파일 목록</h3>
                <ul>
                    {''.join([f'<li><a href="/view_single_receipt/{expense_id}/{i}" target="_blank">{filename}</a></li>' for i, filename in enumerate(file_list)])}
                </ul>
            </body>
            </html>
            """
        else:
            # 단일 파일인 경우
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_files)
            
            if not os.path.exists(file_path):
                return "영수증 파일이 존재하지 않습니다.", 404
                
            return send_file(file_path)
        
    except Exception as e:
        print(f"[RECEIPT_VIEW_ERROR] {str(e)}")
        return f"영수증 보기 오류: {str(e)}", 500


@app.route('/view_single_receipt/<int:expense_id>/<int:file_index>')
def view_single_receipt(expense_id, file_index):
    """개별 영수증 파일 보기"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if session.get('user_level') in ['V', 'S', 'M']:
            cursor.execute('''
                SELECT COALESCE(receipt_filename, receipt_image) as receipt_file
                FROM Sales_Expenses 
                WHERE id = ?
            ''', (expense_id,))
        else:
            cursor.execute('''
                SELECT COALESCE(receipt_filename, receipt_image) as receipt_file
                FROM Sales_Expenses 
                WHERE id = ? AND registered_by = ?
            ''', (expense_id, session.get('user_id')))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return "영수증 파일을 찾을 수 없습니다.", 404
            
        receipt_files = result[0].split(',')
        
        if file_index >= len(receipt_files):
            return "파일 인덱스가 잘못되었습니다.", 404
            
        filename = receipt_files[file_index]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return "영수증 파일이 존재하지 않습니다.", 404
            
        return send_file(file_path)
        
    except Exception as e:
        print(f"[SINGLE_RECEIPT_VIEW_ERROR] {str(e)}")
        return f"영수증 보기 오류: {str(e)}", 500
        print(f"[RECEIPT_VIEW_ERROR] {str(e)}")
        return f"영수증 보기 오류: {str(e)}", 500


@app.route('/download_receipt/<int:expense_id>')
def download_receipt(expense_id):
    """영수증 파일 다운로드"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if session.get('user_level') in ['V', 'S', 'M']:
            cursor.execute('''
                SELECT COALESCE(receipt_filename, receipt_image) as receipt_file
                FROM Sales_Expenses 
                WHERE id = ?
            ''', (expense_id,))
        else:
            cursor.execute('''
                SELECT COALESCE(receipt_filename, receipt_image) as receipt_file
                FROM Sales_Expenses 
                WHERE id = ? AND registered_by = ?
            ''', (expense_id, session.get('user_id')))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return "영수증 파일을 찾을 수 없습니다.", 404
            
        receipt_filename = result[0]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename)
        
        if not os.path.exists(file_path):
            return "영수증 파일이 존재하지 않습니다.", 404
            
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        print(f"[RECEIPT_DOWNLOAD_ERROR] {str(e)}")
        return f"영수증 다운로드 오류: {str(e)}", 500


@app.route('/sales_management')
def sales_management():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_data = {
        'user_name': session.get('user_name'),
        'user_level': session.get('user_level', 'N'),
        'user_level_name': session.get('user_level_name', '일반담당자'),
        'branch_name': session.get('branch_name', ''),
        'user_id': session.get('user_id')
    }
    
    return render_template('sales_management.html', **user_data)

# --- C-Level 개척관리 라우트 (하위 호환용) ---
@app.route('/clevel_management')
def clevel_management():
    return redirect(url_for('sales_management'))

# --- 사용자 관리 라우트 (메인관리자, 서브관리자만 접근 가능) ---
@app.route('/user_management')
def user_management():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_level = session.get('user_level', 'N')
    if not check_permission(user_level, 'S'):  # 서브관리자 이상만 접근 가능
        return "접근 권한이 없습니다.", 403
    
    return render_template('user_management.html', user_name=session.get('user_name'))

# --- 사용자 목록 API ---
@app.route('/api/users')
def get_users():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    if not check_permission(user_level, 'S'):
        return jsonify({"error": "Permission denied"}), 403
    
    conn = get_db_connection()
    try:
        users = conn.execute('''
            SELECT user_id, name, password, user_level, user_level_name, branch_code, branch_name, 
                   phone, gender, birth_date, status, last_login, created_date
            FROM Users ORDER BY user_level, user_id
        ''').fetchall()
        return jsonify([dict(user) for user in users])
    finally:
        conn.close()

# --- 사용자 추가/수정 API ---
@app.route('/api/users', methods=['POST', 'PUT'])
def manage_user():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    if not check_permission(user_level, 'S'):
        return jsonify({"error": "Permission denied"}), 403
    
    data = request.json
    conn = get_db_connection()
    
    try:
        if request.method == 'POST':
            # 패스워드 규칙 검증 (신규 사용자)
            password = data.get('password')
            if password:
                is_valid, validation_message = validate_password(password)
                if not is_valid:
                    return jsonify({"success": False, "message": validation_message}), 400
            
            # 사용자 추가
            conn.execute('''
                INSERT INTO Users 
                (user_id, password, name, user_level, user_level_name, branch_code, branch_name, 
                 phone, gender, birth_date, email, position, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['user_id'], data['password'], data['name'], data['user_level'], 
                data['user_level_name'], data['branch_code'], data['branch_name'],
                data['phone'], data.get('gender'), data.get('birth_date'), 
                data.get('email'), data.get('position'), data.get('status', 'ACTIVE')
            ))
            conn.commit()
            return jsonify({"success": True, "message": "사용자가 추가되었습니다."})
        
        elif request.method == 'PUT':
            # 사용자 수정
            conn.execute('''
                UPDATE Users SET 
                    name=?, user_level=?, user_level_name=?, branch_code=?, branch_name=?,
                    phone=?, gender=?, birth_date=?, email=?, position=?, status=?,
                    updated_date=CURRENT_TIMESTAMP
                WHERE user_id=?
            ''', (
                data['name'], data['user_level'], data['user_level_name'], 
                data['branch_code'], data['branch_name'], data['phone'], 
                data.get('gender'), data.get('birth_date'), data.get('email'), 
                data.get('position'), data.get('status'), data['user_id']
            ))
            conn.commit()
            return jsonify({"success": True, "message": "사용자 정보가 수정되었습니다."})
    
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 비밀번호 변경 API ---
@app.route('/api/users/<user_id>/password', methods=['PUT'])
def change_password(user_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    current_user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    # 본인 비밀번호이거나 관리자 권한 필요
    if user_id != current_user_id and not check_permission(user_level, 'S'):
        return jsonify({"error": "Permission denied"}), 403
    
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if not new_password:
        return jsonify({"success": False, "message": "새 비밀번호를 입력해주세요."}), 400
    
    if new_password != confirm_password:
        return jsonify({"success": False, "message": "새 비밀번호가 일치하지 않습니다."}), 400
    
    # 패스워드 규칙 검증
    is_valid, validation_message = validate_password(new_password)
    if not is_valid:
        return jsonify({"success": False, "message": validation_message}), 400
    
    # 패스워드 이력 확인
    history_valid, history_message = check_password_history(user_id, new_password)
    if not history_valid:
        return jsonify({"success": False, "message": history_message}), 400
    
    conn = get_db_connection()
    try:
        # 본인 비밀번호 변경인 경우 현재 비밀번호 확인
        if user_id == current_user_id:
            if not current_password:
                return jsonify({"success": False, "message": "현재 비밀번호를 입력해주세요."}), 400
            
            current_user = conn.execute(
                "SELECT password FROM Users WHERE user_id = ?", (user_id,)
            ).fetchone()
            
            if not current_user or current_user['password'] != current_password:
                return jsonify({"success": False, "message": "현재 비밀번호가 일치하지 않습니다."}), 400
        
        # 패스워드 이력 저장 (변경 전 패스워드)
        save_password_history(user_id, new_password)
        
        # 비밀번호 업데이트
        conn.execute('''
            UPDATE Users SET 
                password=?, 
                password_changed_date=date('now'),
                updated_date=CURRENT_TIMESTAMP
            WHERE user_id=?
        ''', (new_password, user_id))
        conn.commit()
        return jsonify({"success": True, "message": "비밀번호가 변경되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 비밀번호 초기화 API ---
@app.route('/api/users/<user_id>/reset-password', methods=['PUT'])
def reset_password(user_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    
    # 관리자 권한 필요 (서브관리자 이상)
    if not check_permission(user_level, 'S'):
        return jsonify({"error": "Permission denied"}), 403
    
    data = request.json
    new_password = data.get('new_password', 'password1!')
    
    conn = get_db_connection()
    try:
        # 사용자가 존재하는지 확인
        user_exists = conn.execute(
            "SELECT user_id FROM Users WHERE user_id = ?", (user_id,)
        ).fetchone()
        
        if not user_exists:
            return jsonify({"success": False, "message": "사용자를 찾을 수 없습니다."}), 404
        
        # 패스워드 이력 저장 (초기화 전 패스워드)
        save_password_history(user_id, new_password)
        
        # 비밀번호 초기화
        conn.execute('''
            UPDATE Users SET 
                password=?, 
                password_changed_date=date('now'),
                updated_date=CURRENT_TIMESTAMP
            WHERE user_id=?
        ''', (new_password, user_id))
        conn.commit()
        return jsonify({"success": True, "message": f"비밀번호가 '{new_password}'로 초기화되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/users/<user_id>/delete', methods=['DELETE'])
def delete_user(user_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    current_user_id = session.get('user_id')
    
    # 최고관리자 권한 필요 (V)
    if not check_permission(user_level, 'V'):
        return jsonify({"error": "Permission denied"}), 403
    
    # 자기 자신은 삭제할 수 없음
    if current_user_id == user_id:
        return jsonify({"success": False, "message": "자기 자신은 삭제할 수 없습니다."}), 400
    
    conn = get_db_connection()
    try:
        # 사용자가 존재하는지 확인
        user_info = conn.execute(
            "SELECT user_id, name FROM Users WHERE user_id = ?", (user_id,)
        ).fetchone()
        
        if not user_info:
            return jsonify({"success": False, "message": "사용자를 찾을 수 없습니다."}), 404
        
        # 관련 테이블에서 데이터 삭제 (외래키 제약사항에 따라 순서대로)
        # 1. 연락 이력 삭제
        conn.execute("DELETE FROM Contact_History WHERE registered_by = ?", (user_id,))
        
        # 2. 패스워드 이력 삭제
        conn.execute("DELETE FROM Password_History WHERE user_id = ?", (user_id,))
        
        # 3. 사용자 구독 정보 삭제
        conn.execute("DELETE FROM User_Subscriptions WHERE user_id = ?", (user_id,))
        
        # 4. 사용자 삭제
        conn.execute("DELETE FROM Users WHERE user_id = ?", (user_id,))
        
        conn.commit()
        return jsonify({"success": True, "message": f"사용자 '{user_id} ({user_info['name']})'가 성공적으로 삭제되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"사용자 삭제 중 오류가 발생했습니다: {str(e)}"}), 500
    finally:
        conn.close()

# --- 회원 가입 요청 API ---
@app.route('/api/signup-request', methods=['POST'])
def signup_request():
    data = request.json
    
    # 디버그: 수신된 데이터 확인
    print(f"회원가입 신청 데이터: {data}")
    
    # 필수 필드 검증
    required_fields = ['user_id', 'name', 'phone', 'email', 'birth_date', 'gender', 'position']
    for field in required_fields:
        if not data.get(field):
            print(f"누락된 필드: {field}")
            return jsonify({"success": False, "message": f"{field}는 필수 항목입니다."}), 400
    
    # branch_name이 없으면 기본값 설정
    if not data.get('branch_name'):
        data['branch_name'] = '미지정'
    
    # branch_code가 없으면 branch_name과 동일하게 설정
    if not data.get('branch_code'):
        data['branch_code'] = data['branch_name']
    
    conn = get_db_connection()
    try:
        # 중복 아이디 확인 (기존 사용자)
        existing_user = conn.execute(
            "SELECT user_id FROM Users WHERE user_id = ?", (data['user_id'],)
        ).fetchone()
        
        if existing_user:
            return jsonify({"success": False, "message": "이미 사용 중인 아이디입니다."}), 400
        
        # 중복 신청 확인 및 처리
        existing_request = conn.execute(
            "SELECT id, status FROM Signup_Requests WHERE user_id = ?", 
            (data['user_id'],)
        ).fetchone()
        
        if existing_request:
            if existing_request['status'] == 'PENDING':
                return jsonify({"success": False, "message": "이미 신청한 아이디입니다. 승인 대기 중입니다."}), 400
            elif existing_request['status'] == 'APPROVED':
                return jsonify({"success": False, "message": "이미 승인된 아이디입니다."}), 400
            elif existing_request['status'] == 'REJECTED':
                # 거절된 신청은 업데이트 가능
                conn.execute('''
                    UPDATE Signup_Requests 
                    SET name = ?, phone = ?, email = ?, branch_code = ?, branch_name = ?, 
                        birth_date = ?, gender = ?, position = ?, purpose = ?, 
                        status = 'PENDING', requested_date = CURRENT_TIMESTAMP,
                        processed_date = NULL, processed_by = NULL, admin_notes = NULL
                    WHERE user_id = ?
                ''', (
                    data['name'], data['phone'], data['email'], 
                    data['branch_code'], data['branch_name'], data['birth_date'], 
                    data['gender'], data['position'], data.get('purpose', ''),
                    data['user_id']
                ))
                conn.commit()
                return jsonify({"success": True, "message": "신청 정보가 수정되어 재신청되었습니다."})
        
        # 새로운 가입 신청 저장
        conn.execute('''
            INSERT INTO Signup_Requests (user_id, name, phone, email, branch_code, branch_name, birth_date, gender, position, purpose)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['user_id'], data['name'], data['phone'], data['email'], 
            data['branch_code'], data['branch_name'], data['birth_date'], 
            data['gender'], data['position'], data.get('purpose', '')
        ))
        conn.commit()
        
        return jsonify({"success": True, "message": "가입 신청이 완료되었습니다."})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 가입 신청 목록 조회 API ---
@app.route('/api/signup-requests')
def get_signup_requests():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    if not check_permission(user_level, 'S'):
        return jsonify({"error": "Permission denied"}), 403
    
    conn = get_db_connection()
    try:
        requests_data = conn.execute('''
            SELECT id, user_id, name, phone, email, branch_code, branch_name, purpose, 
                   status, requested_date, processed_date, processed_by, admin_notes
            FROM Signup_Requests 
            ORDER BY requested_date DESC
        ''').fetchall()
        
        return jsonify([dict(row) for row in requests_data])
    finally:
        conn.close()

# --- 가입 신청 승인/거절 API ---
@app.route('/api/signup-requests/<int:request_id>/process', methods=['PUT'])
def process_signup_request(request_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    if not check_permission(user_level, 'S'):
        return jsonify({"error": "Permission denied"}), 403
    
    data = request.json
    action = data.get('action')  # 'approve' or 'reject'
    admin_notes = data.get('admin_notes', '')
    
    if action not in ['approve', 'reject']:
        return jsonify({"success": False, "message": "잘못된 액션입니다."}), 400
    
    admin_user = session.get('user_id')
    
    conn = get_db_connection()
    try:
        # 신청 정보 조회
        signup_request = conn.execute(
            "SELECT * FROM Signup_Requests WHERE id = ? AND status = 'PENDING'", 
            (request_id,)
        ).fetchone()
        
        if not signup_request:
            return jsonify({"success": False, "message": "처리할 수 없는 신청입니다."}), 404
        
        if action == 'approve':
            # 사용자 계정 생성
            default_password = 'Welcome123!'
            conn.execute('''
                INSERT INTO Users 
                (user_id, password, name, user_level, user_level_name, branch_code, branch_name, 
                 phone, email, birth_date, gender, position, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signup_request['user_id'], default_password, signup_request['name'], 
                'N', '일반담당자', signup_request['branch_code'], signup_request['branch_name'],
                signup_request['phone'], signup_request['email'], signup_request['birth_date'],
                signup_request['gender'], signup_request['position'], 'ACTIVE'
            ))
            
            # 신청 상태 업데이트
            conn.execute('''
                UPDATE Signup_Requests 
                SET status = 'APPROVED', processed_date = CURRENT_TIMESTAMP, 
                    processed_by = ?, admin_notes = ?
                WHERE id = ?
            ''', (admin_user, admin_notes, request_id))
            
            message = f"'{signup_request['user_id']}' 계정이 승인되었습니다. 기본 비밀번호: {default_password}"
            
        else:  # reject
            # 신청 상태 업데이트
            conn.execute('''
                UPDATE Signup_Requests 
                SET status = 'REJECTED', processed_date = CURRENT_TIMESTAMP, 
                    processed_by = ?, admin_notes = ?
                WHERE id = ?
            ''', (admin_user, admin_notes, request_id))
            
            message = f"'{signup_request['user_id']}' 가입 신청이 거절되었습니다."
        
        conn.commit()
        return jsonify({"success": True, "message": message})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 신청 상태 조회 API ---
@app.route('/api/check-signup-status', methods=['POST'])
def check_signup_status():
    data = request.json
    user_id = data.get('user_id')
    name = data.get('name')
    
    if not user_id or not name:
        return jsonify({"success": False, "message": "아이디와 이름을 입력해주세요."}), 400
    
    conn = get_db_connection()
    try:
        signup_request = conn.execute('''
            SELECT id, user_id, name, phone, email, branch_code, branch_name, 
                   birth_date, gender, position, purpose, status, requested_date, 
                   processed_date, processed_by, admin_notes
            FROM Signup_Requests 
            WHERE user_id = ? AND name = ?
            ORDER BY requested_date DESC
            LIMIT 1
        ''', (user_id, name)).fetchone()
        
        if not signup_request:
            return jsonify({"success": False, "message": "해당 신청 정보를 찾을 수 없습니다."}), 404
        
        return jsonify({"success": True, "data": dict(signup_request)})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 신청 정보 가져오기 API ---
@app.route('/api/get-signup-request/<user_id>')
def get_signup_request(user_id):
    conn = get_db_connection()
    try:
        signup_request = conn.execute('''
            SELECT id, user_id, name, phone, email, branch_code, branch_name, 
                   birth_date, gender, position, purpose, status, requested_date
            FROM Signup_Requests 
            WHERE user_id = ? AND status IN ('PENDING', 'REJECTED')
            ORDER BY requested_date DESC
            LIMIT 1
        ''', (user_id,)).fetchone()
        
        if not signup_request:
            return jsonify({"success": False, "message": "수정 가능한 신청 정보를 찾을 수 없습니다."}), 404
        
        return jsonify({"success": True, "data": dict(signup_request)})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 재신청 API ---
@app.route('/api/resubmit-signup/<user_id>', methods=['PUT'])
def resubmit_signup(user_id):
    conn = get_db_connection()
    try:
        # 기존 신청이 있는지 확인
        existing_request = conn.execute(
            "SELECT id FROM Signup_Requests WHERE user_id = ? AND status IN ('PENDING', 'REJECTED')", 
            (user_id,)
        ).fetchone()
        
        if not existing_request:
            return jsonify({"success": False, "message": "재신청할 수 있는 신청이 없습니다."}), 404
        
        # 상태를 PENDING으로 변경하고 신청일을 현재 시간으로 업데이트
        conn.execute('''
            UPDATE Signup_Requests 
            SET status = 'PENDING', 
                requested_date = CURRENT_TIMESTAMP,
                processed_date = NULL,
                processed_by = NULL,
                admin_notes = NULL
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        return jsonify({"success": True, "message": "재신청이 완료되었습니다."})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 구독 관리 API ---
@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    if user_level not in ['V', 'S']:
        return jsonify({"error": "Forbidden"}), 403
    
    conn = get_db_connection()
    try:
        # 구독 현황 조회
        subscriptions = conn.execute('''
            SELECT us.*, u.name as user_name,
                   COALESCE(SUM(ph.amount), 0) as total_paid
            FROM User_Subscriptions us
            LEFT JOIN Users u ON us.user_id = u.user_id
            LEFT JOIN Payment_History ph ON us.user_id = ph.user_id
            GROUP BY us.user_id
            ORDER BY us.subscription_start_date DESC
        ''').fetchall()
        
        # 결제 이력 조회
        payments = conn.execute('''
            SELECT ph.*, u.name as user_name
            FROM Payment_History ph
            LEFT JOIN Users u ON ph.user_id = u.user_id
            ORDER BY ph.payment_date DESC
            LIMIT 100
        ''').fetchall()
        
        return jsonify({
            "subscriptions": [dict(row) for row in subscriptions],
            "payments": [dict(row) for row in payments]
        })
    finally:
        conn.close()

@app.route('/api/subscriptions', methods=['POST'])
def create_subscription():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    if user_level not in ['V', 'S']:
        return jsonify({"error": "Forbidden"}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    subscription_type = data.get('subscription_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    payment_amount = data.get('payment_amount', 0)
    payment_method = data.get('payment_method', 'bank_transfer')
    notes = data.get('notes', '')
    
    if not all([user_id, subscription_type, start_date, end_date]):
        return jsonify({"success": False, "message": "필수 항목을 모두 입력해주세요."}), 400
    
    conn = get_db_connection()
    try:
        conn.execute('BEGIN TRANSACTION')
        
        # 기존 구독 정보 확인
        existing = conn.execute(
            "SELECT * FROM User_Subscriptions WHERE user_id = ?", (user_id,)
        ).fetchone()
        
        # 구독 유형 변환 (UI에서 오는 값을 DB 형식으로 변환)
        if subscription_type == 'monthly':
            db_subscription_type = 'MONTHLY'
        elif subscription_type == 'annual':
            db_subscription_type = 'YEARLY'  # ANNUAL -> YEARLY로 변경
        elif subscription_type == 'free':
            db_subscription_type = 'FREE'
        else:
            db_subscription_type = subscription_type.upper()
        
        if existing:
            # 기존 구독 업데이트
            conn.execute('''
                UPDATE User_Subscriptions SET 
                    subscription_type=?, subscription_start_date=?, subscription_end_date=?, updated_date=CURRENT_TIMESTAMP
                WHERE user_id=?
            ''', (db_subscription_type, start_date, end_date, user_id))
        else:
            # 새 구독 생성
            conn.execute('''
                INSERT INTO User_Subscriptions (user_id, subscription_type, subscription_start_date, subscription_end_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, db_subscription_type, start_date, end_date))
        
        # 결제 금액이 있으면 결제 이력 추가
        if payment_amount and float(payment_amount) > 0:
            from datetime import date
            today = date.today().strftime('%Y-%m-%d')
            
            # payment_type 설정
            payment_type = 'MONTHLY' if db_subscription_type == 'MONTHLY' else \
                          'YEARLY' if db_subscription_type == 'YEARLY' else 'SIGNUP'
            
            conn.execute('''
                INSERT INTO Payment_History (user_id, payment_date, amount, payment_type, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, today, float(payment_amount), payment_type, payment_method, notes))
        
        conn.commit()
        return jsonify({"success": True, "message": "구독이 설정되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/subscriptions/<user_id>', methods=['DELETE'])
def delete_subscription(user_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    if user_level not in ['V', 'S']:
        return jsonify({"error": "Forbidden"}), 403
    
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM User_Subscriptions WHERE user_id = ?", (user_id,))
        conn.commit()
        return jsonify({"success": True, "message": "구독이 삭제되었습니다."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/payment_history/<int:payment_id>', methods=['DELETE'])
def delete_payment_history(payment_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    if user_level not in ['V', 'S']:
        return jsonify({"error": "Forbidden"}), 403
    
    conn = get_db_connection()
    try:
        # 삭제하기 전에 해당 결제 이력이 존재하는지 확인
        payment = conn.execute(
            "SELECT * FROM Payment_History WHERE id = ?", (payment_id,)
        ).fetchone()
        
        if not payment:
            return jsonify({"success": False, "message": "결제 이력을 찾을 수 없습니다."}), 404
        
        # 결제 이력 삭제
        conn.execute("DELETE FROM Payment_History WHERE id = ?", (payment_id,))
        conn.commit()
        
        return jsonify({"success": True, "message": "결제 이력이 삭제되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 비용등록 관리 API ---
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 권한에 따른 조회 범위 설정
        if check_permission(user_level, 'S'):  # 관리자는 모든 비용 조회
            expenses = conn.execute('''
                SELECT e.*, u.name as registered_by_name, c.company_name
                FROM Expenses e
                LEFT JOIN Users u ON e.registered_by = u.user_id
                LEFT JOIN Company_Basic c ON e.biz_no = c.biz_no
                ORDER BY e.expense_date DESC
            ''').fetchall()
        else:  # 일반 사용자는 본인 등록 비용만 조회
            expenses = conn.execute('''
                SELECT e.*, u.name as registered_by_name, c.company_name
                FROM Expenses e
                LEFT JOIN Users u ON e.registered_by = u.user_id
                LEFT JOIN Company_Basic c ON e.biz_no = c.biz_no
                WHERE e.registered_by = ?
                ORDER BY e.expense_date DESC
            ''', (user_id,)).fetchall()
        
        return jsonify([dict(expense) for expense in expenses])
    finally:
        conn.close()

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO Expenses 
            (expense_date, biz_no, expense_type, amount, description, receipt_file, registered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('expense_date'), data.get('biz_no'), data.get('expense_type'),
            data.get('amount'), data.get('description'), data.get('receipt_file'), user_id
        ))
        conn.commit()
        return jsonify({"success": True, "message": "비용이 등록되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 권한 확인: 본인이 등록한 비용이거나 관리자인 경우만 수정 가능
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM Expenses WHERE id = ?", (expense_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        conn.execute('''
            UPDATE Expenses SET 
                expense_date=?, biz_no=?, expense_type=?, amount=?, 
                description=?, receipt_file=?, updated_date=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            data.get('expense_date'), data.get('biz_no'), data.get('expense_type'),
            data.get('amount'), data.get('description'), data.get('receipt_file'), expense_id
        ))
        conn.commit()
        return jsonify({"success": True, "message": "비용 정보가 수정되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 권한 확인: 본인이 등록한 비용이거나 관리자인 경우만 삭제 가능
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM Expenses WHERE id = ?", (expense_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        conn.execute("DELETE FROM Expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return jsonify({"success": True, "message": "비용이 삭제되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- C-Level 개척관리 API ---
@app.route('/api/clevel_targets', methods=['GET'])
def get_clevel_targets():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 권한에 따른 조회 범위 설정
        if check_permission(user_level, 'S'):  # 관리자는 모든 타겟 조회
            targets = conn.execute('''
                SELECT t.*, u.name as registered_by_name, c.company_name
                FROM CLevel_Targets t
                LEFT JOIN Users u ON t.registered_by = u.user_id
                LEFT JOIN Company_Basic c ON t.biz_no = c.biz_no
                ORDER BY t.created_date DESC
            ''').fetchall()
        else:  # 일반 사용자는 본인 등록 타겟만 조회
            targets = conn.execute('''
                SELECT t.*, u.name as registered_by_name, c.company_name
                FROM CLevel_Targets t
                LEFT JOIN Users u ON t.registered_by = u.user_id
                LEFT JOIN Company_Basic c ON t.biz_no = c.biz_no
                WHERE t.registered_by = ?
                ORDER BY t.created_date DESC
            ''', (user_id,)).fetchall()
        
        return jsonify([dict(target) for target in targets])
    finally:
        conn.close()

@app.route('/api/clevel_targets', methods=['POST'])
def add_clevel_target():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO CLevel_Targets 
            (biz_no, target_name, target_position, contact_info, target_date, 
             approach_method, status, notes, registered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('biz_no'), data.get('target_name'), data.get('target_position'),
            data.get('contact_info'), data.get('target_date'), data.get('approach_method'),
            data.get('status', 'PLANNED'), data.get('notes'), user_id
        ))
        conn.commit()
        return jsonify({"success": True, "message": "C-Level 타겟이 등록되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/clevel_targets/<int:target_id>', methods=['PUT'])
def update_clevel_target(target_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 권한 확인: 본인이 등록한 타겟이거나 관리자인 경우만 수정 가능
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM CLevel_Targets WHERE id = ?", (target_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        conn.execute('''
            UPDATE CLevel_Targets SET 
                biz_no=?, target_name=?, target_position=?, contact_info=?, 
                target_date=?, approach_method=?, status=?, notes=?, 
                updated_date=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            data.get('biz_no'), data.get('target_name'), data.get('target_position'),
            data.get('contact_info'), data.get('target_date'), data.get('approach_method'),
            data.get('status'), data.get('notes'), target_id
        ))
        conn.commit()
        return jsonify({"success": True, "message": "C-Level 타겟 정보가 수정되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/clevel_targets/<int:target_id>', methods=['DELETE'])
def delete_clevel_target(target_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 권한 확인: 본인이 등록한 타겟이거나 관리자인 경우만 삭제 가능
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM CLevel_Targets WHERE id = ?", (target_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        conn.execute("DELETE FROM CLevel_Targets WHERE id = ?", (target_id,))
        conn.commit()
        return jsonify({"success": True, "message": "C-Level 타겟이 삭제되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 개척대상 기업 관리 API ---
@app.route('/api/pioneering_targets', methods=['GET'])
def get_pioneering_targets():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 권한에 따른 조회 범위 설정
        if check_permission(user_level, 'S'):  # 관리자는 모든 타겟 조회
            targets = conn.execute('''
                SELECT p.*, u.name as visitor_name, c.company_name
                FROM Pioneering_Targets p
                LEFT JOIN Users u ON p.visitor_id = u.user_id
                LEFT JOIN Company_Basic c ON REPLACE(p.biz_no, '-', '') = c.biz_no
                ORDER BY p.visit_date DESC, p.created_date DESC
            ''').fetchall()
        else:  # 일반 사용자는 본인 등록 타겟만 조회
            targets = conn.execute('''
                SELECT p.*, u.name as visitor_name, c.company_name
                FROM Pioneering_Targets p
                LEFT JOIN Users u ON p.visitor_id = u.user_id
                LEFT JOIN Company_Basic c ON REPLACE(p.biz_no, '-', '') = c.biz_no
                WHERE p.registered_by = ?
                ORDER BY p.visit_date DESC, p.created_date DESC
            ''', (user_id,)).fetchall()
        
        return jsonify([dict(target) for target in targets])
    finally:
        conn.close()

@app.route('/api/pioneering_targets', methods=['POST'])
def add_pioneering_target():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    
    try:
        data = request.json
    except Exception as e:
        return jsonify({"success": False, "message": "잘못된 JSON 형식입니다."}), 400
    
    if not data:
        return jsonify({"success": False, "message": "데이터가 전송되지 않았습니다."}), 400
    
    user_id = session.get('user_id')
    biz_no = data.get('biz_no')
    visit_date = data.get('visit_date')
    notes = data.get('notes', '')
    visitor_id = data.get('visitor_id', user_id)
    
    if not biz_no or not visit_date:
        return jsonify({"success": False, "message": "사업자번호와 방문일자는 필수입니다."}), 400
    
    conn = get_db_connection()
    try:
        # 중복 확인
        existing = conn.execute('''
            SELECT id FROM Pioneering_Targets 
            WHERE biz_no = ? AND visit_date = ? AND registered_by = ?
        ''', (biz_no, visit_date, user_id)).fetchone()
        
        if existing:
            return jsonify({"success": False, "message": "이미 해당 날짜에 등록한 기업입니다."})
        
        # 삽입
        result = conn.execute('''
            INSERT INTO Pioneering_Targets 
            (biz_no, visit_date, visitor_id, notes, registered_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (biz_no, visit_date, visitor_id, notes, user_id))
        
        conn.commit()
        
        return jsonify({
            "success": True, 
            "message": "개척 대상이 정상적으로 등록되었습니다.", 
            "id": result.lastrowid
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"등록 중 오류가 발생했습니다: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/pioneering_targets/<int:target_id>', methods=['DELETE'])
def delete_pioneering_target(target_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 권한 확인: 본인이 등록한 타겟이거나 관리자인 경우만 삭제 가능
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM Pioneering_Targets WHERE id = ?", (target_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        conn.execute("DELETE FROM Pioneering_Targets WHERE id = ?", (target_id,))
        conn.commit()
        return jsonify({"success": True, "message": "개척 대상이 삭제되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/pioneering_targets/<int:target_id>/visit', methods=['PUT'])
def mark_target_visited(target_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE Pioneering_Targets SET 
                is_visited = 1, 
                visited_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (target_id,))
        conn.commit()
        return jsonify({"success": True, "message": "방문 완료 처리되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/pioneering_targets/upload', methods=['POST'])
def upload_pioneering_csv():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'message': 'CSV 파일만 업로드 가능합니다.'}), 400
    
    user_id = session.get('user_id')
    
    try:
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)
        
        conn = get_db_connection()
        inserted = 0
        
        for row in reader:
            if row.get('사업자번호') and row.get('방문일자'):
                try:
                    conn.execute('''
                        INSERT INTO Pioneering_Targets 
                        (biz_no, visit_date, visitor_id, registered_by)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        row['사업자번호'], row['방문일자'], 
                        row.get('방문자ID', user_id), user_id
                    ))
                    inserted += 1
                except Exception as e:
                    continue  # 중복 등의 오류는 무시하고 계속
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'inserted': inserted, 'message': f'{inserted}건이 등록되었습니다.'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'CSV 처리 중 오류: {str(e)}'}), 500

# --- 영업비용 관리 API ---
@app.route('/api/sales_expenses', methods=['GET'])
def get_sales_expenses():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 권한에 따른 조회 범위 설정
        if check_permission(user_level, 'S'):  # 관리자는 모든 비용 조회
            expenses = conn.execute('''
                SELECT e.id, e.expense_date, 
                       COALESCE(e.expense_type, e.category) as expense_type, 
                       e.amount, e.payment_method,
                       e.description, e.receipt_image as receipt_file, e.registered_by,
                       u.name as registered_by_name, e.created_date
                FROM Sales_Expenses e
                LEFT JOIN Users u ON e.registered_by = u.user_id
                ORDER BY e.expense_date DESC
            ''').fetchall()
        else:  # 일반 사용자는 본인 등록 비용만 조회
            expenses = conn.execute('''
                SELECT e.id, e.expense_date, 
                       COALESCE(e.expense_type, e.category) as expense_type, 
                       e.amount, e.payment_method,
                       e.description, e.receipt_image as receipt_file, e.registered_by,
                       u.name as registered_by_name, e.created_date
                FROM Sales_Expenses e
                LEFT JOIN Users u ON e.registered_by = u.user_id
                WHERE e.registered_by = ?
                ORDER BY e.expense_date DESC
            ''', (user_id,)).fetchall()
        
        return jsonify([dict(expense) for expense in expenses])
    finally:
        conn.close()

@app.route('/api/sales_expenses', methods=['POST'])
def add_sales_expense():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    
    # 여러 파일 업로드 처리
    receipt_filenames = []
    if 'receipt_files' in request.files:
        files = request.files.getlist('receipt_files')
        
        # 최대 3개 파일 제한
        if len(files) > 3:
            return jsonify({"error": "최대 3개의 파일만 업로드 가능합니다."}), 400
        
        for file in files:
            if file and file.filename:
                # 이미지 파일 형식 체크
                allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
                file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                
                if file_ext not in allowed_extensions:
                    return jsonify({"error": "이미지 파일만 업로드 가능합니다."}), 400
                
                # 파일명 보안을 위해 secure_filename 사용
                filename = secure_filename(file.filename)
                # 중복 방지를 위해 타임스탬프 추가
                timestamp = str(int(time.time()))
                filename = f"{timestamp}_{filename}"
                
                # 파일 저장
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                receipt_filenames.append(filename)
    
    # 파일명들을 JSON 형태로 저장 (여러 파일 지원)
    receipt_data = ','.join(receipt_filenames) if receipt_filenames else None
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO Sales_Expenses 
            (expense_date, category, expense_type, amount, payment_method, description, receipt_image, registered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form.get('expense_date'), 
            request.form.get('expense_type'),  # category 필드
            request.form.get('expense_type'),  # expense_type 필드 
            request.form.get('amount'), 
            request.form.get('payment_method', '개인카드'),  # 기본값 설정
            request.form.get('description'), 
            receipt_data, 
            user_id
        ))
        conn.commit()
        return jsonify({"success": True, "message": "영업비용이 등록되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/sales_expenses/<int:expense_id>', methods=['PUT'])
def update_sales_expense(expense_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 권한 확인: 본인이 등록한 비용이거나 관리자인 경우만 수정 가능
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM Sales_Expenses WHERE id = ?", (expense_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        # 파일 업로드 처리 (수정 시 영수증 파일 저장)
        receipt_filename = None
        if 'receipt_file' in request.files:
            file = request.files['receipt_file']
            if file and file.filename:
                # 이미지 파일 형식 체크
                allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
                file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if file_ext not in allowed_extensions:
                    return jsonify({"error": "이미지 파일만 업로드 가능합니다."}), 400

                # 파일명 보안을 위해 secure_filename 사용
                filename = secure_filename(file.filename)
                # 중복 방지를 위해 타임스탬프 추가
                timestamp = str(int(time.time()))
                filename = f"{timestamp}_{filename}"

                # 파일 저장
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    file.save(file_path)
                except Exception as save_err:
                    print(f"[FILE_SAVE_ERROR] {save_err}")
                    return jsonify({"success": False, "message": "파일 저장 중 오류가 발생했습니다."}), 500

                receipt_filename = filename
        
        # 파일이 새로 업로드되지 않은 경우 기존 파일명 유지
        if receipt_filename:
            conn.execute('''
                UPDATE Sales_Expenses SET 
                    expense_date=?, category=?, expense_type=?, amount=?, payment_method=?, 
                    description=?, receipt_image=?, updated_date=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (
                request.form.get('expense_date'), 
                request.form.get('expense_type'),  # category
                request.form.get('expense_type'),  # expense_type
                request.form.get('amount'), 
                request.form.get('payment_method'),
                request.form.get('description'), 
                receipt_filename, 
                expense_id
            ))
        else:
            conn.execute('''
                UPDATE Sales_Expenses SET 
                    expense_date=?, category=?, expense_type=?, amount=?, payment_method=?, 
                    description=?, updated_date=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (
                request.form.get('expense_date'), 
                request.form.get('expense_type'),  # category
                request.form.get('expense_type'),  # expense_type
                request.form.get('amount'), 
                request.form.get('payment_method'),
                request.form.get('description'), 
                expense_id
            ))
        
        conn.commit()
        return jsonify({"success": True, "message": "영업비용 정보가 수정되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/sales_expenses/<int:expense_id>', methods=['DELETE'])
def delete_sales_expense(expense_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # 권한 확인: 본인이 등록한 비용이거나 관리자인 경우만 삭제 가능
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM Sales_Expenses WHERE id = ?", (expense_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        conn.execute("DELETE FROM Sales_Expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return jsonify({"success": True, "message": "영업비용이 삭제되었습니다."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- 개척대상 기업 CSV 처리 API ---
@app.route('/api/pioneering_targets_csv', methods=['GET', 'POST'])
def pioneering_targets_csv():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        # CSV 다운로드
        conn = get_db_connection()
        rows = conn.execute('''
            SELECT p.id, p.biz_no, b.company_name, p.visit_date, p.visitor_id, 
                   CASE WHEN p.is_visited = 1 THEN '완료' ELSE '예정' END as visit_status,
                   p.notes, p.registered_by, p.created_date
            FROM Pioneering_Targets p
            LEFT JOIN Company_Basic b ON REPLACE(p.biz_no, '-', '') = b.biz_no
            ORDER BY p.id
        ''').fetchall()
        conn.close()
        
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['번호', '사업자번호', '회사명', '방문일자', '방문자ID', '방문상태', '메모', '등록자', '등록일'])
        for row in rows:
            # 사업자번호와 방문일자에서 하이픈 제거
            biz_no = row['biz_no'].replace('-', '') if row['biz_no'] else ''
            visit_date = row['visit_date'].replace('-', '') if row['visit_date'] else ''
            
            cw.writerow([row['id'], biz_no, row['company_name'], visit_date, 
                        row['visitor_id'], row['visit_status'], row['notes'], row['registered_by'], row['created_date']])
        
        output = si.getvalue().encode('utf-8-sig')
        return Response(output, mimetype='text/csv', 
                       headers={"Content-Disposition": "attachment;filename=pioneering_targets.csv"})
    
    else:
        # CSV 업로드
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '파일이 선택되지 않았습니다.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '파일이 선택되지 않았습니다.'}), 400
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': 'CSV 파일만 업로드 가능합니다.'}), 400
        
        # 인코딩 감지 및 처리
        content = file.stream.read()
        try:
            decoded_content = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                decoded_content = content.decode('cp949')
            except UnicodeDecodeError:
                decoded_content = content.decode('utf-8', errors='ignore')
        
        stream = io.StringIO(decoded_content)
        reader = csv.DictReader(stream)
        
        conn = get_db_connection()
        user_id = session.get('user_id')
        
        try:
            inserted = 0
            for row in reader:
                # 필수 필드 확인
                if not all([row.get('사업자번호'), row.get('방문일자'), row.get('방문자ID')]):
                    continue
                
                # 사업자번호와 방문일자 형식 정리 (하이픈 추가)
                biz_no = row.get('사업자번호', '').replace('-', '')
                if len(biz_no) == 10:  # 일반 사업자번호
                    biz_no = f"{biz_no[:3]}-{biz_no[3:5]}-{biz_no[5:]}"
                elif len(biz_no) == 13:  # 법인등록번호
                    biz_no = f"{biz_no[:6]}-{biz_no[6:]}"
                
                visit_date = row.get('방문일자', '').replace('-', '')
                if len(visit_date) == 8:  # YYYYMMDD 형식
                    visit_date = f"{visit_date[:4]}-{visit_date[4:6]}-{visit_date[6:]}"
                
                # 방문상태를 is_visited로 변환
                visit_status = row.get('방문상태', '예정')
                is_visited = 1 if visit_status == '완료' else 0
                
                conn.execute('''
                    INSERT INTO Pioneering_Targets (biz_no, visit_date, visitor_id, is_visited, notes, registered_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    biz_no, visit_date, row.get('방문자ID'),
                    is_visited, row.get('메모', ''), user_id
                ))
                inserted += 1
            
            conn.commit()
            return jsonify({'success': True, 'message': f'{inserted}건의 개척대상이 등록되었습니다.', 'inserted': inserted})
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            conn.close()

# --- 영업비용 CSV 처리 API ---
@app.route('/api/sales_expenses_csv', methods=['GET', 'POST'])
def sales_expenses_csv():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        # CSV 다운로드
        conn = get_db_connection()
        user_id = session.get('user_id')
        user_level = session.get('user_level', 'N')
        
        # 권한에 따른 조회 범위 설정
        if check_permission(user_level, 'S'):
            # 관리자는 전체 조회
            rows = conn.execute('''
                SELECT id, expense_date, expense_type, amount, payment_method, 
                       description, receipt_filename, registered_by, created_date
                FROM Sales_Expenses ORDER BY expense_date DESC
            ''').fetchall()
        else:
            # 일반 사용자는 본인 등록건만 조회
            rows = conn.execute('''
                SELECT id, expense_date, expense_type, amount, payment_method, 
                       description, receipt_filename, registered_by, created_date
                FROM Sales_Expenses WHERE registered_by = ? ORDER BY expense_date DESC
            ''', (user_id,)).fetchall()
        
        conn.close()
        
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['번호', '날짜', '항목', '금액', '결제방법', '설명', '영수증파일', '등록자', '등록일'])
        for row in rows:
            cw.writerow([row['id'], row['expense_date'], row['expense_type'], row['amount'], 
                        row['payment_method'], row['description'], row['receipt_filename'], 
                        row['registered_by'], row['created_date']])
        
        output = si.getvalue().encode('utf-8-sig')
        return Response(output, mimetype='text/csv', 
                       headers={"Content-Disposition": "attachment;filename=sales_expenses.csv"})
    
    else:
        # CSV 업로드
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': 'CSV 파일만 업로드 가능합니다.'}), 400
        
        # 인코딩 감지 및 처리
        content = file.stream.read()
        try:
            decoded_content = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                decoded_content = content.decode('cp949')
            except UnicodeDecodeError:
                decoded_content = content.decode('utf-8', errors='ignore')
        
        stream = io.StringIO(decoded_content)
        reader = csv.DictReader(stream)
        
        conn = get_db_connection()
        user_id = session.get('user_id')
        
        try:
            inserted = 0
            for row in reader:
                # 필수 필드 확인
                if not all([row.get('날짜'), row.get('항목'), row.get('금액')]):
                    continue
                
                conn.execute('''
                    INSERT INTO Sales_Expenses (expense_date, expense_type, amount, payment_method, description, registered_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('날짜'), row.get('항목'), row.get('금액'),
                    row.get('결제방법', '현금'), row.get('설명', ''), user_id
                ))
                inserted += 1
            
            conn.commit()
            return jsonify({'success': True, 'message': f'{inserted}건의 영업비용이 등록되었습니다.', 'inserted': inserted})
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            conn.close()

@app.route('/api/change-password', methods=['POST'])
def api_change_password():
    """비밀번호 변경 API"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    
    data = request.get_json()
    new_password = data.get('new_password')
    
    if not new_password:
        return jsonify({"success": False, "message": "새 비밀번호를 입력해주세요."}), 400
    
    # 비밀번호 복잡성 검사
    import re
    password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,20}$'
    if not re.match(password_pattern, new_password):
        return jsonify({"success": False, "message": "비밀번호는 8-20자리로 대문자, 소문자, 숫자, 특수문자를 모두 포함해야 합니다."}), 400
    
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    try:
        # 사용자 존재 확인
        user = conn.execute("SELECT password FROM Users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            return jsonify({"success": False, "message": "사용자를 찾을 수 없습니다."}), 404
        
        # 현재 비밀번호와 동일한지 확인 (같으면 변경 거부)
        if user['password'] == new_password:
            return jsonify({"success": False, "message": "현재 비밀번호와 다른 비밀번호를 입력해주세요."}), 400
        
        # 새 비밀번호로 업데이트
        conn.execute("""
            UPDATE Users 
            SET password = ?, password_changed_date = CURRENT_TIMESTAMP, updated_date = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (new_password, user_id))
        
        conn.commit()
        
        # 세션 초기화 (다시 로그인하도록)
        session.clear()
        
        return jsonify({"success": True, "message": "비밀번호가 성공적으로 변경되었습니다."})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# ==========================================
# 영업 파이프라인 관리 시스템
# ==========================================

@app.route('/pipeline')
def sales_pipeline():
    """영업 파이프라인 대시보드"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    return render_template('pipeline.html', 
                         user_id=user_id,
                         user_level=user_level,
                         user_name=session.get('user_name', ''))

@app.route('/api/pipeline/dashboard')
def pipeline_dashboard_data():
    """파이프라인 대시보드 데이터 API"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다"}), 401
    
    user_id = session.get('user_id')
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        # 오늘 연락해야 할 기업
        today = datetime.now().strftime('%Y-%m-%d')

        # [ACCESS CONTROL] ct0001, ct0002 파트너십 로직 적용
        target_managers = [user_id]
        if user_id in ['ct0001', 'ct0002']:
            target_managers = ['ct0001', 'ct0002']
            
        mgr_placeholders = ','.join(['?'] * len(target_managers))
        
        # 오늘 연락해야 할 기업
        today = datetime.now().strftime('%Y-%m-%d')
        today_contacts_query = f'''
            SELECT mc.id, mc.biz_reg_no, mc.manager_id, mc.status, mc.keyman_name,
                   mc.keyman_phone, mc.keyman_position, mc.keyman_email, mc.registration_reason,
                   mc.next_contact_date, mc.last_contact_date, mc.notes, mc.expected_amount,
                   mc.priority_level, mc.created_at, mc.updated_at,
                   cb.company_name, cb.representative_name 
            FROM managed_companies mc
            LEFT JOIN Company_Basic cb ON mc.biz_reg_no = cb.biz_no
            WHERE mc.manager_id IN ({mgr_placeholders}) AND mc.next_contact_date = ?
            ORDER BY mc.priority_level DESC
        '''
        cursor.execute(today_contacts_query, (*target_managers, today))
        today_contacts = cursor.fetchall()
        
        # 관리 소홀 기업 (상태별 알림 주기 적용)
        urgent_companies = []
        status_periods = {
            'prospect': 14, 'contacted': 7, 'proposal': 3, 
            'negotiation': 2, 'contract': 30, 'hold': 30
        }
        
        for status, days in status_periods.items():
            threshold_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            urgent_query = f'''
                SELECT mc.id, mc.biz_reg_no, mc.manager_id, mc.status, mc.keyman_name,
                       mc.keyman_phone, mc.keyman_position, mc.keyman_email, mc.registration_reason,
                       mc.next_contact_date, mc.last_contact_date, mc.notes, mc.expected_amount,
                       mc.priority_level, mc.created_at, mc.updated_at,
                       cb.company_name, cb.representative_name 
                FROM managed_companies mc
                LEFT JOIN Company_Basic cb ON mc.biz_reg_no = cb.biz_no
                WHERE mc.manager_id IN ({mgr_placeholders}) AND mc.status = ? 
                AND (mc.last_contact_date IS NULL OR mc.last_contact_date < ?)
                ORDER BY CASE WHEN mc.last_contact_date IS NULL THEN 0 ELSE 1 END, mc.last_contact_date ASC
            '''
            cursor.execute(urgent_query, (*target_managers, status, threshold_date))
            urgent_for_status = cursor.fetchall()
            urgent_companies.extend(urgent_for_status)
        
        # 전체 관리 기업 현황
        # 전체 관리 기업 현황
        total_query = f'''
            SELECT mc.id, mc.biz_reg_no, mc.manager_id, mc.status, mc.keyman_name,
                   mc.keyman_phone, mc.keyman_position, mc.keyman_email, mc.registration_reason,
                   mc.next_contact_date, mc.last_contact_date, mc.notes, mc.expected_amount,
                   mc.priority_level, mc.created_at, mc.updated_at,
                   cb.company_name, cb.representative_name 
            FROM managed_companies mc
            LEFT JOIN Company_Basic cb ON mc.biz_reg_no = cb.biz_no
            WHERE mc.manager_id IN ({mgr_placeholders})
            ORDER BY mc.updated_at DESC
        '''
        cursor.execute(total_query, tuple(target_managers))
        all_companies = cursor.fetchall()
        
        # 상태별 통계
        # 상태별 통계
        stats_query = f'''
            SELECT status, COUNT(*) as count, 
                   COALESCE(SUM(expected_amount), 0) as total_amount
            FROM managed_companies 
            WHERE manager_id IN ({mgr_placeholders})
            GROUP BY status
        '''
        cursor.execute(stats_query, tuple(target_managers))
        status_stats = {row[0]: {'count': row[1], 'amount': row[2]} for row in cursor.fetchall()}
        
        return jsonify({
            "success": True,
            "data": {
                "today_contacts": [dict(row) for row in today_contacts],
                "urgent_companies": [dict(row) for row in urgent_companies],
                "all_companies": [dict(row) for row in all_companies],
                "status_stats": status_stats
            }
        })
        
    except Exception as e:
        print(f"Pipeline dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/pipeline/company', methods=['POST'])
def add_managed_company():
    """관심 기업 등록"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다"}), 401
    
    user_id = session.get('user_id')
    data = request.get_json()
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 기업 정보 확인
        cursor.execute('SELECT biz_no, company_name FROM Company_Basic WHERE biz_no = ?', (data['biz_reg_no'],))
        company = cursor.fetchone()
        if not company:
            return jsonify({"success": False, "message": "존재하지 않는 기업입니다"}), 400
        
        # 중복 등록 확인
        cursor.execute('SELECT id FROM managed_companies WHERE biz_reg_no = ? AND manager_id = ?', 
                      (data['biz_reg_no'], user_id))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "이미 관리 중인 기업입니다"}), 400
        
        # 새 관심 기업 등록
        insert_query = '''
            INSERT INTO managed_companies 
            (biz_reg_no, manager_id, status, keyman_name, keyman_phone, keyman_position, 
             keyman_email, registration_reason, next_contact_date, notes, expected_amount, priority_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        cursor.execute(insert_query, (
            data['biz_reg_no'], user_id, data.get('status', 'prospect'),
            data['keyman_name'], data.get('keyman_phone'), data.get('keyman_position'),
            data.get('keyman_email'), data.get('registration_reason'),
            data.get('next_contact_date'), data.get('notes'),
            data.get('expected_amount', 0), data.get('priority_level', 1)
        ))
        
        company_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({"success": True, "message": "관심 기업이 등록되었습니다", "company_id": company_id})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/pipeline/company/<int:company_id>', methods=['PUT'])
def update_managed_company(company_id):
    """관심 기업 정보 수정"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다"}), 401
    
    user_id = session.get('user_id')
    data = request.get_json()
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 권한 확인
        cursor.execute('SELECT manager_id FROM managed_companies WHERE id = ?', (company_id,))
        result = cursor.fetchone()
        if not result or result[0] != user_id:
            return jsonify({"success": False, "message": "수정 권한이 없습니다"}), 403
        
        # 정보 업데이트
        update_query = '''
            UPDATE managed_companies SET
                status = ?, keyman_name = ?, keyman_phone = ?, keyman_position = ?,
                keyman_email = ?, next_contact_date = ?, last_contact_date = ?, notes = ?, 
                expected_amount = ?, priority_level = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        
        cursor.execute(update_query, (
            data.get('status'), data.get('keyman_name'), data.get('keyman_phone'),
            data.get('keyman_position'), data.get('keyman_email'),
            data.get('next_contact_date'), data.get('last_contact_date'), data.get('notes'),
            data.get('expected_amount', 0), data.get('priority_level', 1),
            company_id
        ))
        
        conn.commit()
        return jsonify({"success": True, "message": "기업 정보가 수정되었습니다"})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/pipeline/company/<int:company_id>', methods=['DELETE'])
def delete_managed_company(company_id):
    """관심 기업 삭제 (접촉 이력 포함)"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다"}), 401
    
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 권한 확인
        cursor.execute('SELECT manager_id, company_name FROM managed_companies WHERE id = ?', (company_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"success": False, "message": "기업을 찾을 수 없습니다"}), 404
        if result[0] != user_id:
            return jsonify({"success": False, "message": "삭제 권한이 없습니다"}), 403
        
        company_name = result[1]
        
        # 관련 접촉 이력 먼저 삭제
        cursor.execute('DELETE FROM pipeline_contact_history WHERE managed_company_id = ?', (company_id,))
        deleted_contacts = cursor.rowcount
        
        # 기업 정보 삭제
        cursor.execute('DELETE FROM managed_companies WHERE id = ?', (company_id,))
        
        conn.commit()
        return jsonify({
            "success": True, 
            "message": f"'{company_name}' 기업이 삭제되었습니다. (접촉이력 {deleted_contacts}건 삭제)"
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/pipeline/contact', methods=['POST'])
def add_contact_history():
    """접촉 이력 등록"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다"}), 401
    
    user_id = session.get('user_id')
    data = request.get_json()
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 관리 권한 확인
        cursor.execute('SELECT manager_id FROM managed_companies WHERE id = ?', 
                      (data['managed_company_id'],))
        result = cursor.fetchone()
        if not result or result[0] != user_id:
            return jsonify({"success": False, "message": "접촉 이력을 등록할 권한이 없습니다"}), 403
        
        # 접촉 이력 등록
        insert_query = '''
            INSERT INTO pipeline_contact_history 
            (managed_company_id, contact_date, contact_type, content, cost, 
             follow_up_required, follow_up_date, attachment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        cursor.execute(insert_query, (
            data['managed_company_id'], data['contact_date'], data['contact_type'],
            data['content'], data.get('cost', 0), data.get('follow_up_required', 0),
            data.get('follow_up_date'), data.get('attachment')
        ))
        
        # 부모 테이블의 last_contact_date 자동 업데이트
        cursor.execute('''
            UPDATE managed_companies 
            SET last_contact_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (data['contact_date'], data['managed_company_id']))
        
        # 후속 약속이 있으면 next_contact_date도 업데이트
        if data.get('follow_up_date'):
            cursor.execute('''
                UPDATE managed_companies 
                SET next_contact_date = ?
                WHERE id = ?
            ''', (data['follow_up_date'], data['managed_company_id']))
        
        conn.commit()
        return jsonify({"success": True, "message": "접촉 이력이 등록되었습니다"})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/pipeline/contact/<int:company_id>')
def get_pipeline_contact_history(company_id):
    """특정 기업의 접촉 이력 조회"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다"}), 401
    
    user_id = session.get('user_id')
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        # 관리 권한 확인
        cursor.execute('SELECT manager_id FROM managed_companies WHERE id = ?', (company_id,))
        result = cursor.fetchone()
        if not result or result[0] != user_id:
            return jsonify({"success": False, "message": "조회 권한이 없습니다"}), 403
        
        # 접촉 이력 조회
        history_query = '''
            SELECT * FROM pipeline_contact_history 
            WHERE managed_company_id = ?
            ORDER BY contact_date DESC, created_at DESC
        '''
        cursor.execute(history_query, (company_id,))
        history = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({"success": True, "data": history})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/ai-analysis', methods=['POST'])
@app.route('/api/ai_analysis', methods=['POST'])
def ai_analysis_stream():
    """AI 기업 분석 API (스트리밍)"""

    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다"}), 401
    
    data = request.get_json()
    biz_no = data.get('biz_no')
    
    if not biz_no:
        return jsonify({"success": False, "message": "사업자번호가 필요합니다"}), 400
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 기업 기본 정보 조회
        cursor.execute('''
            SELECT company_name, representative_name, industry_name, address, pension_count
            FROM Company_Basic 
            WHERE biz_no = ?
        ''', (biz_no,))
        
        company_basic = cursor.fetchone()
        if not company_basic:
            return jsonify({"success": False, "message": "기업 정보를 찾을 수 없습니다"}), 404
        
        # 재무 정보 조회 (최근 3년)
        cursor.execute('''
            SELECT fiscal_year, sales_revenue, operating_income, total_assets, 
                   total_equity, retained_earnings, corporate_tax
            FROM Company_Financial 
            WHERE biz_no = ? 
            ORDER BY fiscal_year DESC 
            LIMIT 3
        ''', (biz_no,))
        
        financials = cursor.fetchall()
        
        # 접촉이력 조회 (최근 10건)
        cursor.execute('''
            SELECT contact_datetime, contact_type, contact_person, memo, registered_by
            FROM Contact_History 
            WHERE biz_no = ? 
            ORDER BY contact_datetime DESC 
            LIMIT 10
        ''', (biz_no,))
        
        contact_history = cursor.fetchall()
        
        # 주주 정보 조회 (상위 10명)
        cursor.execute('''
            SELECT shareholder_name, relationship, ownership_percent, total_shares_owned
            FROM Company_Shareholder 
            WHERE biz_no = ? 
            ORDER BY CAST(ownership_percent AS REAL) DESC 
            LIMIT 10
        ''', (biz_no,))
        
        shareholders = cursor.fetchall()
        
        # AI 분석 실행
        analysis_result = perform_ai_analysis(company_basic, financials, contact_history, shareholders)
        
        return jsonify({
            "success": True,
            "analysis": analysis_result
        })
        
    except Exception as e:
        print(f"AI 분석 오류: {e}")
        return jsonify({"success": False, "message": f"분석 중 오류 발생: {str(e)}"}), 500
    finally:
        conn.close()

def perform_ai_analysis(company_basic, financials, contact_history=None, shareholders=None):
    """OpenAI API를 사용한 전문적인 경영 컨설팅 분석"""
    import os
    import json
    from openai import OpenAI
    
    # 기업 기본 정보 추출
    company_name = company_basic[0] or "정보없음"
    representative = company_basic[1] or "정보없음"  
    industry = company_basic[2] or "정보없음"
    address = company_basic[3] or "정보없음"
    employee_count = company_basic[4] or 0  # pension_count를 직원수로 사용
    
    # 재무 분석
    financial_summary = ""
    latest_year_data = None
    
    if financials and len(financials) > 0:
        latest_year_data = financials[0]
        
        # 최근 3년 데이터 분석
        revenue_trend = []
        profit_trend = []
        asset_trend = []
        
        for fin in financials:
            if fin[1]:  # 매출액
                revenue_trend.append(fin[1])
            if fin[2]:  # 영업이익
                profit_trend.append(fin[2])
            if fin[3]:  # 자산총계
                asset_trend.append(fin[3])
        
        # 성장률 계산
        revenue_growth = "안정적" if len(revenue_trend) > 1 else "데이터 부족"
        if len(revenue_trend) >= 2:
            growth_rate = ((revenue_trend[0] - revenue_trend[-1]) / revenue_trend[-1]) * 100
            if growth_rate > 10:
                revenue_growth = f"고성장 ({growth_rate:.1f}%)"
            elif growth_rate > 0:
                revenue_growth = f"성장세 ({growth_rate:.1f}%)"
            elif growth_rate > -10:
                revenue_growth = f"소폭 감소 ({growth_rate:.1f}%)"
            else:
                revenue_growth = f"감소세 ({growth_rate:.1f}%)"
        
        financial_summary = f"최근년도 매출액: {latest_year_data[1]:,}원, 성장추세: {revenue_growth}"
    
    # OpenAI API 사용 (환경변수에서 API 키 확인)
    api_key = os.environ.get('OPENAI_API_KEY')
    print(f"API 키 확인: {api_key[:20]}..." if api_key else "API 키 없음")
    
    if api_key and api_key.startswith('sk-'):
        try:
            # OpenAI 클라이언트 초기화
            client = OpenAI(api_key=api_key)
            
            # 더 상세한 재무 분석을 위한 데이터 구성
            financial_details = ""
            if financials and len(financials) > 0:
                financial_details = "재무 상세 정보:\n"
                for i, fin in enumerate(financials):
                    year = fin[0]
                    revenue = fin[1] if fin[1] else 0
                    profit = fin[2] if fin[2] else 0
                    assets = fin[3] if fin[3] else 0
                    equity = fin[4] if fin[4] else 0
                    
                    financial_details += f"? {year}년: 매출액 {revenue:,}원, 영업이익 {profit:,}원, 자산총계 {assets:,}원, 자본총계 {equity:,}원\n"
                    
                    # 재무비율 계산
                    if assets > 0 and revenue > 0:
                        roe = (profit / equity * 100) if equity > 0 else 0
                        asset_turnover = revenue / assets
                        profit_margin = (profit / revenue * 100) if revenue > 0 else 0
                        financial_details += f"  - ROE: {roe:.1f}%, 자산회전율: {asset_turnover:.2f}, 영업이익률: {profit_margin:.1f}%\n"
            
            # 접촉이력 정보 구성
            contact_summary = ""
            if contact_history and len(contact_history) > 0:
                contact_summary = "== 영업 접촉 이력 (최근 10건) ==\n"
                for i, contact in enumerate(contact_history, 1):
                    date = contact[0] or "날짜미상"
                    type_ = contact[1] or "일반접촉"
                    person = contact[2] or "미상"
                    memo = contact[3] or ""
                    registered_by = contact[4] or "시스템"
                    
                    contact_summary += f"{i}. [{date}] {type_} - {person}\n"
                    if memo:
                        contact_summary += f"   내용: {memo[:100]}{'...' if len(memo) > 100 else ''}\n"
                    contact_summary += f"   담당자: {registered_by}\n\n"
            else:
                contact_summary = "== 영업 접촉 이력 ==\n아직 접촉 이력이 없습니다.\n\n"
            
            # 주주 정보 구성
            shareholder_summary = ""
            if shareholders and len(shareholders) > 0:
                shareholder_summary = "== 주주 구조 (상위 10명) ==\n"
                total_ownership = 0
                for i, sh in enumerate(shareholders, 1):
                    name = sh[0] or "미상"
                    position = sh[1] or ""
                    ratio = sh[2] or "0"
                    shares = sh[3] or "0"
                    
                    try:
                        ratio_float = float(ratio) if ratio else 0.0
                        total_ownership += ratio_float
                    except:
                        ratio_float = 0.0
                    
                    shareholder_summary += f"{i}. {name}"
                    if position:
                        shareholder_summary += f" ({position})"
                    shareholder_summary += f" - 지분율: {ratio_float:.2f}%"
                    if shares and shares != "0":
                        try:
                            shares_int = int(float(shares))
                            shareholder_summary += f", 보유주식: {shares_int:,}주"
                        except:
                            pass
                    shareholder_summary += "\n"
                
                shareholder_summary += f"\n상위 {min(len(shareholders), 10)}인 합계 지분율: {total_ownership:.2f}%\n\n"
            else:
                shareholder_summary = "== 주주 구조 ==\n주주 정보가 없습니다.\n\n"
            
            # 전문적인 경영 컨설팅 분석 프롬프트 구성
            detailed_prompt = f"""
당신은 기업 경영 컨설턴트이자 재무 분석 전문가입니다. 다음 기업에 대해 **경영 개선 및 성장 전략 중심**의 실질적인 컨설팅 보고서를 작성해주세요.

== 기업 기본 정보 ==
• 기업명: {company_name}
• 대표자: {representative}
• 업종: {industry}
• 본사: {address}
• 직원수: {employee_count}명 (국민연금 가입자)

== 재무 정보 (최근 3개년) ==
{financial_details}

{shareholder_summary}

{contact_summary}

== 경영 컨설팅 보고서 작성 요청 ==

**중요**: 투자 추천이나 주가 평가는 제외하고, 순수하게 **경영 개선과 성장 전략**에 초점을 맞춘 보고서를 작성해주세요.

다음 4개 섹션으로 구성된 **최소 1200자 이상**의 상세한 경영 컨설팅 보고서를 작성해주세요:

**1. 기업 현황 종합 분석** (350자 이상)
   - 업종 특성과 현재 시장 환경 분석
   - 기업의 핵심 강점과 개선이 필요한 약점 (SWOT)
   - 주주 구조 분석 (대주주 지배구조, 경영권 안정성)
   - 경쟁사 대비 포지셔닝 및 차별화 요소
   - 사업 모델의 지속가능성과 성장 잠재력
   - 조직 규모(직원수)의 적정성 평가

**2. 재무 건전성 및 성과 평가** (350자 이상)
   - 3개년 재무 추이의 심층 분석 (매출, 수익성, 자산 변화)
   - 핵심 수익성 지표 분석
     * 매출 성장률과 성장 지속가능성
     * 영업이익률, 순이익률 추이
     * ROE, ROA 등 자본 효율성
   - 재무 안정성 지표 심층 분석
     * 부채비율, 차입금 규모와 부담
     * 유동비율, 당좌비율 (단기 지급능력)
     * 자기자본비율 (재무구조 건전성)
   - 현금흐름 분석 (영업/투자/재무 활동)
   - 동종업계 평균 대비 비교 평가
   - 재무제표에서 발견되는 특이사항이나 리스크 신호

**3. 핵심 경영 과제 및 리스크** (300자 이상)
   - **재무적 과제**
     * 수익성 개선 방안 (매출 증대, 비용 절감)
     * 재무구조 개선 방안 (부채 관리, 자본 확충)
     * 현금흐름 관리 및 유동성 개선
   - **영업 및 시장 과제**
     * 시장 점유율 확대 방안
     * 신규 고객 확보 및 기존 고객 관리
     * 제품/서비스 경쟁력 강화
   - **조직 및 경영 과제**
     * 조직 효율성 개선
     * 인력 구조 최적화
     * 의사결정 체계 개선
   - **접촉이력 기반 실제 이슈**
     * 영업 활동에서 파악된 실질적인 경영 애로사항
     * 고객 관계 개선이 필요한 부분
   - 각 과제별 구체적인 해결 방안 제시

**4. 실행 가능한 개선 과제** (300자 이상)
   - **즉시 실행 과제 (1-3개월)**
     * 빠르게 효과를 볼 수 있는 단기 개선 과제
     * 비용 절감, 프로세스 개선 등
     * 각 과제의 기대효과와 실행 방법
   
   - **단기 전략 과제 (6개월-1년)**
     * 영업 및 마케팅 전략 개선
     * 재무구조 최적화 (차입금 관리, 자금조달)
     * 고객 관리 체계 구축
     * 디지털화/자동화 추진
   
   - **중장기 성장 전략 (1-3년)**
     * 사업 확장 또는 다각화 방향
     * 시장 확대 전략 (지역, 고객층)
     * 기술 혁신 및 R&D 투자
     * 조직 역량 강화 (인재 확보, 교육)
   
   - **우선순위 및 로드맵**
     * 각 과제의 중요도와 시급성 평가
     * 예상 투자비용과 기대 효과
     * 단계별 실행 순서 제안

**작성 가이드라인:**
1. 구체적 수치와 데이터를 최대한 활용할 것
2. 이 기업만의 특수한 상황을 반영한 맞춤형 분석
3. 접촉이력에서 나타난 실제 영업 상황을 적극 반영
4. 주주구조를 고려한 지배구조 및 경영권 분석
5. 일반론이 아닌 실행 가능한 구체적 액션 아이템 제시
6. 전문적이되 이해하기 쉬운 실용적 용어 사용
7. **투자 추천, 주가 평가, 밸류에이션은 절대 언급하지 말 것**
8. 경영 개선과 성장 전략에만 집중
9. 총 1200자 이상의 충실한 내용

각 섹션은 단순 나열이 아닌, 논리적 흐름을 가진 분석 내러티브로 작성해주세요.
"""
            
            print(f"OpenAI API 호출 시작 - 기업명: {company_name}")
            
            # OpenAI API 호출
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": """당신은 맥킨지, BCG, 베인 등 글로벌 전략 컨설팅 기업의 시니어 파트너로 20년 이상 기업 컨설팅 경험을 보유하고 있습니다.

**전문 분야:**
- 경영 전략 및 사업 구조조정
- 재무 구조 개선 및 수익성 향상
- 조직 효율화 및 프로세스 혁신
- 영업 및 마케팅 전략
- 디지털 전환 및 혁신 전략

**컨설팅 원칙:**
1. 데이터 기반의 객관적 분석
2. 실행 가능한 구체적 액션 플랜 제시
3. 단기/중기/장기 로드맵 제공
4. 경영진이 즉시 실행할 수 있는 실용적 조언
5. 투자 추천이나 주가 평가는 절대 하지 않음 (경영 개선에만 집중)

**작성 스타일:**
- 전문적이되 실무자가 이해하기 쉬운 명확한 표현
- 구체적인 수치와 사례 활용
- 논리적이고 설득력 있는 분석 구조
- 긍정적이면서도 현실적인 개선 방향 제시"""
                    },
                    {
                        "role": "user", 
                        "content": detailed_prompt
                    }
                ],
                max_tokens=5000,  # 상세한 보고서를 위해 토큰 증가
                temperature=0.4,  # 창의적이면서도 일관성 있는 분석
                presence_penalty=0.2,  # 다양한 관점 제시
                frequency_penalty=0.1
            )
            
            # AI 응답 파싱
            ai_analysis = response.choices[0].message.content
            print(f"OpenAI API 응답 받음 - 응답 길이: {len(ai_analysis)} 문자")
            print(f"응답 미리보기: {ai_analysis[:200]}...")
            
            # 섹션별로 더 정확하게 파싱
            sections = {
                'summary': '',
                'financial_analysis': '',
                'risk_assessment': '',
                'recommendations': ''
            }
            
            # 섹션 구분을 위한 키워드 매칭 (컨설팅 보고서 구조)
            current_section = None
            lines = ai_analysis.split('\n')
            
            for line in lines:
                line = line.strip()
                # 1. 기업 현황 종합 분석
                if '기업 현황' in line or '기업 개요' in line or '사업 분석' in line or ('1.' in line[:5] and '기업' in line):
                    current_section = 'summary'
                # 2. 재무 건전성 및 성과 평가
                elif '재무' in line and ('건전성' in line or '성과' in line or '평가' in line) or ('2.' in line[:5] and '재무' in line):
                    current_section = 'financial_analysis'
                # 3. 핵심 경영 과제 및 리스크
                elif ('경영 과제' in line or '핵심' in line or '리스크' in line) or ('3.' in line[:5] and ('과제' in line or '리스크' in line)):
                    current_section = 'risk_assessment'
                # 4. 실행 가능한 개선 과제 (투자 관련 키워드 제거!)
                elif '실행' in line or '개선 과제' in line or '컨설팅 제안' in line or ('4.' in line[:5] and ('실행' in line or '개선' in line)):
                    current_section = 'recommendations'
                elif line and current_section:
                    sections[current_section] += line + ' '
            
            # 섹션이 비어있는 경우 전체 텍스트를 균등 분할
            if not any(sections.values()):
                paragraphs = [p.strip() for p in ai_analysis.split('\n\n') if p.strip()]
                if len(paragraphs) >= 4:
                    sections['summary'] = paragraphs[0]
                    sections['financial_analysis'] = paragraphs[1]
                    sections['risk_assessment'] = paragraphs[2]
                    sections['recommendations'] = paragraphs[3]
                else:
                    sections['summary'] = ai_analysis[:len(ai_analysis)//4]
                    sections['financial_analysis'] = ai_analysis[len(ai_analysis)//4:len(ai_analysis)//2]
                    sections['risk_assessment'] = ai_analysis[len(ai_analysis)//2:3*len(ai_analysis)//4]
                    sections['recommendations'] = ai_analysis[3*len(ai_analysis)//4:]
            
            return {
                "summary": sections['summary'].strip() or f"{company_name}는 {industry} 업종에서 사업을 영위하는 기업으로, {representative} 대표 체제 하에 운영되고 있습니다.",
                "financial_analysis": sections['financial_analysis'].strip() or f"재무분석: {financial_summary}를 기반으로 한 상세 분석이 제공됩니다.",
                "risk_assessment": sections['risk_assessment'].strip() or f"{industry} 업계의 일반적인 리스크와 기업 고유의 위험요소를 종합적으로 평가하였습니다.",
                "recommendations": sections['recommendations'].strip() or "전문적인 분석을 바탕으로 한 투자 의견과 향후 모니터링 포인트를 제시합니다."
            }
            
            
        except Exception as e:
            print(f"OpenAI API 오류 (고급 분석): {type(e).__name__}: {e}")
            import traceback
            print(f"상세 오류 정보: {traceback.format_exc()}") 
            # API 오류 시에도 기본 분석은 제공
    
    # API 키가 없거나 오류가 발생한 경우 기본 분석 반환
    return {
        "summary": f"{company_name}는 {industry} 업종에서 사업을 영위하는 기업으로, {representative} 대표 체제 하에 운영되고 있습니다.",
        "financial_analysis": f"재무분석: {financial_summary}를 기반으로 한 상세 분석이 제공됩니다.",
        "risk_assessment": f"{industry} 업계의 일반적인 리스크와 기업 고유의 위험요소를 종합적으로 평가하였습니다.",
        "recommendations": "전문적인 분석을 바탕으로 한 투자 의견과 향후 모니터링 포인트를 제시합니다."
    }

# =======================================================
# 그래프 시각화용 기업 분석 데이터 API
# =======================================================

@app.route('/api/company-analysis-data/<biz_no>')
def get_company_analysis_data(biz_no):
    """기업 분석 그래프용 데이터 API"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다"}), 401
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 기업 기본 정보
        cursor.execute('''
            SELECT company_name, representative_name, industry_name, address, 
                   pension_count, establish_date
            FROM Company_Basic 
            WHERE biz_no = ?
        ''', (biz_no,))
        basic_row = cursor.fetchone()
        
        if not basic_row:
            return jsonify({"success": False, "message": "기업 정보를 찾을 수 없습니다"}), 404
        
        company_info = {
            "company_name": basic_row[0] or "",
            "representative_name": basic_row[1] or "",
            "industry_name": basic_row[2] or "",
            "address": basic_row[3] or "",
            "employee_count": basic_row[4] or 0,
            "establish_date": basic_row[5] or ""
        }
        
        # 주주 정보 (전체)
        cursor.execute('''
            SELECT shareholder_name, relationship, ownership_percent, total_shares_owned
            FROM Company_Shareholder 
            WHERE biz_no = ? 
            ORDER BY CAST(COALESCE(ownership_percent, '0') AS REAL) DESC
        ''', (biz_no,))
        
        shareholders = []
        for row in cursor.fetchall():
            try:
                percent = float(row[2]) if row[2] else 0.0
            except:
                percent = 0.0
            try:
                shares = int(float(row[3])) if row[3] else 0
            except:
                shares = 0
            shareholders.append({
                "name": row[0] or "미상",
                "relationship": row[1] or "",
                "ownership_percent": percent,
                "shares": shares
            })
        
        # 재무 정보 (최근 3년)
        cursor.execute('''
            SELECT fiscal_year, sales_revenue, operating_income, net_income,
                   total_assets, total_equity, retained_earnings
            FROM Company_Financial 
            WHERE biz_no = ? 
            ORDER BY fiscal_year DESC 
            LIMIT 3
        ''', (biz_no,))
        
        financials = []
        for row in cursor.fetchall():
            financials.append({
                "year": row[0] or "",
                "sales_revenue": row[1] or 0,
                "operating_income": row[2] or 0,
                "net_income": row[3] or 0,
                "total_assets": row[4] or 0,
                "total_equity": row[5] or 0,
                "retained_earnings": row[6] or 0
            })
        
        # 접촉이력 (최근 20건)
        cursor.execute('''
            SELECT contact_datetime, contact_type, contact_person, memo, registered_by
            FROM Contact_History 
            WHERE biz_no = ? 
            ORDER BY contact_datetime DESC 
            LIMIT 20
        ''', (biz_no,))
        
        contact_history = []
        contact_type_counts = {}
        for row in cursor.fetchall():
            contact_type = row[1] or "기타"
            contact_history.append({
                "datetime": row[0] or "",
                "type": contact_type,
                "person": row[2] or "",
                "memo": row[3] or "",
                "registered_by": row[4] or ""
            })
            contact_type_counts[contact_type] = contact_type_counts.get(contact_type, 0) + 1
        
        return jsonify({
            "success": True,
            "data": {
                "company_info": company_info,
                "shareholders": shareholders,
                "financials": financials,
                "contact_history": contact_history,
                "contact_type_summary": contact_type_counts
            }
        })
        
    except Exception as e:
        print(f"기업 분석 데이터 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# =======================================================
# 대표자 및 주주 정보 수정 API 엔드포인트
# =======================================================


@app.route('/api/update-ceo-name', methods=['POST'])
def update_ceo_name():
    """대표자 이름 업데이트 API"""
    try:
        data = request.get_json()
        biz_no = data.get('biz_no')
        new_ceo_name = data.get('new_ceo_name')
        
        if not biz_no or not new_ceo_name:
            return jsonify({'success': False, 'message': '필수 파라미터가 누락되었습니다.'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Company_Basic 테이블에서 대표자명 업데이트
        cursor.execute('''
            UPDATE Company_Basic
            SET representative_name = ?
            WHERE biz_no = ?
        ''', (new_ceo_name, biz_no))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '대표자명이 성공적으로 업데이트되었습니다.'})
    
    except Exception as e:
        print(f"대표자명 업데이트 오류: {e}")
        return jsonify({'success': False, 'message': f'업데이트 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/update_representative_name', methods=['POST'])
def update_representative_name_api():
    """대표자 이름 업데이트 API (detail.html용)"""
    try:
        data = request.get_json()
        biz_no = data.get('biz_no')
        representative_name = data.get('representative_name')
        
        if not biz_no or not representative_name:
            return jsonify({'success': False, 'message': '필수 파라미터가 누락되었습니다.'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Company_Basic 테이블에서 대표자명 업데이트
        cursor.execute('''
            UPDATE Company_Basic
            SET representative_name = ?
            WHERE biz_no = ?
        ''', (representative_name, biz_no))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '대표자명이 성공적으로 업데이트되었습니다.'})
    
    except Exception as e:
        print(f"대표자명 업데이트 오류: {e}")
        return jsonify({'success': False, 'message': f'업데이트 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/update-shareholder', methods=['POST'])
def update_shareholder():
    """주주명 업데이트 API"""
    try:
        data = request.get_json()
        biz_no = data.get('biz_no')
        old_shareholder_name = data.get('old_shareholder_name')
        new_shareholder_name = data.get('new_shareholder_name')
        
        if not biz_no or not old_shareholder_name or not new_shareholder_name:
            return jsonify({'success': False, 'message': '필수 파라미터가 누락되었습니다.'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Company_Shareholder 테이블에서 주주명 업데이트
        cursor.execute('''
            UPDATE Company_Shareholder
            SET shareholder_name = ?
            WHERE biz_no = ? AND shareholder_name = ?
        ''', (new_shareholder_name, biz_no, old_shareholder_name))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '주주명이 성공적으로 업데이트되었습니다.'})
    
    except Exception as e:
        print(f"주주명 업데이트 오류: {e}")
        return jsonify({'success': False, 'message': f'업데이트 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/update-share-count', methods=['POST'])
def update_share_count():
    """수식수 업데이트 API"""
    try:
        data = request.get_json()
        biz_no = data.get('biz_no')
        shareholder_name = data.get('shareholder_name')
        new_share_count = data.get('new_share_count')
        
        if not biz_no or not shareholder_name or new_share_count is None:
            return jsonify({'success': False, 'message': '필수 파라미터가 누락되었습니다.'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Company_Shareholder 테이블에서 수식수 업데이트
        cursor.execute('''
            UPDATE Company_Shareholder
            SET share_count = ?
            WHERE biz_no = ? AND shareholder_name = ?
        ''', (new_share_count, biz_no, shareholder_name))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '수식수가 성공적으로 업데이트되었습니다.'})
    
    except Exception as e:
        print(f"수식수 업데이트 오류: {e}")
        return jsonify({'success': False, 'message': f'업데이트 중 오류가 발생했습니다: {str(e)}'}), 500


# ============================================
# YS Honers 페이지 라우트
# ============================================

@app.route('/lys')
def lys_main():
    """YS Honers 메인 페이지"""
    conn = get_db_connection()
    try:
        # 팀원 정보 조회
        team_members = conn.execute('''
            SELECT * FROM ys_team_members ORDER BY display_order
        ''').fetchall()
        
        # 뉴스 정보 조회 (최신 6개)
        news_items = conn.execute('''
            SELECT * FROM ys_news ORDER BY publish_date DESC, id DESC LIMIT 6
        ''').fetchall()
        
        # 세미나 정보 조회 (미래 일정 순)
        seminars_rows = conn.execute('''
            SELECT * FROM ys_seminars 
            ORDER BY date ASC, time ASC
        ''').fetchall()
        
        seminars = []
        for row in seminars_rows:
            seminar = dict(row)
            # 해당 세미나의 세션 조회
            sessions = conn.execute('''
                SELECT * FROM ys_seminar_sessions 
                WHERE seminar_id = ? 
                ORDER BY display_order ASC, id ASC
            ''', (seminar['id'],)).fetchall()
            seminar['sessions'] = [dict(s) for s in sessions]
            seminars.append(seminar)
        
        # 카운트 정보 조회
        try:
            seminar_count = conn.execute('SELECT COUNT(*) FROM SeminarRegistrations').fetchone()[0]
        except:
            seminar_count = 0
            
        try:
            inquiry_count = conn.execute('SELECT COUNT(*) FROM ys_inquiries').fetchone()[0]
        except:
            inquiry_count = 0
            
        counts = {
            'seminar': seminar_count,
            'inquiry': inquiry_count
        }
        
        return render_template('lys_main.html', 
                               team_members=[dict(row) for row in team_members],
                               news_items=[dict(row) for row in news_items],
                               seminars=[dict(row) for row in seminars],
                               counts=counts)
    except Exception as e:
        print(f"LYS 메인 페이지 오류: {e}")
        # 오류 시 빈 데이터로 렌더링 (크래시 방지)
        return render_template('lys_main.html', 
                               team_members=[], 
                               news_items=[], 
                               seminars=[], 
                               counts={'seminar': 0, 'inquiry': 0})
    finally:
        conn.close()

@app.route('/api/seminar/register', methods=['POST'])
def register_seminar_api():
    """세미나 참가 신청 API"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "데이터가 없습니다."}), 400
            
        required_fields = ['seminar_title', 'name', 'phone', 'biz_no']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "message": f"필수 항목이 누락되었습니다: {field}"}), 400
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO SeminarRegistrations 
                (seminar_title, name, phone, company_name, position, biz_no)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['seminar_title'],
                data['name'],
                data['phone'],
                data.get('company_name', ''),
                data.get('position', ''),
                data['biz_no']
            ))
            conn.commit()
            return jsonify({"success": True, "message": "세미나 참가 신청이 완료되었습니다."})
        except Exception as e:
            conn.rollback()
            return jsonify({"success": False, "message": f"데이터베이스 오류: {str(e)}"}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({"success": False, "message": f"서버 오류: {str(e)}"}), 500

# --- LYS ADMIN ROUTES START ---
@app.route('/lys/admin/seminars')
def lys_admin_seminars():
    """세미나 관리 페이지"""
    if not session.get('lys_admin_auth'):
        return redirect('/lys/admin')
        
    conn = get_db_connection()
    try:
        seminars = conn.execute('SELECT * FROM ys_seminars ORDER BY date DESC').fetchall()
        return render_template('lys_admin_seminars.html', seminars=[dict(row) for row in seminars])
    except Exception as e:
        print(f"세미나 관리 오류: {e}")
        return str(e), 500
    finally:
        conn.close()

@app.route('/lys/admin/seminars/add', methods=['POST'])
def lys_admin_add_seminar():
    """세미나 추가"""
    if not session.get('lys_admin_auth'):
        return redirect('/lys/admin')

    try:
        title = request.form.get('title')
        date = request.form.get('date')
        time = request.form.get('time')
        location = request.form.get('location')
        description = request.form.get('description')
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO ys_seminars (title, date, time, location, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, date, time, location, description))
        conn.commit()
        conn.close()
        return redirect('/lys/admin/seminars')
    except Exception as e:
        return f"Error: {e}"

@app.route('/api/lys/seminar-registration/<int:id>/delete', methods=['POST'])
def api_lys_delete_registration(id):
    """세미나 신청 내역 삭제"""
    if not session.get('lys_admin_auth'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM SeminarRegistrations WHERE id = ?', (id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"세미나 신청 삭제 오류: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/lys/admin/seminars/<int:id>/delete', methods=['POST'])
def lys_admin_delete_seminar(id):
    if not session.get('lys_admin_auth'): return redirect('/lys/admin')
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM ys_seminars WHERE id = ?', (id,))
        conn.commit()
    finally:
        conn.close()
    return redirect('/lys/admin/seminars')

@app.route('/lys/admin/registrations')
def lys_admin_registrations():
    """세미나 신청자 관리 페이지"""
    if not session.get('lys_admin_auth'):
        return redirect('/lys/admin')
        
    conn = get_db_connection()
    try:
        registrations = conn.execute('''
            SELECT * FROM SeminarRegistrations ORDER BY created_at DESC
        ''').fetchall()
        return render_template('lys_admin_registrations.html', registrations=[dict(row) for row in registrations])
    finally:
        conn.close()

@app.route('/lys/admin/registrations/<int:id>/delete', methods=['POST'])
def lys_admin_delete_registration(id):
    if not session.get('lys_admin_auth'): return redirect('/lys/admin')
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM SeminarRegistrations WHERE id = ?', (id,))
        conn.commit()
    finally:
        conn.close()
    return redirect('/lys/admin/registrations')

@app.route('/lys/admin/questions', methods=['GET', 'POST'])
def lys_admin_questions():
    """진단 질문 관리 페이지"""
    if not session.get('lys_admin_auth'):
        return redirect('/lys/admin')
        
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            question_text = request.form['question']
            q_type = request.form['type']
            # Get next display order
            max_order = conn.execute('SELECT MAX(display_order) FROM ys_questions').fetchone()[0] or 0
            
            conn.execute('''
                INSERT INTO ys_questions (question_text, type, display_order, is_active)
                VALUES (?, ?, ?, 1)
            ''', (question_text, q_type, max_order + 1))
            conn.commit()
            return redirect('/lys/admin/questions')
            
        questions = conn.execute('SELECT * FROM ys_questions ORDER BY display_order ASC').fetchall()
        return render_template('lys_admin_questions.html', questions=[dict(row) for row in questions])
    finally:
        conn.close()

@app.route('/lys/admin/questions/reorder', methods=['POST'])
def lys_admin_reorder_questions():
    if not session.get('lys_admin_auth'): return jsonify({'success': False}), 403
    try:
        order_data = request.json['order'] # List of IDs in new order
        conn = get_db_connection()
        for index, q_id in enumerate(order_data):
            conn.execute('UPDATE ys_questions SET display_order = ? WHERE id = ?', (index + 1, q_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/lys/admin/questions/<int:id>/delete', methods=['POST'])
def lys_admin_delete_question(id):
    if not session.get('lys_admin_auth'): return redirect('/lys/admin')
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM ys_questions WHERE id = ?', (id,))
        conn.commit()
    finally:
        conn.close()
    return redirect('/lys/admin/questions')
# --- LYS ADMIN ROUTES END ---

@app.route('/lys/inquiry')
def lys_inquiry():
    """YS Honers 상담신청 페이지"""
    conn = get_db_connection()
    try:
        questions = conn.execute('''
            SELECT * FROM ys_questions WHERE is_active = 1 ORDER BY display_order
        ''').fetchall()
        return render_template('lys_inquiry.html', questions=[dict(q) for q in questions])
    except Exception as e:
        print(f"질문 조회 오류: {e}")
        return render_template('lys_inquiry.html', questions=[])
    finally:
        conn.close()

@app.route('/lys/admin', methods=['GET', 'POST'])
def lys_admin():
    """YS Honers 관리자 페이지"""
    # 비밀번호 인증
    ADMIN_PASSWORD = 'admin1234!'
    
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['lys_admin_auth'] = True
        else:
            return render_template('lys_admin_login.html', error='비밀번호가 올바르지 않습니다.')
    
    # 인증 확인
    if not session.get('lys_admin_auth'):
        return render_template('lys_admin_login.html', error=None)
    
    conn = get_db_connection()
    try:
        # 팀원 정보 조회
        team_members = conn.execute('''
            SELECT * FROM ys_team_members ORDER BY display_order
        ''').fetchall()
        
        # 뉴스 정보 조회
        news_items = conn.execute('''
            SELECT * FROM ys_news ORDER BY display_order, id
        ''').fetchall()
        
        # 세미나 정보 조회 (세션 포함)
        seminars_rows = conn.execute('''
            SELECT * FROM ys_seminars ORDER BY date DESC
        ''').fetchall()
        
        seminars = []
        for row in seminars_rows:
            s_dict = dict(row)
            sessions = conn.execute('SELECT * FROM ys_seminar_sessions WHERE seminar_id = ? ORDER BY display_order', (s_dict['id'],)).fetchall()
            s_dict['sessions'] = [dict(sess) for sess in sessions]
            seminars.append(s_dict)
        
        # 상담 문의 조회
        inquiries_raw = conn.execute('''
            SELECT * FROM ys_inquiries ORDER BY created_at DESC
        ''').fetchall()
        
        # 세미나 신청자 조회 (새로 추가)
        registrations = conn.execute('''
            SELECT * FROM SeminarRegistrations ORDER BY created_at DESC
        ''').fetchall()

        # 질문 목록 조회
        quiz_questions = conn.execute('''
            SELECT * FROM ys_questions ORDER BY display_order
        ''').fetchall()
        
        # 체크리스트 JSON 파싱
        import json
        inquiries = []
        for inq in inquiries_raw:
            inq_dict = dict(inq)
            if inq_dict.get('checklist'):
                try:
                    inq_dict['checklist_parsed'] = json.loads(inq_dict['checklist'])
                except:
                    inq_dict['checklist_parsed'] = []
            else:
                inq_dict['checklist_parsed'] = []
            inquiries.append(inq_dict)
        
        # 문의 확인 처리 (새 문의를 read로 변경)
        conn.execute('''
            UPDATE ys_inquiries SET status = 'read' WHERE status = 'new' OR status IS NULL
        ''')
        conn.commit()
        
        return render_template('lys_admin.html',
                               team_members=[dict(row) for row in team_members],
                               news_items=[dict(row) for row in news_items],
                               seminars=[dict(row) for row in seminars], 
                               inquiries=inquiries,
                               registrations=[dict(row) for row in registrations],
                               quiz_questions=[dict(row) for row in quiz_questions])
    except Exception as e:
        print(f"LYS 관리자 페이지 오류: {e}")
        return render_template('lys_admin.html', team_members=[], news_items=[], inquiries=[], quiz_questions=[])
    finally:
        conn.close()

@app.route('/lys/admin/logout')
def lys_admin_logout():
    """관리자 로그아웃"""
    session.pop('lys_admin_auth', None)
    return redirect('/lys')

@app.route('/api/lys/questions/export')
def api_lys_export_questions():
    """질문 데이터 내보내기 (JSON)"""
    if not session.get('lys_admin_auth'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    try:
        import json
        questions = conn.execute('SELECT * FROM ys_questions ORDER BY display_order').fetchall()
        data = [dict(row) for row in questions]
        
        # JSON 파일로 반환
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return Response(
            json_str,
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment;filename=questions_backup.json'}
        )
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/lys/questions/import', methods=['POST'])
def api_lys_import_questions():
    """질문 데이터 가져오기 (JSON)"""
    if not session.get('lys_admin_auth'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
        
    try:
        import json
        data = json.load(file)
        
        if not isinstance(data, list):
             return jsonify({'success': False, 'message': 'Invalid format: Expected a list of questions'}), 400
             
        conn = get_db_connection()
        # 트랜잭션 시작 (기존 데이터 삭제 후 삽입)
        try:
            conn.execute('BEGIN TRANSACTION')
            conn.execute('DELETE FROM ys_questions')
            
            for q in data:
                # 필수 필드 확인
                if 'question_text' not in q:
                    continue
                
                conn.execute('''
                    INSERT INTO ys_questions (question_text, display_order, is_active)
                    VALUES (?, ?, ?)
                ''', (q.get('question_text'), q.get('display_order', 0), q.get('is_active', 1)))
                
            conn.commit()
            return jsonify({'success': True, 'message': f'Successfully imported {len(data)} questions.'})
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/lys/team')
def lys_team():
    """YS Honers 전문가 소개 페이지"""
    conn = get_db_connection()
    try:
        team_members = conn.execute('''
            SELECT * FROM ys_team_members ORDER BY display_order
        ''').fetchall()
        return render_template('lys_team.html', 
                               team_members=[dict(row) for row in team_members])
    except Exception as e:
        print(f"LYS 팀 페이지 오류: {e}")
        return render_template('lys_team.html', team_members=[])
    finally:
        conn.close()

# ============================================
# YS Honers API 엔드포인트
# ============================================

@app.route('/api/lys/team', methods=['GET', 'POST', 'PUT'])
def api_lys_team():
    """팀원 정보 API"""
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            team_members = conn.execute('''
                SELECT * FROM ys_team_members ORDER BY display_order
            ''').fetchall()
            return jsonify({'success': True, 'data': [dict(row) for row in team_members]})
        
        elif request.method == 'POST':
            data = request.get_json()
            conn.execute('''
                INSERT INTO ys_team_members (name, position, phone, bio, photo_url, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data.get('name'), data.get('position'), data.get('phone'),
                  data.get('bio'), data.get('photo_url'), data.get('display_order', 1)))
            conn.commit()
            return jsonify({'success': True, 'message': '팀원이 추가되었습니다.'})
        
        elif request.method == 'PUT':
            data = request.get_json()
            conn.execute('''
                UPDATE ys_team_members 
                SET name=?, position=?, phone=?, bio=?, photo_url=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (data.get('name'), data.get('position'), data.get('phone'),
                  data.get('bio'), data.get('photo_url'), data.get('id')))
            conn.commit()
            return jsonify({'success': True, 'message': '팀원 정보가 업데이트되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/lys/team/<int:team_id>', methods=['DELETE'])
def api_lys_team_delete(team_id):
    """팀원 삭제 API"""
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM ys_team_members WHERE id=?', (team_id,))
        conn.commit()
        return jsonify({'success': True, 'message': '팀원이 삭제되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/lys/news', methods=['GET', 'POST', 'PUT'])
def api_lys_news():
    """뉴스 API"""
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            news_items = conn.execute('''
                SELECT * FROM ys_news ORDER BY publish_date DESC, id DESC
            ''').fetchall()
            return jsonify({'success': True, 'data': [dict(row) for row in news_items]})
        
        elif request.method == 'POST':
            data = request.get_json()
            conn.execute('''
                INSERT INTO ys_news (title, category, summary, link_url, publish_date, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data.get('title'), data.get('category'), data.get('summary'),
                  data.get('link_url'), data.get('publish_date'), data.get('display_order', 1)))
            conn.commit()
            return jsonify({'success': True, 'message': '뉴스가 추가되었습니다.'})
        
        elif request.method == 'PUT':
            data = request.get_json()
            conn.execute('''
                UPDATE ys_news 
                SET title=?, category=?, summary=?, link_url=?, publish_date=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (data.get('title'), data.get('category'), data.get('summary'),
                  data.get('link_url'), data.get('publish_date'), data.get('id')))
            conn.commit()
            return jsonify({'success': True, 'message': '뉴스가 업데이트되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/lys/news/<int:news_id>', methods=['DELETE'])
def api_lys_news_delete(news_id):
    """뉴스 삭제 API"""
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM ys_news WHERE id=?', (news_id,))
        conn.commit()
        return jsonify({'success': True, 'message': '뉴스가 삭제되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/lys/seminar/<int:seminar_id>', methods=['DELETE'])
def api_lys_seminar_delete(seminar_id):
    """세미나 삭제 API"""
    if not session.get('lys_admin_auth'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM ys_seminars WHERE id = ?', (seminar_id,))
        conn.commit()
        return jsonify({'success': True, 'message': '세미나가 삭제되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/lys/inquiry', methods=['GET', 'POST'])
def api_lys_inquiry():
    """상담 문의 API"""
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            inquiries = conn.execute('''
                SELECT * FROM ys_inquiries ORDER BY created_at DESC
            ''').fetchall()
            return jsonify({'success': True, 'data': [dict(row) for row in inquiries]})
        
        elif request.method == 'POST':
            data = request.get_json()
            import json
            checklist = json.dumps(data.get('checklist', []), ensure_ascii=False) if data.get('checklist') else None
            
            conn.execute('''
                INSERT INTO ys_inquiries (name, company, phone, checklist, content, status)
                VALUES (?, ?, ?, ?, ?, 'new')
            ''', (data.get('name'), data.get('company'), data.get('phone'),
                  checklist, data.get('content')))
            conn.commit()
            return jsonify({'success': True, 'message': '상담 문의가 등록되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/lys/inquiry/<int:inquiry_id>', methods=['DELETE'])
def api_lys_inquiry_delete(inquiry_id):
    """상담 문의 삭제 API"""
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM ys_inquiries WHERE id=?', (inquiry_id,))
        conn.commit()
        return jsonify({'success': True, 'message': '문의가 삭제되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/lys/upload', methods=['POST'])
def api_lys_upload():
    """이미지 업로드 API"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '파일이 선택되지 않았습니다.'}), 400
        
        # 파일 저장
        import uuid
        filename = f"{int(time.time() * 1000)}-{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True, 
            'message': '파일이 업로드되었습니다.',
            'url': f'/uploads/{filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """업로드된 파일 제공"""
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Helper: Fetch OG Image
def _fetch_og_image(url):
    """URL에서 OG:Image 메타 태그를 추출합니다 (네이버 블로그 지원)."""
    if not url: return None
    if not url.startswith('http'): return None
    
    try:
        # User-Agent 설정 (봇 차단 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # 네이버 블로그 Iframe 처리
        if "blog.naver.com" in url:
            iframe = soup.find('iframe', id='mainFrame')
            if iframe:
                iframe_src = iframe.get('src')
                if iframe_src:
                    if iframe_src.startswith("/"):
                        iframe_src = "https://blog.naver.com" + iframe_src
                    # 내부 프레임 내용 재요청
                    response = requests.get(iframe_src, headers=headers, timeout=5)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Body Image Priority (postfiles.pstatic.net) -> More reliable than blogthumb
        try:
            body_imgs = soup.find_all('img')
            for img in body_imgs:
                src = img.get('src')
                if src and 'postfiles.pstatic.net' in src and 'type=w' in src:
                    return src
        except:
            pass

        og_image = soup.find('meta', property='og:image')
        
        if og_image and og_image.get('content'):
            return og_image['content']
            
        # Twitter card fallback
        twitter_image = soup.find('meta', name='twitter:image')
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']
            
        return None
    except Exception as e:
        print(f"Error fetching OG image from {url}: {e}")
        return None

@app.route('/api/lys/save-all', methods=['POST'])
def api_lys_save_all():
    """전체 데이터 저장 API (팀원+뉴스)"""
    conn = get_db_connection()
    try:
        data = request.get_json()
        
        # 팀원 정보 업데이트
        if 'team' in data:
            for member in data['team']:
                if member.get('id'):
                    conn.execute('''
                        UPDATE ys_team_members 
                        SET name=?, position=?, phone=?, bio=?, photo_url=?, updated_at=CURRENT_TIMESTAMP
                        WHERE id=?
                    ''', (member.get('name'), member.get('position'), member.get('phone'),
                          member.get('bio'), member.get('photo_url'), member.get('id')))
        
        # 뉴스 정보 업데이트
        if 'news' in data:
            for news in data['news']:
                # 링크 URL 변경 시 또는 썸네일이 없을 때 이미지 자동 추출
                new_thumbnail_url = news.get('thumbnail_url')
                link_url = news.get('link_url')
                
                # 기존 데이터 조회 (URL 변경 확인용) - 최적화: ID가 있을 때만
                current_thumbnail = None
                current_link = None
                
                if news.get('id'):
                    row = conn.execute('SELECT link_url, thumbnail_url FROM ys_news WHERE id = ?', (news.get('id'),)).fetchone()
                    if row:
                        current_link = row[0]
                        current_thumbnail = row[1]
                
                # 썸네일 자동 업데이트 조건:
                # 1. 링크가 새로 입력되었거나 변경되었을 때
                # 2. 썸네일이 비어있고 링크가 있을 때
                should_fetch = False
                if link_url and (link_url != current_link):
                    should_fetch = True
                elif link_url and not current_thumbnail and not new_thumbnail_url:
                    should_fetch = True
                
                fetched_thumbnail = None
                if should_fetch:
                    print(f"Fetching OG image for: {link_url}")
                    fetched_thumbnail = _fetch_og_image(link_url)
                
                # 최종 저장할 썸네일 결정 (새로 가져온 것 > 입력된 것 > 기존 것)
                final_thumbnail = fetched_thumbnail or new_thumbnail_url or current_thumbnail
                
                if news.get('id'):
                    conn.execute('''
                        UPDATE ys_news 
                        SET title=?, category=?, summary=?, link_url=?, thumbnail_url=?, publish_date=?, updated_at=CURRENT_TIMESTAMP
                        WHERE id=?
                    ''', (news.get('title'), news.get('category'), news.get('summary'),
                          news.get('link_url'), final_thumbnail, news.get('publish_date'), news.get('id')))
                else:
                    # 신규 생성 시에도 썸네일 페치
                    if not final_thumbnail and link_url:
                        final_thumbnail = _fetch_og_image(link_url)
                        
                    conn.execute('''
                        INSERT INTO ys_news (title, category, summary, link_url, thumbnail_url, publish_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (news.get('title'), news.get('category'), news.get('summary'),
                          news.get('link_url'), final_thumbnail, news.get('publish_date')))
        
        # 세미나 정보 업데이트
        if 'seminars' in data:
            for seminar in data['seminars']:
                seminar_id = seminar.get('id')
                
                # 1. 세미나 기본 정보 저장/수정
                if seminar_id:
                    conn.execute('''
                        UPDATE ys_seminars 
                        SET title=?, date=?, time=?, location=?, description=?, max_attendees=?
                        WHERE id=?
                    ''', (seminar.get('title'), seminar.get('date'), seminar.get('time'),
                          seminar.get('location'), seminar.get('description'), 
                          seminar.get('max_attendees', 0), seminar_id))
                else:
                    cursor = conn.execute('''
                        INSERT INTO ys_seminars (title, date, time, location, description, max_attendees)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (seminar.get('title'), seminar.get('date'), seminar.get('time'),
                          seminar.get('location'), seminar.get('description'),
                          seminar.get('max_attendees', 0)))
                    seminar_id = cursor.lastrowid

                # 2. 세션 정보 저장 (전체 삭제 후 재등록 전략 - 간단한 구현)
                # 주의: 기존 세션 ID를 유지해야 한다면 로직이 복잡해짐. 여기서는 단순화를 위해 삭제 후 재삽입
                # 하지만, 세션 ID가 다른데 참조되지 않는다면 삭제 후 재삽입이 깔끔함.
                conn.execute('DELETE FROM ys_seminar_sessions WHERE seminar_id = ?', (seminar_id,))
                
                if 'sessions' in seminar and seminar['sessions']:
                    for session_item in seminar['sessions']:
                        conn.execute('''
                            INSERT INTO ys_seminar_sessions 
                            (seminar_id, time_range, title, speaker, description, location_note, display_order)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            seminar_id,
                            session_item.get('time_range', ''),
                            session_item.get('title', ''),
                            session_item.get('speaker', ''),
                            session_item.get('description', ''),
                            session_item.get('location_note', ''),
                            session_item.get('display_order', 1)
                        ))

        
        conn.commit()
        return jsonify({'success': True, 'message': '변경사항이 저장되었습니다.'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/lys/inquiry/unread-count')
def api_lys_inquiry_unread_count():
    """미확인 상담 문의 개수 조회 (ct0001, ct0002용)"""
    conn = get_db_connection()
    try:
        # 상태가 'new'인 문의 개수 조회
        result = conn.execute('''
            SELECT COUNT(*) as count FROM ys_inquiries WHERE status = 'new' OR status IS NULL
        ''').fetchone()
        count = result['count'] if result else 0
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'count': 0})
    finally:
        conn.close()

@app.route('/api/lys/inquiry/mark-read', methods=['POST'])
def api_lys_inquiry_mark_read():
    """모든 상담 문의를 확인함으로 표시"""
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE ys_inquiries SET status = 'read' WHERE status = 'new' OR status IS NULL
        ''')
        conn.commit()
        return jsonify({'success': True, 'message': '모든 문의가 확인 처리되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# --- 개인사업자(전단계) 관리 라우트 ---

@app.route('/individual_businesses')
def individual_business_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 검색 파라미터 가져오기
    company_name = request.args.get('company_name', '').strip()
    business_number = request.args.get('business_number', '').strip()
    address = request.args.get('address', '').strip()
    industry_type = request.args.get('industry_type', '').strip()
    financial_year = request.args.get('financial_year', '2024').strip() # 기본값 2024
    revenue_min = request.args.get('revenue_min', '').strip()
    revenue_max = request.args.get('revenue_max', '').strip()
    net_income_min = request.args.get('net_income_min', '').strip()
    net_income_max = request.args.get('net_income_max', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    status_filter = request.args.get('status', '전체').strip() # 접촉대기, 접촉중, 접촉해제, 완료  등
    
    # 페이징 파라미터
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        limit = 50
        offset = 0
        
    is_ajax = request.args.get('ajax', 'false').lower() == 'true'
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # 컬럼 존재 확인 및 추가 (assigned_user_id, status)
        cursor.execute("PRAGMA table_info(individual_business_owners)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'assigned_user_id' not in columns:
            cursor.execute("ALTER TABLE individual_business_owners ADD COLUMN assigned_user_id TEXT")
        if 'status' not in columns:
            cursor.execute("ALTER TABLE individual_business_owners ADD COLUMN status TEXT DEFAULT '접촉대기'")
        conn.commit()
        
        # 동적 SQL 쿼리 구성
        query = "SELECT * FROM individual_business_owners WHERE 1=1"
        params = []

        # === 프라이버시 및 상태 필터링 로직 ===
        # ct0001, ct0002는 모든 데이터 열람 가능
        if user_id in ['ct0001', 'ct0002']:
             pass # 제한 없음
        else:
            # 일반 사용자는 "다른 사람이 접촉중"인 건은 볼 수 없음
            # 즉, (assigned_user_id IS NULL) OR (assigned_user_id = 내아이디) OR (status = '접촉해제')
            # '접촉중'이면서 '다른 사람'인 것만 제외하면 됨
            query += " AND (assigned_user_id IS NULL OR assigned_user_id = ? OR status = '접촉해제')"
            params.append(user_id)

        # 상태 필터 (전체, 접촉대기, 접촉중, 접촉해제 등)
        if status_filter and status_filter != '전체':
            if status_filter == '접촉중':
                 # 내 접촉중인 것만 (일반 유저의 경우 위 조건과 결합되어 자연스럽게 내것만 나옴, 관리자는 전체 접촉중)
                 if user_id not in ['ct0001', 'ct0002']:
                     query += " AND status = '접촉중' AND assigned_user_id = ?"
                     params.append(user_id)
                 else:
                     query += " AND status = '접촉중'"
            else:
                 query += " AND status = ?"
                 params.append(status_filter)
        
        if company_name:
            query += " AND company_name LIKE ?"
            params.append(f'%{company_name}%')
        
        if business_number:
            query += " AND business_number LIKE ?"
            params.append(f'%{business_number}%')
        
        if address:
            query += " AND address LIKE ?"
            params.append(f'%{address}%')

        if industry_type:
            query += " AND industry_type LIKE ?"
            params.append(f'%{industry_type}%')
            
        if financial_year:
            query += " AND CAST(financial_year AS INTEGER) = ?"
            params.append(int(financial_year))
        
        if revenue_min:
            query += " AND CAST(revenue AS REAL) >= ?"
            params.append(float(revenue_min))
        
        if revenue_max:
            query += " AND CAST(revenue AS REAL) <= ?"
            params.append(float(revenue_max))
        
        if net_income_min:
            query += " AND CAST(net_income AS REAL) >= ?"
            params.append(float(net_income_min))
        
        if net_income_max:
            query += " AND CAST(net_income AS REAL) <= ?"
            params.append(float(net_income_max))
            
        if start_date:
            query += " AND date(created_at) >= date(?)"
            params.append(start_date)
            
        if end_date:
            query += " AND date(created_at) <= date(?)"
            params.append(end_date)
            
        # Debugging date search
        print(f"DEBUG SEARCH: Start={start_date}, End={end_date}, Params={params}")
        
        # Default sort by address (Zipcode + Address) as requested
        query += " ORDER BY address ASC LIMIT ? OFFSET ?"
        params.append(limit)
        params.append(offset)
        
        cursor.execute(query, params)
        businesses = cursor.fetchall()
        
        # AJAX 요청이면 JSON 반환
        if is_ajax:
            business_list = []
            for item in businesses:
                business_list.append({
                    'id': item['id'],
                    'business_number': item['business_number'],
                    'company_name': item['company_name'],
                    'status': item['status'], # 상태 추가
                    'representative_name': item['representative_name'],
                    'birth_year': item['birth_year'],
                    'address': item['address'],
                    'industry_type': item['industry_type'],
                    'establishment_year': item['establishment_year'],
                    'financial_year': item['financial_year'],
                    'revenue': item['revenue'],
                    'net_income': item['net_income'],
                    'created_at': item['created_at'][:10] if item['created_at'] else '',
                    'phone_number': item['phone_number']
                })
            return jsonify({'success': True, 'data': business_list})
        
        # 검색 파라미터를 템플릿에 전달
        search_params = {
            'company_name': company_name,
            'business_number': business_number,
            'address': address,
            'industry_type': industry_type,
            'financial_year': financial_year,
            'revenue_min': revenue_min,
            'revenue_max': revenue_max,
            'net_income_min': net_income_min,
            'net_income_max': net_income_max,
            'start_date': start_date,
            'end_date': end_date,
            'status': status_filter
        }
        
        return render_template('individual_list.html', businesses=businesses, search=search_params)
    except Exception as e:
        print(f"Error fetching individual businesses: {e}")
        return render_template('individual_list.html', businesses=[], error=str(e), search={})
    finally:
        conn.close()

@app.route('/individual_businesses/add', methods=['POST'])
def add_individual_business():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        data = request.form
        
        # 필수 필드 확인
        if not data.get('company_name'):
            return jsonify({'success': False, 'message': '기업명은 필수입니다.'})
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO individual_business_owners (
                    company_name, representative_name, birth_year, establishment_year,
                    is_family_shareholder, is_other_shareholder, industry_type,
                    financial_year, employee_count, total_assets, total_capital,
                    revenue, net_income, address, business_number, phone_number, fax_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('company_name'),
                data.get('representative_name'),
                data.get('birth_year'),
                data.get('establishment_year'),
                data.get('is_family_shareholder', 'N'),
                data.get('is_other_shareholder', 'N'),
                data.get('industry_type'),
                data.get('financial_year'),
                data.get('employee_count'),
                data.get('total_assets'),
                data.get('total_capital'),
                data.get('revenue'),
                data.get('net_income'),
                data.get('address'),
                data.get('business_number'),
                data.get('phone_number'),
                data.get('fax_number')
            ))
            conn.commit()
            return jsonify({'success': True, 'message': '등록되었습니다.'})
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'message': '이미 등록된 사업자번호입니다.'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/individual_businesses/upload', methods=['POST'])
def upload_individual_business_excel():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'})
        
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '파일이 없습니다.'})
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '선택된 파일이 없습니다.'})
        
    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(file)
            
            # 컬럼명 정리 (공백 제거)
            df.columns = [str(col).strip() for col in df.columns]
            print(f"엑셀 컬럼명: {list(df.columns)}")  # 디버깅용 로그
            
            # 컬럼명 정규화 함수 (공백, 특수문자 제거)
            def normalize_col(col):
                return col.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
            
            # 정규화된 컬럼명 매핑 생성
            normalized_cols = {normalize_col(col): col for col in df.columns}
            print(f"정규화된 컬럼명: {normalized_cols}")  # 디버깅용 로그
            
            # 컬럼 매핑 (엑셀 헤더 -> DB 컬럼) - 정규화된 이름으로 매핑
            column_map_normalized = {
                '기업명': 'company_name',
                '대표자명': 'representative_name',
                '출생년도': 'birth_year',
                '설립년도': 'establishment_year',
                '가족주주여부': 'is_family_shareholder',
                '타인주주여부': 'is_other_shareholder',
                '업종': 'industry_type',
                '재무제표연도': 'financial_year',
                '기준연도': 'financial_year',
                '종업원수': 'employee_count',
                '종업원수(명)': 'employee_count',
                '총자산': 'total_assets',
                '총자산(억)': 'total_assets',
                '자본총계': 'total_capital',
                '자본총계(억)': 'total_capital',
                '매출액': 'revenue',
                '매출액(억)': 'revenue',
                '당기순이익': 'net_income',
                '당기순이익(억)': 'net_income',
                '사업장주소': 'address',
                '사업자주소': 'address',
                '주소': 'address',
                '사업자번호': 'business_number',
                '전화번호': 'phone_number',
            }
            
            # 실제 엑셀 컬럼명을 기반으로 매핑 생성
            column_map = {}
            for norm_key, db_col in column_map_normalized.items():
                # 정규화된 키로 매칭
                if norm_key in normalized_cols:
                    column_map[normalized_cols[norm_key]] = db_col
                # 원본 컬럼에도 직접 확인
                for excel_col in df.columns:
                    if norm_key in normalize_col(excel_col):
                        column_map[excel_col] = db_col
            
            print(f"최종 매핑: {column_map}")  # 디버깅용 로그
            
            # 엑셀 헤더에 (억) 포함 여부 확인 (이미 억 단위인지)
            already_in_billion = any('(억)' in str(col) or '억' in str(col) for col in df.columns)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 테이블 존재 확인 및 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS individual_business_owners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    representative_name TEXT,
                    birth_year TEXT,
                    establishment_year TEXT,
                    is_family_shareholder TEXT,
                    is_other_shareholder TEXT,
                    industry_type TEXT,
                    financial_year TEXT,
                    employee_count TEXT,
                    total_assets TEXT,
                    total_capital TEXT,
                    revenue TEXT,
                    net_income TEXT,
                    address TEXT,
                    business_number TEXT,
                    phone_number TEXT,
                    fax_number TEXT,
                    memo TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            
            success_count = 0
            fail_count = 0
            first_error = None
            skip_count = 0
            
            for _, row in df.iterrows():
                try:
                    # 데이터 정리
                    data = {}
                    for kor_col, db_col in column_map.items():
                        if kor_col in row:
                            val = row[kor_col]
                            if pd.isna(val):
                                val = None
                            else:
                                # 년도 필드 처리 (.0 제거)
                                if db_col in ['birth_year', 'establishment_year', 'financial_year']:
                                    try:
                                        val = str(int(float(val)))
                                    except (ValueError, TypeError):
                                        val = str(val) if val else None
                                # 재무 데이터 처리
                                elif db_col in ['total_assets', 'total_capital', 'revenue', 'net_income']:
                                    try:
                                        num_val = float(val)
                                        # 이미 억 단위면 그대로, 아니면 변환
                                        if not already_in_billion:
                                            val = round(num_val / 100000000, 1)
                                        else:
                                            val = num_val  # 이미 억 단위
                                    except (ValueError, TypeError):
                                        val = None
                                # 종업원수 처리 (.0 제거)
                                elif db_col == 'employee_count':
                                    try:
                                        val = str(int(float(val)))
                                    except (ValueError, TypeError):
                                        val = str(val) if val else None
                            data[db_col] = val
                    
                    if not data.get('company_name'):
                        skip_count += 1
                        continue
                        
                    # 중복 확인 및 업데이트/삽입
                    cursor.execute("SELECT id FROM individual_business_owners WHERE business_number = ?", (data.get('business_number'),))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # 업데이트
                        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
                        values = list(data.values())
                        values.append(data.get('business_number'))
                        
                        cursor.execute(f'''
                            UPDATE individual_business_owners 
                            SET {set_clause}
                            WHERE business_number = ?
                        ''', values)
                    else:
                        # 삽입
                        data['created_at'] = '0001-01-01 00:00:00' # 초기 등록일은 맨 뒤로 가도록 설정
                        columns = ', '.join(data.keys())
                        placeholders = ', '.join(['?' for _ in data])
                        cursor.execute(f'''
                            INSERT INTO individual_business_owners ({columns})
                            VALUES ({placeholders})
                        ''', list(data.values()))
                        
                    success_count += 1
                except Exception as e:
                    print(f"Row processing error: {e}")
                    if first_error is None:
                        first_error = str(e)
                    fail_count += 1
                    
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True if success_count > 0 else False, 
                'message': f'총 {success_count}건 처리 완료 (실패 {fail_count}건, 스킵 {skip_count}건)' + (f' | 첫번째 오류: {first_error}' if first_error else '')
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'엑셀 처리 중 오류: {str(e)}'})
            
    return jsonify({'success': False, 'message': '엑셀 파일만 업로드 가능합니다.'})

# --- 개인사업자 상세 조회 및 메모/히스토리 API ---

@app.route('/individual_businesses/<int:id>/detail')
def get_individual_business_detail(id):
    """개인사업자 상세 정보, 메모, 히스토리 조회"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'})
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 컬럼 존재 확인 및 추가
        cursor.execute("PRAGMA table_info(individual_business_owners)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'assigned_user_id' not in columns:
            cursor.execute("ALTER TABLE individual_business_owners ADD COLUMN assigned_user_id TEXT")
        if 'status' not in columns:
            cursor.execute("ALTER TABLE individual_business_owners ADD COLUMN status TEXT DEFAULT '접촉대기'")
        if 'memo' not in columns:
            cursor.execute("ALTER TABLE individual_business_owners ADD COLUMN memo TEXT")
        
        # 히스토리 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS individual_business_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                type TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                FOREIGN KEY (business_id) REFERENCES individual_business_owners(id)
            )
        ''')
        
        # 히스토리 테이블 컬럼 확인 및 추가 (created_by 등)
        cursor.execute("PRAGMA table_info(individual_business_history)")
        h_cols = [c[1] for c in cursor.fetchall()]
        if 'created_by' not in h_cols:
             cursor.execute("ALTER TABLE individual_business_history ADD COLUMN created_by TEXT")
             
        conn.commit()
        
        # 데이터 조회
        cursor.execute("SELECT * FROM individual_business_owners WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'success': False, 'message': '기업 정보를 찾을 수 없습니다.'})

        memo = row['memo'] if row else ''
        status = row['status'] if 'status' in row.keys() and row['status'] else None
        assigned_user_id = row['assigned_user_id'] if 'assigned_user_id' in row.keys() else None
        
        # 히스토리 조회
        cursor.execute('''
            SELECT type, content, created_at, created_by FROM individual_business_history
            WHERE business_id = ? ORDER BY created_at DESC
        ''', (id,))
        history = [{'type': h['type'], 'content': h['content'], 'created_at': h['created_at'], 'created_by': h['created_by']} for h in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'data': {
                'memo': memo,
                'status': status,
                'assigned_user_id': assigned_user_id,
                'history': history
            }
        })
    except Exception as e:
        print(f"상세 조회 오류: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/individual_businesses/<int:id>/memo', methods=['POST'])
def save_individual_business_memo(id):
    """개인사업자 메모 및 상태 저장"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'})
    
    current_user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        memo = data.get('memo', '')
        new_status = data.get('status') # 상태 변경 요청이 있을 경우
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 현재 상태 및 담당자 조회
        cursor.execute("SELECT status, assigned_user_id FROM individual_business_owners WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'success': False, 'message': '기업 정보를 찾을 수 없습니다.'})

        current_status = row['status']
        assigned_user_id = row['assigned_user_id']
        
        updates = ["memo = ?"]
        params = [memo]
        
        # 상태 업데이트 로직
        if new_status and new_status != current_status:
            updates.append("status = ?")
            params.append(new_status)
            
            # 상태 변경 시 등록일(최근활동일) 갱신
            updates.append("created_at = CURRENT_TIMESTAMP")
            
            # 접촉중으로 변경 시, 담당자가 없으면 현재 사용자로 지정
            if new_status == '접촉중':
                if not assigned_user_id:
                    updates.append("assigned_user_id = ?")
                    params.append(current_user_id)
            
            # 접촉해제로 변경 시, 담당자를 유지할지 해제할지? 
            # -> 보통 해제하면 다른 사람이 가져갈 수 있어야 하므로 assigned_user_id를 NULL로 하거나, 
            #    그냥 '접촉해제' 상태로 두면 리스트 필터링에서 보이게 되므로(status='접촉해제') OK.
            #    여기서는 담당자 정보는 이력상 남겨두고 상태만 변경함. (다른 사람이 '접촉중'으로 변경 시 덮어써짐)
            
        params.append(id)
        
        cursor.execute(f"UPDATE individual_business_owners SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '저장되었습니다.'})
    except Exception as e:
        print(f"메모 저장 오류: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/individual_businesses/<int:id>/history', methods=['POST'])
def add_individual_business_history(id):
    """개인사업자 히스토리 추가 및 상태 변경"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'})
    
    current_user_id = session.get('user_id')
    current_user_name = session.get('user_name', current_user_id)
    
    try:
        data = request.get_json()
        history_type = data.get('type', '기타')
        content = data.get('content', '')
        new_status = data.get('status')
        
        if not content:
            return jsonify({'success': False, 'message': '내용을 입력해주세요.'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 히스토리 추가
        # created_by 컬럼이 있는지 확인 (history 테이블)
        cursor.execute("PRAGMA table_info(individual_business_history)")
        cols = [c[1] for c in cursor.fetchall()]
        if 'created_by' not in cols:
             cursor.execute("ALTER TABLE individual_business_history ADD COLUMN created_by TEXT")
        
        cursor.execute('''
            INSERT INTO individual_business_history (business_id, type, content, created_by)
            VALUES (?, ?, ?, ?)
        ''', (id, history_type, content, current_user_name))
        
        # 상태 업데이트 로직
        if new_status:
            cursor.execute("SELECT status, assigned_user_id FROM individual_business_owners WHERE id = ?", (id,))
            row = cursor.fetchone()
            if row:
                current_status = row['status']
                assigned_user_id = row['assigned_user_id']
                
                if new_status != current_status:
                    updates = ["status = ?"]
                    params = [new_status]
                    
                    # 상태 변경 시 등록일(최근활동일) 갱신
                    updates.append("created_at = CURRENT_TIMESTAMP")
                    
                    if new_status == '접촉중':
                        if not assigned_user_id:
                             updates.append("assigned_user_id = ?")
                             params.append(current_user_id)
                    elif new_status == '접촉중' and assigned_user_id and assigned_user_id != current_user_id:
                        # 이미 다른 담당자가 있는데 접촉중으로 바꾼다면? -> 강제 탈취 (마지막 접촉자 기준)
                        updates.append("assigned_user_id = ?")
                        params.append(current_user_id)
                        
                    params.append(id)
                    cursor.execute(f"UPDATE individual_business_owners SET {', '.join(updates)} WHERE id = ?", params)
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '히스토리가 추가되었습니다.'})
    except Exception as e:
        print(f"히스토리 추가 오류: {e}")
        return jsonify({'success': False, 'message': str(e)})



if __name__ == '__main__':


    print("=== 애플리케이션 시작 ===")
    print(f"Flask 앱 디렉터리: {app_dir}")
    print(f"데이터베이스 경로: {DB_PATH}")
    print(f"RENDER 환경변수: {os.environ.get('RENDER', 'N/A')}")
    print(f"PORT 환경변수: {os.environ.get('PORT', 'N/A')}")
    
    # 데이터베이스 파일 상태 확인
    if os.path.exists(DB_PATH):
        file_size = os.path.getsize(DB_PATH)
        print(f"? 데이터베이스 파일 존재: {DB_PATH} (크기: {file_size} bytes)")
    else:
        print(f"? 데이터베이스 파일 없음: {DB_PATH}")
    
# ==========================================
# LYS Feature Functions (Seminars & Blog)
# ==========================================
def init_lys_tables():
    conn = get_db_connection()
    try:
        # 세미나 테이블
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Seminars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                date TEXT,
                time TEXT,
                location TEXT,
                image_url TEXT,
                link_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 블로그/뉴스 테이블
        conn.execute('''
            CREATE TABLE IF NOT EXISTS BlogPosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT,
                summary TEXT,
                thumbnail_url TEXT,
                link_url TEXT,
                publish_date TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 세미나 신청자 테이블 (별도 관리)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS SeminarRegistrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seminar_title TEXT NOT NULL,
                name TEXT NOT NULL,
        }
        if 'naver.com' in url or 'pstatic.net' in url:
            headers['Referer'] = 'https://blog.naver.com/'

        # Stream=True for efficiency
        resp = requests.get(url, headers=headers, stream=True, timeout=10)
        resp.raise_for_status()
        
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
                   
        return Response(resp.content, resp.status_code, headers)
    except Exception as e:
        print(f"Proxy error for {url}: {e}")
        return "Error fetching image", 500
if __name__ == '__main__':
    # 앱 시작 시 테이블 초기화
    print("\n=== 데이터베이스 테이블 초기화 ===")
    try:
        init_user_tables()
        print("? 사용자 테이블 초기화 완료")
    except Exception as e:
        print(f"? 사용자 테이블 초기화 실패: {e}")
    
    try:
        init_business_tables()
        print("? 비즈니스 테이블 초기화 완료")
    except Exception as e:
        print(f"? 비즈니스 테이블 초기화 실패: {e}")
    
    try:
        init_pipeline_tables()
        print("? 영업 파이프라인 테이블 초기화 완료")
    except Exception as e:
        print(f"? 영업 파이프라인 테이블 초기화 실패: {e}")
    
    try:
        init_ys_honers_tables()
        print("? YS Honers 테이블 초기화 완료")
    except Exception as e:
        print(f"? YS Honers 테이블 초기화 실패: {e}")
    
    try:
        init_individual_business_tables()
        print("? 개인사업자 테이블 초기화 완료")
    except Exception as e:
        print(f"? 개인사업자 테이블 초기화 실패: {e}")

    try:
        init_lys_tables()
        print("? LYS 테이블 초기화 완료")
    except Exception as e:
        print(f"? LYS 테이블 초기화 실패: {e}")
    
    # 서버 시작
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=== Flask 서버 시작 ===")
    print(f"Host: 0.0.0.0")
    print(f"Port: {port}")
    print(f"Debug: {not os.environ.get('RENDER')}")  # Render에서는 debug=False
    
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=not os.environ.get('RENDER')  # Render에서는 debug=False
    )