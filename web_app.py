# -*- coding: cp949 -*-
# Company Management System
import os
import sqlite3
import io
import time
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, Response, send_file
from datetime import datetime
import pytz
import pandas as pd
import math
import csv
from werkzeug.utils import secure_filename
from jinja2 import FileSystemLoader, TemplateNotFound

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_kst_now():
    """한국 시간 현재 시각을 반환합니다."""
    return datetime.now(KST)
import pytz
from datetime import timezone, timedelta

# --- 커스텀 템플릿 로더 (CP949 지원) ---
class CP949FileSystemLoader(FileSystemLoader):
    def get_source(self, environment, template):
        # 파일 경로 찾기
        for searchpath in self.searchpath:
            filename = os.path.join(searchpath, template)
            if os.path.exists(filename):
                # CP949로 먼저 시도, 실패하면 UTF-8로 시도
                try:
                    with open(filename, 'r', encoding='cp949') as f:
                        source = f.read()
                except UnicodeDecodeError:
                    with open(filename, 'r', encoding='utf-8') as f:
                        source = f.read()
                
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
app.jinja_loader = CP949FileSystemLoader(template_dir)

# DB 경로 설정 (Render Persistent Disk 사용)
app_dir = os.path.dirname(os.path.abspath(__file__))

# render.com에서는 환경변수 RENDER가 설정됨
if os.environ.get('RENDER'):
    # render.com 서버 환경 - Persistent Disk 사용
    persistent_disk_path = '/var/data'
    
    # Persistent Disk 디렉터리 확인 및 생성
    if os.path.exists(persistent_disk_path):
        # Persistent Disk가 마운트된 경우
        DB_PATH = os.path.join(persistent_disk_path, 'company_database.db')
        print(f"Using Persistent Disk DB: {DB_PATH}")
    else:
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
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        # 연결 실패 시 메모리 DB로 폴백 (임시 조치)
        print("Falling back to in-memory database")
        conn = sqlite3.connect(':memory:', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

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
    # 하드코딩된 관리자 계정 (긴급 접속용)
    if user_id == 'yangch' and password == 'yang1123!':
        return {
            'user_id': 'yangch',
            'password': 'yang1123!',
            'name': '양철호(관리자)',
            'user_level': 'V',
            'user_level_name': '메인관리자',
            'branch_code': 'ADMIN',
            'branch_name': '시스템관리',
            'phone': '010-0000-0000',
            'status': 'ACTIVE'
        }
    
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
                    'days_remaining': days_remaining
                }
        
        return None
    finally:
        conn.close()

@app.route('/')
def index():
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # 구독 정보 조회
    subscription_info = get_user_subscription_info(session.get('user_id'))
    
    # 사용자 권한 정보를 템플릿에 전달
    user_data = {
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
                # M(매니저), N(일반담당자)는 본인 등록건만 조회
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
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page
        
        all_data = query_companies_data(request.args)
        total_rows = len(all_data)
        
        has_next_page = total_rows > (offset + per_page)
        
        paginated_data = all_data.iloc[offset : offset + per_page].where(pd.notnull(all_data), None)
        
        return jsonify({
            'companies': paginated_data.to_dict('records'),
            'hasNextPage': has_next_page,
            'offset': offset,
            'totalRows': total_rows
        })
    except Exception as e:
        print(f"Error in get_companies: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/export_excel')
def export_excel():
    if not session.get('logged_in'):
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
def company_detail(biz_no):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
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

@app.route('/api/contact_history', methods=['POST', 'PUT'])
def handle_contact_history():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    
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
            conn.execute(
                "UPDATE Contact_History SET contact_datetime=?, contact_type=?, contact_person=?, memo=?, registered_by=? WHERE history_id = ?", 
                (formatted_datetime, contact_type, contact_person, memo, user_id, history_id)
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
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM Contact_History WHERE history_id = ?", (history_id,))
        conn.commit()
        return jsonify({"success": True})
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_level = session.get('user_level', 'N')
    if not check_permission(user_level, 'S'):  # 서브관리자 이상만 접근 가능
        return "접근 권한이 없습니다.", 403
    
    return render_template('user_management.html', user_name=session.get('user_name'))

# --- 사용자 목록 API ---
@app.route('/api/users')
def get_users():
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
        
        # 파일 업로드 처리
        receipt_filename = None
        if 'receipt_file' in request.files:
            file = request.files['receipt_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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
    if not session.get('logged_in'):
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

if __name__ == '__main__':
    # 앱 시작 시 테이블 초기화
    init_user_tables()
    init_business_tables()
    app.run(host='0.0.0.0', port=5000, debug=True)