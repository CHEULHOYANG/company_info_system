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

# �ѱ� �ð��� ����
KST = pytz.timezone('Asia/Seoul')

def get_kst_now():
    """�ѱ� �ð� ���� �ð��� ��ȯ�մϴ�."""
    return datetime.now(KST)
import pytz
from datetime import timezone, timedelta

# --- Ŀ���� ���ø� �δ� (CP949 ����) ---
class CP949FileSystemLoader(FileSystemLoader):
    def get_source(self, environment, template):
        # ���� ��� ã��
        for searchpath in self.searchpath:
            filename = os.path.join(searchpath, template)
            if os.path.exists(filename):
                # CP949�� ���� �õ�, �����ϸ� UTF-8�� �õ�
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

# --- �⺻ ���� ---
app = Flask(__name__)
app.secret_key = 'your_very_secret_key_12345'

# ���ε� ���� ����
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# �ѱ� �ð��� ����
KST = pytz.timezone('Asia/Seoul')

# ���� �ѱ� �ð��� ��ȯ�ϴ� �Լ�
def get_kst_now():
    """���� �ѱ� �ð��� ��ȯ�մϴ�."""
    return datetime.now(KST)

def format_kst_datetime(dt_str=None):
    """�ѱ� �ð���� �����õ� ���� �ð� ���ڿ��� ��ȯ�մϴ�."""
    if dt_str:
        # �Էµ� �ð��� ������ �ѱ� �ð���� ��ȯ
        try:
            if isinstance(dt_str, str):
                # ISO ���� ���ڿ� �Ľ�
                if 'T' in dt_str:
                    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                    dt = dt.replace(tzinfo=pytz.UTC)
                
                # UTC���� KST�� ��ȯ
                kst_dt = dt.astimezone(KST)
                return kst_dt.strftime('%Y-%m-%d %H:%M:%S')
            return dt_str
        except:
            return dt_str
    else:
        # ���� �ѱ� �ð� ��ȯ
        return get_kst_now().strftime('%Y-%m-%d %H:%M:%S')

# Ŀ���� ���ø� �δ� ����
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.jinja_loader = CP949FileSystemLoader(template_dir)

# DB ��� ���� (Render Persistent Disk ���)
app_dir = os.path.dirname(os.path.abspath(__file__))

# render.com������ ȯ�溯�� RENDER�� ������
if os.environ.get('RENDER'):
    # render.com ���� ȯ�� - Persistent Disk ���
    persistent_disk_path = '/var/data'
    
    # Persistent Disk ���͸� Ȯ�� �� ����
    if os.path.exists(persistent_disk_path):
        # Persistent Disk�� ����Ʈ�� ���
        DB_PATH = os.path.join(persistent_disk_path, 'company_database.db')
        print(f"Using Persistent Disk DB: {DB_PATH}")
    else:
        # Persistent Disk�� ���� ��� (���� ���� ����)
        # 1����: ���� DB ������ ������ ��� ��� (������ ����)
        existing_db = os.path.join(app_dir, 'company_database.db')
        if os.path.exists(existing_db):
            DB_PATH = existing_db
            print(f"Using existing DB (no persistent disk): {DB_PATH}")
        else:
            # 2����: ���� DB�� ������ data ������ ���� ����
            db_dir = os.path.join(app_dir, 'data')
            os.makedirs(db_dir, exist_ok=True)
            DB_PATH = os.path.join(db_dir, 'company_info.db')
            print(f"Creating new DB (no persistent disk): {DB_PATH}")
else:
    # ���� ���� ȯ�� - ���� ���� ���
    DB_PATH = os.path.join(app_dir, 'company_database.db')
    print(f"Local DB: {DB_PATH}")

# --- DB ���� �Լ� �� ����� ���� ---
def get_db_connection():
    """�����ͺ��̽� ������ ��ȯ�մϴ�. Persistent Disk ����"""
    try:
        # �����ͺ��̽� ���͸��� ������ ����
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created DB directory: {db_dir}")
        
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        # ���� ���� �� �޸� DB�� ���� (�ӽ� ��ġ)
        print("Falling back to in-memory database")
        conn = sqlite3.connect(':memory:', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

# ���� ���� ��ȸ �Լ�
def get_user_subscription_info(user_id):
    """������� ���� ������ ��ȸ�մϴ�."""
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
            
            # �ѱ� �ð���� ���� ��¥ ���
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

# ����� ���̺� �ʱ�ȭ �Լ�
def init_user_tables():
    """����� ���� ���̺���� �ʱ�ȭ�մϴ�. (���� ������ ����)"""
    conn = get_db_connection()
    try:
        # ���� Users ���̺� ���� ���� Ȯ��
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Users';")
        users_exists = cursor.fetchone()
        
        if users_exists:
            # ���� ����� �����Ͱ� �ִ��� Ȯ��
            cursor.execute("SELECT COUNT(*) FROM Users")
            user_count = cursor.fetchone()[0]
            if user_count > 0:
                print("User tables already exist with data - skipping initialization")
                # Signup_Requests�� Password_History ���̺� ���� (���� ���)
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
                        position TEXT DEFAULT '����',
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
                
                # ���� ���� ���̺� ����
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
                
                # ���� �̷� ���̺� ����
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
        
        # SQL ������ ������ ���, ������ �⺻ ���̺� ����
        sql_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_user_table.sql')
        if os.path.exists(sql_file_path):
            try:
                # CP949 ���ڵ����� ���� �õ�
                with open(sql_file_path, 'r', encoding='cp949') as f:
                    sql_script = f.read()
            except UnicodeDecodeError:
                # UTF-8�� ��õ�
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
            
            # �� SQL ���� �и��Ͽ� ����
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
            # �⺻ ���̺�� ���� (���� ������ ����)
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
                    position TEXT DEFAULT '����',
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

# ���� ����Ͻ� ���̺� �ʱ�ȭ �Լ�
def init_business_tables():
    """���� ����Ͻ� ���̺���� �ʱ�ȭ�մϴ�. (���� ������ ����)"""
    conn = get_db_connection()
    try:
        # ���� ���̺� ���� ���� Ȯ��
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Company_Basic';")
        company_basic_exists = cursor.fetchone()
        
        if company_basic_exists:
            print("Business tables already exist with data - skipping initialization")
            return
        
        # ���̺��� ���� ��쿡�� ����
        print("Creating new business tables...")
        
        # ������� ���̺� ����
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
        
        # ����ó ���̺� ����
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
        
        # ����� ���̺� ����
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
        
        # C-Level ��ô���� ���̺� ����
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
        
        # ��ô��� ��� ���̺� ����
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
        
        # ������� ���̺� ����
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Sales_Expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_date DATE NOT NULL,
                expense_type TEXT NOT NULL CHECK (expense_type IN ('�Ĵ�', '�����', '������', '������', '�����', '��Ÿ')),
                amount INTEGER NOT NULL,
                payment_method TEXT NOT NULL CHECK (payment_method IN ('����ī��', '����ī��', '����')),
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

# �н����� ��Ģ ���� �Լ�
def validate_password(password):
    """
    �н����� ��Ģ�� �����մϴ�.
    ��Ģ: 8�� �̻�, ���� ��/�ҹ���, ����, Ư������ ����
    """
    import re
    
    if len(password) < 8:
        return False, "��й�ȣ�� 8�� �̻��̾�� �մϴ�."
    
    if len(password) > 20:
        return False, "��й�ȣ�� 20�� ���Ͽ��� �մϴ�."
    
    # ���� �빮�� ���� ����
    if not re.search(r'[A-Z]', password):
        return False, "��й�ȣ�� ���� �빮�ڰ� ���ԵǾ�� �մϴ�."
    
    # ���� �ҹ��� ���� ����
    if not re.search(r'[a-z]', password):
        return False, "��й�ȣ�� ���� �ҹ��ڰ� ���ԵǾ�� �մϴ�."
    
    # ���� ���� ����
    if not re.search(r'[0-9]', password):
        return False, "��й�ȣ�� ���ڰ� ���ԵǾ�� �մϴ�."
    
    # Ư������ ���� ����
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "��й�ȣ�� Ư������(!@#$%^&*(),.?\":{}|<>)�� ���ԵǾ�� �մϴ�."
    
    return True, "��ȿ�� ��й�ȣ�Դϴ�."

# �н����� �̷� Ȯ�� �Լ�
def check_password_history(user_id, new_password, history_count=5):
    """
    ������� �ֱ� �н����� �̷��� Ȯ���Ͽ� �ߺ� ����� �����մϴ�.
    """
    conn = get_db_connection()
    try:
        # �ֱ� ����� �н����� ��ȸ (�ִ� history_count��)
        recent_passwords = conn.execute('''
            SELECT password FROM Password_History 
            WHERE user_id = ? 
            ORDER BY created_date DESC 
            LIMIT ?
        ''', (user_id, history_count)).fetchall()
        
        # ���� ��� ���� �н����嵵 Ȯ��
        current_password = conn.execute('''
            SELECT password FROM Users WHERE user_id = ?
        ''', (user_id,)).fetchone()
        
        if current_password and current_password['password'] == new_password:
            return False, "���� ��� ���� ��й�ȣ�� �����մϴ�."
        
        for row in recent_passwords:
            if row['password'] == new_password:
                return False, f"�ֱ� {history_count}���� ��й�ȣ �� �̹� ����� ��й�ȣ�Դϴ�."
        
        return True, "��� ������ ��й�ȣ�Դϴ�."
    finally:
        conn.close()

# �н����� �̷� ���� �Լ�
def save_password_history(user_id, password):
    """
    �н����� ���� �� �̷��� �����մϴ�.
    """
    conn = get_db_connection()
    try:
        # ���� �н����带 �̷¿� ����
        current_password = conn.execute('''
            SELECT password FROM Users WHERE user_id = ?
        ''', (user_id,)).fetchone()
        
        if current_password:
            conn.execute('''
                INSERT INTO Password_History (user_id, password)
                VALUES (?, ?)
            ''', (user_id, current_password['password']))
        
        # ������ �̷� ���� (�ֱ� 10���� ����)
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

# ����� ���� �Լ�
def authenticate_user(user_id, password):
    """����� ������ �����մϴ�."""
    # �ϵ��ڵ��� ������ ���� (��� ���ӿ�)
    if user_id == 'yangch' and password == 'yang1123!':
        return {
            'user_id': 'yangch',
            'password': 'yang1123!',
            'name': '��öȣ(������)',
            'user_level': 'V',
            'user_level_name': '���ΰ�����',
            'branch_code': 'ADMIN',
            'branch_name': '�ý��۰���',
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
            # ������ �α��� �ð� ������Ʈ
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

# ����� ���� ��ȸ �Լ�
def get_user_info(user_id):
    """����� ������ ��ȸ�մϴ�."""
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

# ���� Ȯ�� �Լ�
def check_permission(user_level, required_level):
    """����� ������ Ȯ���մϴ�."""
    level_hierarchy = {'V': 4, 'S': 3, 'M': 2, 'N': 1}
    return level_hierarchy.get(user_level, 0) >= level_hierarchy.get(required_level, 0)

# �� ���� �� �����ͺ��̽� �� ����� ���̺� �ʱ�ȭ
def initialize_application():
    """���ø����̼� �ʱ�ȭ �Լ�"""
    print("=== Application Initialization ===")
    print(f"Environment: {'Render' if os.environ.get('RENDER') else 'Local'}")
    print(f"Database Path: {DB_PATH}")
    
    # Render ȯ�濡�� Persistent Disk ���� Ȯ��
    if os.environ.get('RENDER'):
        persistent_disk_path = '/var/data'
        if os.path.exists(persistent_disk_path):
            print("? Persistent Disk detected and mounted")
            # ��ũ �뷮 Ȯ��
            try:
                import shutil
                total, used, free = shutil.disk_usage(persistent_disk_path)
                print(f"  Disk space - Total: {total//1024**3}GB, Used: {used//1024**3}GB, Free: {free//1024**3}GB")
            except:
                pass
        else:
            print("? Persistent Disk not found - using fallback storage")
    
    # �����ͺ��̽� ���� ���� ���� Ȯ��
    if os.path.exists(DB_PATH):
        print(f"? Database file exists: {DB_PATH}")
        try:
            # �����ͺ��̽� ���� �׽�Ʈ
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
            conn.close()
            print("? Database connection successful")
        except Exception as e:
            print(f"? Database connection test failed: {e}")
    else:
        print(f"Creating new database: {DB_PATH}")
    
    # ����� ���̺� �ʱ�ȭ
    init_user_tables()
    print("=== Initialization Complete ===")

# �� ���� �� �ʱ�ȭ ����
initialize_application()

# --- ����� �ֽ� ��ġ ��� ---
def calculate_unlisted_stock_value(financial_data):
    """
    �ʿ��� �繫 �׸�:
    - total_assets: �ڻ��Ѱ�
    - total_liabilities: ��ä�Ѱ�
    - net_income: ������(�ֱ� 3�� ���)
    - shares_issued_count: �����ֽļ�(������ �ں���/5000)
    - capital_stock_value: �ں���
    """
    if not financial_data:
        return {}
    df_financial = pd.DataFrame(financial_data)
    if df_financial.empty:
        return {}

    latest_data = df_financial.sort_values(by='fiscal_year', ascending=False).iloc[0]

    total_assets = float(latest_data.get('total_assets') or 0)
    total_liabilities = float(latest_data.get('total_liabilities') or 0)

    # �ֱ� 3�� ��� ������
    net_income_3y_avg = pd.to_numeric(df_financial['net_income'], errors='coerce').mean()
    if pd.isna(net_income_3y_avg):
        net_income_3y_avg = 0

    asset_value = total_assets - total_liabilities
    profit_value = net_income_3y_avg / 0.1 if net_income_3y_avg else 0

    calculated_value = (asset_value * 2 + profit_value * 3) / 5

    # �ֽļ� ��� - ������ fallback ����
    total_shares = float(latest_data.get('shares_issued_count') or 0)
    
    # 1�ܰ�: shares_issued_count�� ���ų� 1 ������ ���
    if total_shares <= 1:
        # 2�ܰ�: ���� ���� �ֽļ� �հ� �õ�
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
                # 3�ܰ�: �ں���/5000 ���
                capital_stock = float(latest_data.get('capital_stock_value') or 0)
                if capital_stock > 0:
                    total_shares = capital_stock / 5000
                else:
                    total_shares = 1
        except Exception as e:
            print(f"���� ���� �ֽļ� �հ� ��� ����: {e}")
            # 3�ܰ�: �ں���/5000 ���
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

# --- ������� ������ ��ȸ �Լ� �߰� ---
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
    if args.get('company_size') and args.get('company_size') != '��ü':
        filters.append("b.company_size = ?")
        params.append(args.get('company_size'))
    # ����(�ּ�) �˻�: ��� Ű���尡 ���ԵǾ�� ��
    if args.get('region'):
        region_keywords = [kw.strip() for kw in args.get('region').split() if kw.strip()]
        for kw in region_keywords:
            filters.append("b.address LIKE ?")
            params.append(f"%{kw}%")
    # �����׿��� min/max (retained_earnings, �鸸���� �Է°��� ���� ������ ��ȯ)
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

# --- �α׾ƿ� ���Ʈ �߰� ---
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

# --- �����̷� ��ȸ ���Ʈ �߰� ---
@app.route('/history')
def history_search():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('history.html', user_name=session.get('user_name'))

# --- �α��� ���Ʈ �߰� ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        
        # DB ��� ����� ����
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
            
            # �ӽ� ��й�ȣ(password1!) üũ
            if password == 'password1!':
                return redirect(url_for('change_password_first_time'))
            
            return redirect(url_for('main'))
        else:
            error = '���̵� �Ǵ� ��й�ȣ�� �ùٸ��� �ʽ��ϴ�.'
    return render_template('login.html', error=error)

@app.route('/change-password-first-time', methods=['GET', 'POST'])
def change_password_first_time():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # ���� ��й�ȣ�� �ӽ� ��й�ȣ���� Ȯ��
        if current_password != 'password1!':
            return render_template('change_password_first.html', 
                                 error='���� ��й�ȣ�� �ùٸ��� �ʽ��ϴ�.')
        
        # �� ��й�ȣ Ȯ��
        if new_password != confirm_password:
            return render_template('change_password_first.html', 
                                 error='�� ��й�ȣ�� ��ġ���� �ʽ��ϴ�.')
        
        # ��й�ȣ ���⼺ ����
        if not validate_password(new_password):
            return render_template('change_password_first.html', 
                                 error='��й�ȣ�� 8-20�ڸ��̸�, �빮��, �ҹ���, ����, Ư�����ڸ� ���� �ϳ� �̻� �����ؾ� �մϴ�.')
        
        # �ӽ� ��й�ȣ�� ������ �ȵ�
        if new_password == 'password1!':
            return render_template('change_password_first.html', 
                                 error='�ӽ� ��й�ȣ�� ���� ��й�ȣ�� ����� �� �����ϴ�.')
        
        user_id = session.get('user_id')
        
        # ��й�ȣ ����
        conn = get_db_connection()
        try:
            # �н����� �̷� ����
            save_password_history(user_id, new_password)
            
            # ��й�ȣ ������Ʈ
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
                                 error=f'��й�ȣ ���� �� ������ �߻��߽��ϴ�: {str(e)}')
        finally:
            conn.close()
    
    return render_template('change_password_first.html')

# --- index(Ȩ) ������ ���Ʈ �߰� ---

# --- ���� ���� ��ȸ �Լ� ---
def get_user_subscription_info(user_id):
    """������� ���� ������ ��ȸ�ϰ� ���� ��¥�� ����Ͽ� ��ȯ"""
    if not user_id:
        return None
    
    conn = get_db_connection()
    try:
        # ����� ���� ���� ��ȸ (���� ���̺� ��Ű�� ���)
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

    # ���� ���� ��ȸ (���ο� �Լ� ���)
    subscription_info = get_user_subscription_info(user_id)    # ���������̼� ����
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    # Company_Basic ���̺�� ����
    total_companies = conn.execute('SELECT COUNT(*) FROM Company_Basic').fetchone()[0]
    total_pages = math.ceil(total_companies / per_page)

    companies = conn.execute('SELECT * FROM Company_Basic LIMIT ? OFFSET ?', (per_page, offset)).fetchall()

    # ���� �̷� ��ȸ ���� ó�� ����
    user_level = session.get('user_level', 'N')
    contact_params = []
    contact_history_query = "SELECT * FROM Contact_History"
    
    # V(���ΰ�����), S(���������)�� ��ü �̷� ��ȸ ����
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
    
    # ���� ���� ��ȸ
    subscription_info = get_user_subscription_info(session.get('user_id'))
    
    # ����� ���� ������ ���ø��� ����
    user_data = {
        'user_name': session.get('user_name'),
        'user_level': session.get('user_level', 'N'),
        'user_level_name': session.get('user_level_name', '�Ϲݴ����'),
        'branch_name': session.get('branch_name', ''),
        'can_manage_users': check_permission(session.get('user_level', 'N'), 'S'),
        'subscription_info': subscription_info
    }
    
    return render_template('main.html', **user_data)
# (���ʿ��� �߸��� �鿩���� ���� ����)
# --- �����̷� ������ ��ȸ API �߰� ---
@app.route('/api/contact_history_csv', methods=['GET', 'POST'])
def contact_history_csv():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    if request.method == 'GET':
        # ������ ����� Contact_History�� CSV�� ��ȯ (�����ڴ� ��ü ��ȸ ����)
        conn = get_db_connection()
        user_level = session.get('user_level', 'N')
        user_id = session.get('user_id')
        
        if user_level in ['V', 'S']:  # �ְ������, �ý��۰����ڴ� ��ü ��ȸ
            rows = conn.execute('SELECT history_id, contact_datetime, biz_no, contact_type, contact_person, memo, registered_by FROM Contact_History ORDER BY history_id').fetchall()
        else:  # �Ϲ� ����ڴ� ���� ��� �Ǹ� ��ȸ
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
        # ���ε�: ���� ������ ��ü ���� ��, ���ε�� CSV�� ��ü ��ü
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '������ �����ϴ�.'}), 400
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': 'CSV ���ϸ� ���ε� �����մϴ�.'}), 400
        
        # ���ڵ� ���� �� ó��
        content = file.stream.read()
        try:
            # UTF-8 BOM �켱 �õ�
            decoded_content = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                # CP949 (EUC-KR) �õ�
                decoded_content = content.decode('cp949')
            except UnicodeDecodeError:
                # UTF-8 �õ�
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
    print(">>> /api/history_search ���Ʈ ����")  # ���Ʈ ���� Ȯ�ο� �α�
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = session.get('user_id')
        print(f"���� user_id: {user_id}")
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
        
        # �����ID�� ��Ȯ�� �Էµ� ��츸 �ش� ����� ��ϰǸ� ��ȸ
        if search_user is not None and search_user.strip() != "":
            filters.append("h.registered_by = ?")
            params.append(search_user.strip())
        else:
            # �����ID ���Է� �� ���ѿ� ���� ��ȸ ���� ����
            if check_permission(user_level, 'S'):  # V(���ΰ�����), S(���������)
                # ��ü �̷� ��ȸ (���� ����)
                pass
            else:
                # M(�Ŵ���), N(�Ϲݴ����)�� ���� ��ϰǸ� ��ȸ
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

        print(f"���� ����: {query}")
        print(f"�Ķ����: {params}")

        conn = get_db_connection()
        results = conn.execute(query, params).fetchall()
        conn.close()

        print(f"��ȸ�� ��� ��: {len(results)}")
        return jsonify([dict(row) for row in results])
        
    except Exception as e:
        print(f"Error in api_history_search: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# ���� [����] get_companies �Լ� ����
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
            return "�˻� ����� 500���� �ʰ��մϴ�. ������ �����Ͽ� 500�� ���Ϸ� ��ȸ���ּ���.", 400
        df.rename(columns={
            'biz_no': '����ڹ�ȣ', 'company_name': '�����', 'representative_name': '��ǥ�ڸ�', 'phone_number': '��ȭ��ȣ',
            'company_size': '����Ը�', 'address': '�ּ�', 'industry_name': '������', 'fiscal_year': '�ֽŰ��⵵',
            'total_assets': '�ڻ��Ѱ�', 'sales_revenue': '�����', 'retained_earnings': '�����׿���'
        }, inplace=True)
        excel_cols = ['����ڹ�ȣ', '�����', '��ǥ�ڸ�', '��ȭ��ȣ', '����Ը�', '�ּ�', '������', '�ֽŰ��⵵', '�ڻ��Ѱ�', '�����', '�����׿���']
        df_excel = df[[col for col in excel_cols if col in df.columns]]
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='�������')
        output.seek(0)
        return Response(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": "attachment;filename=company_data.xlsx"})
    except ImportError:
        return "���� ���� ������ �ʿ��� 'xlsxwriter' ��Ű���� ��ġ�Ǿ� ���� �ʽ��ϴ�. �����ڿ��� �����ϼ���.", 500
    except Exception as e:
        print(f"Error in export_excel: {e}")
        return f"���� ���� ���� �� ������ �߻��߽��ϴ�. ��: {e}", 500

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

    # ���ѿ� ���� �����̷� ��ȸ ���� ����
    if user_level == 'V':  # ���ΰ�����: ��� �̷�
        pass
    elif user_level == 'S':  # ���������: �����ڱ� �̷¸�
        history_query += " AND registered_by IN (SELECT user_id FROM Users WHERE user_level IN ('V', 'S'))"
    else:  # �Ŵ���, �Ϲݴ����: ���� �̷¸�
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
    
    # ���� ���� ó�� ���� - ������, �ֽļ�, �ݾ� ���
    processed_shareholders = []
    total_shares_owned = 0
    
    if shareholders:
        # ��ü �ֽļ� ��� (stock_valuation���� ���� �� ���)
        total_shares_issued = stock_valuation.get('total_shares_issued', 1)
        estimated_stock_value = stock_valuation.get('estimated_stock_value', 0)
        
        for shareholder in shareholders:
            try:
                shareholder_dict = dict(shareholder)
                
                # ������ ������ ��ȯ
                try:
                    ownership_percent = float(shareholder_dict.get('ownership_percent', 0) or 0)
                except (ValueError, TypeError):
                    ownership_percent = 0.0
                
                # ���� �ֽļ��� �ִ��� Ȯ��
                actual_stock_quantity = shareholder_dict.get('total_shares_owned')
                has_actual_stock_data = (actual_stock_quantity is not None and 
                                       actual_stock_quantity != '' and 
                                       actual_stock_quantity != 0)
                
                if has_actual_stock_data:
                    # ���� �ֽļ� �����Ͱ� �ִ� ���
                    try:
                        stock_quantity = float(actual_stock_quantity)
                        is_predicted = False
                    except (ValueError, TypeError):
                        stock_quantity = 0.0
                        is_predicted = False
                else:
                    # ���� �ֽļ��� ���� ��� �������� ���� ���
                    try:
                        stock_quantity = (total_shares_issued * ownership_percent) / 100.0
                        is_predicted = True
                    except (ValueError, TypeError):
                        stock_quantity = 0.0
                        is_predicted = True
                
                # �ֽ� �ݾ� ���
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
                    'is_predicted': is_predicted  # ���� ���θ� ǥ��
                })
                
                processed_shareholders.append(shareholder_dict)
                total_shares_owned += stock_quantity
                
            except Exception as e:
                print(f"���� ���� ó�� �� ����: {e}")
                # ������ �߻��� ���ִ� �ǳʶٰ� ��� ����
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

    # �����Ͻð� ������ ���� �ѱ� �ð����� ����
    if not contact_datetime_str:
        contact_datetime_str = format_kst_datetime()
    
    try:
        # �ð��� ������ �ִ� ��� �ѱ� �ð����� ��ȯ
        if contact_datetime_str:
            if 'T' in contact_datetime_str:
                # ISO ������ ���
                if contact_datetime_str.endswith('Z'):
                    # UTC �ð��� ���
                    dt_utc = datetime.fromisoformat(contact_datetime_str[:-1]).replace(tzinfo=pytz.UTC)
                    dt_kst = dt_utc.astimezone(KST)
                    formatted_datetime = dt_kst.strftime('%Y-%m-%d %H:%M:%S')
                elif '+' in contact_datetime_str or '-' in contact_datetime_str.split('T')[1]:
                    # �ð��� ������ �ִ� ���
                    dt_with_tz = datetime.fromisoformat(contact_datetime_str)
                    dt_kst = dt_with_tz.astimezone(KST)
                    formatted_datetime = dt_kst.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # �ð��� ������ ���� ��� �ѱ� �ð����� ����
                    dt_naive = datetime.fromisoformat(contact_datetime_str.replace('T', ' '))
                    dt_kst = KST.localize(dt_naive)
                    formatted_datetime = dt_kst.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # �Ϲ� ���ڿ� ������ ��� �ѱ� �ð����� ����
                formatted_datetime = contact_datetime_str
        else:
            # �ð��� ������ ���� �ѱ� �ð� ���
            formatted_datetime = format_kst_datetime()
        
        # �̷� �ð� üũ (�ѱ� �ð� ����)
        submitted_dt = datetime.strptime(formatted_datetime, '%Y-%m-%d %H:%M:%S')
        now_kst = get_kst_now().replace(tzinfo=None)
        
        # 1���� �����ð��� �ξ� ��Ʈ��ũ �����̳� �ð� ����ȭ ������ ���
        from datetime import timedelta
        if submitted_dt > (now_kst + timedelta(minutes=1)):
            return jsonify({"success": False, "message": "�̷� ��¥ �� �ð����� ���/������ �� �����ϴ�."}), 400
            
    except ValueError as e:
        return jsonify({"success": False, "message": f"�߸��� ��¥ �����Դϴ�: {str(e)}"}), 400

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
            return jsonify({"success": True, "message": "�߰��Ǿ����ϴ�.", "new_history_id": new_id})
        
        elif request.method == 'PUT':
            if not history_id:
                return jsonify({"success": False, "message": "������ �̷� ID�� �����ϴ�."}), 400
            conn.execute(
                "UPDATE Contact_History SET contact_datetime=?, contact_type=?, contact_person=?, memo=?, registered_by=? WHERE history_id = ?", 
                (formatted_datetime, contact_type, contact_person, memo, user_id, history_id)
            )
            conn.commit()
            return jsonify({"success": True, "message": "�����Ǿ����ϴ�."})

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

# --- ������ ���� ���Ʈ ---
@app.route('/gift_tax')
def gift_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('gift_tax.html', user_name=session.get('user_name'))

# --- �絵�ҵ漼 ���� ���Ʈ ---
@app.route('/transfer_tax')
def transfer_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('transfer_tax.html', user_name=session.get('user_name'))

# --- ���ռҵ漼 ���� ���Ʈ ---
@app.route('/income_tax')
def income_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('income_tax.html', user_name=session.get('user_name'))

# --- 4�뺸��� ���� ���Ʈ ---
@app.route('/social_ins_tax')
def social_ins_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('social_ins_tax.html', user_name=session.get('user_name'))


# --- ��漼 ���� ���Ʈ ---
@app.route('/acquisition_tax')
def acquisition_tax():
    if not session.get('logged_in') or not session.get('user_name') or session.get('user_name') == 'None':
        return redirect(url_for('login'))
    return render_template('acquisition_tax.html', user_name=session.get('user_name'))

# --- ������ ���� ���Ʈ ---
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

# --- ����� ���� ���Ʈ ---
@app.route('/expense_management')
def expense_management():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_data = {
        'user_name': session.get('user_name'),
        'user_level': session.get('user_level', 'N'),
        'user_level_name': session.get('user_level_name', '�Ϲݴ����'),
        'branch_name': session.get('branch_name', ''),
        'user_id': session.get('user_id')
    }
    
    return render_template('expense_management.html', **user_data)

# --- �������� ���� ���Ʈ ---
@app.route('/view_receipt/<int:expense_id>')
def view_receipt(expense_id):
    """������ ���� ���� (���� ���� ����)"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ����ڰ� ����� �������� �Ǵ� �����ڴ� ��� ������ ��ȸ
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
            return "������ ������ ã�� �� �����ϴ�.", 404
            
        receipt_files = result[0]
        
        # ���� ������ ��� �޸��� ���е� ���ϸ���� ó��
        if ',' in receipt_files:
            file_list = receipt_files.split(',')
            # ù ��° ���ϸ� �����ְų�, ���� ���� ��� �������� �����̷�Ʈ
            return f"""
            <html>
            <head><title>������ ���� ���</title></head>
            <body>
                <h3>������ ���� ���</h3>
                <ul>
                    {''.join([f'<li><a href="/view_single_receipt/{expense_id}/{i}" target="_blank">{filename}</a></li>' for i, filename in enumerate(file_list)])}
                </ul>
            </body>
            </html>
            """
        else:
            # ���� ������ ���
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_files)
            
            if not os.path.exists(file_path):
                return "������ ������ �������� �ʽ��ϴ�.", 404
                
            return send_file(file_path)
        
    except Exception as e:
        print(f"[RECEIPT_VIEW_ERROR] {str(e)}")
        return f"������ ���� ����: {str(e)}", 500


@app.route('/view_single_receipt/<int:expense_id>/<int:file_index>')
def view_single_receipt(expense_id, file_index):
    """���� ������ ���� ����"""
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
            return "������ ������ ã�� �� �����ϴ�.", 404
            
        receipt_files = result[0].split(',')
        
        if file_index >= len(receipt_files):
            return "���� �ε����� �߸��Ǿ����ϴ�.", 404
            
        filename = receipt_files[file_index]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return "������ ������ �������� �ʽ��ϴ�.", 404
            
        return send_file(file_path)
        
    except Exception as e:
        print(f"[SINGLE_RECEIPT_VIEW_ERROR] {str(e)}")
        return f"������ ���� ����: {str(e)}", 500
        print(f"[RECEIPT_VIEW_ERROR] {str(e)}")
        return f"������ ���� ����: {str(e)}", 500


@app.route('/download_receipt/<int:expense_id>')
def download_receipt(expense_id):
    """������ ���� �ٿ�ε�"""
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
            return "������ ������ ã�� �� �����ϴ�.", 404
            
        receipt_filename = result[0]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename)
        
        if not os.path.exists(file_path):
            return "������ ������ �������� �ʽ��ϴ�.", 404
            
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        print(f"[RECEIPT_DOWNLOAD_ERROR] {str(e)}")
        return f"������ �ٿ�ε� ����: {str(e)}", 500


@app.route('/sales_management')
def sales_management():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_data = {
        'user_name': session.get('user_name'),
        'user_level': session.get('user_level', 'N'),
        'user_level_name': session.get('user_level_name', '�Ϲݴ����'),
        'branch_name': session.get('branch_name', ''),
        'user_id': session.get('user_id')
    }
    
    return render_template('sales_management.html', **user_data)

# --- C-Level ��ô���� ���Ʈ (���� ȣȯ��) ---
@app.route('/clevel_management')
def clevel_management():
    return redirect(url_for('sales_management'))

# --- ����� ���� ���Ʈ (���ΰ�����, ��������ڸ� ���� ����) ---
@app.route('/user_management')
def user_management():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_level = session.get('user_level', 'N')
    if not check_permission(user_level, 'S'):  # ��������� �̻� ���� ����
        return "���� ������ �����ϴ�.", 403
    
    return render_template('user_management.html', user_name=session.get('user_name'))

# --- ����� ��� API ---
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

# --- ����� �߰�/���� API ---
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
            # �н����� ��Ģ ���� (�ű� �����)
            password = data.get('password')
            if password:
                is_valid, validation_message = validate_password(password)
                if not is_valid:
                    return jsonify({"success": False, "message": validation_message}), 400
            
            # ����� �߰�
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
            return jsonify({"success": True, "message": "����ڰ� �߰��Ǿ����ϴ�."})
        
        elif request.method == 'PUT':
            # ����� ����
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
            return jsonify({"success": True, "message": "����� ������ �����Ǿ����ϴ�."})
    
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- ��й�ȣ ���� API ---
@app.route('/api/users/<user_id>/password', methods=['PUT'])
def change_password(user_id):
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    current_user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    # ���� ��й�ȣ�̰ų� ������ ���� �ʿ�
    if user_id != current_user_id and not check_permission(user_level, 'S'):
        return jsonify({"error": "Permission denied"}), 403
    
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if not new_password:
        return jsonify({"success": False, "message": "�� ��й�ȣ�� �Է����ּ���."}), 400
    
    if new_password != confirm_password:
        return jsonify({"success": False, "message": "�� ��й�ȣ�� ��ġ���� �ʽ��ϴ�."}), 400
    
    # �н����� ��Ģ ����
    is_valid, validation_message = validate_password(new_password)
    if not is_valid:
        return jsonify({"success": False, "message": validation_message}), 400
    
    # �н����� �̷� Ȯ��
    history_valid, history_message = check_password_history(user_id, new_password)
    if not history_valid:
        return jsonify({"success": False, "message": history_message}), 400
    
    conn = get_db_connection()
    try:
        # ���� ��й�ȣ ������ ��� ���� ��й�ȣ Ȯ��
        if user_id == current_user_id:
            if not current_password:
                return jsonify({"success": False, "message": "���� ��й�ȣ�� �Է����ּ���."}), 400
            
            current_user = conn.execute(
                "SELECT password FROM Users WHERE user_id = ?", (user_id,)
            ).fetchone()
            
            if not current_user or current_user['password'] != current_password:
                return jsonify({"success": False, "message": "���� ��й�ȣ�� ��ġ���� �ʽ��ϴ�."}), 400
        
        # �н����� �̷� ���� (���� �� �н�����)
        save_password_history(user_id, new_password)
        
        # ��й�ȣ ������Ʈ
        conn.execute('''
            UPDATE Users SET 
                password=?, 
                password_changed_date=date('now'),
                updated_date=CURRENT_TIMESTAMP
            WHERE user_id=?
        ''', (new_password, user_id))
        conn.commit()
        return jsonify({"success": True, "message": "��й�ȣ�� ����Ǿ����ϴ�."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- ��й�ȣ �ʱ�ȭ API ---
@app.route('/api/users/<user_id>/reset-password', methods=['PUT'])
def reset_password(user_id):
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    
    # ������ ���� �ʿ� (��������� �̻�)
    if not check_permission(user_level, 'S'):
        return jsonify({"error": "Permission denied"}), 403
    
    data = request.json
    new_password = data.get('new_password', 'password1!')
    
    conn = get_db_connection()
    try:
        # ����ڰ� �����ϴ��� Ȯ��
        user_exists = conn.execute(
            "SELECT user_id FROM Users WHERE user_id = ?", (user_id,)
        ).fetchone()
        
        if not user_exists:
            return jsonify({"success": False, "message": "����ڸ� ã�� �� �����ϴ�."}), 404
        
        # �н����� �̷� ���� (�ʱ�ȭ �� �н�����)
        save_password_history(user_id, new_password)
        
        # ��й�ȣ �ʱ�ȭ
        conn.execute('''
            UPDATE Users SET 
                password=?, 
                password_changed_date=date('now'),
                updated_date=CURRENT_TIMESTAMP
            WHERE user_id=?
        ''', (new_password, user_id))
        conn.commit()
        return jsonify({"success": True, "message": f"��й�ȣ�� '{new_password}'�� �ʱ�ȭ�Ǿ����ϴ�."})
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
    
    # �ְ������ ���� �ʿ� (V)
    if not check_permission(user_level, 'V'):
        return jsonify({"error": "Permission denied"}), 403
    
    # �ڱ� �ڽ��� ������ �� ����
    if current_user_id == user_id:
        return jsonify({"success": False, "message": "�ڱ� �ڽ��� ������ �� �����ϴ�."}), 400
    
    conn = get_db_connection()
    try:
        # ����ڰ� �����ϴ��� Ȯ��
        user_info = conn.execute(
            "SELECT user_id, name FROM Users WHERE user_id = ?", (user_id,)
        ).fetchone()
        
        if not user_info:
            return jsonify({"success": False, "message": "����ڸ� ã�� �� �����ϴ�."}), 404
        
        # ���� ���̺��� ������ ���� (�ܷ�Ű ������׿� ���� �������)
        # 1. ���� �̷� ����
        conn.execute("DELETE FROM Contact_History WHERE registered_by = ?", (user_id,))
        
        # 2. �н����� �̷� ����
        conn.execute("DELETE FROM Password_History WHERE user_id = ?", (user_id,))
        
        # 3. ����� ���� ���� ����
        conn.execute("DELETE FROM User_Subscriptions WHERE user_id = ?", (user_id,))
        
        # 4. ����� ����
        conn.execute("DELETE FROM Users WHERE user_id = ?", (user_id,))
        
        conn.commit()
        return jsonify({"success": True, "message": f"����� '{user_id} ({user_info['name']})'�� ���������� �����Ǿ����ϴ�."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"����� ���� �� ������ �߻��߽��ϴ�: {str(e)}"}), 500
    finally:
        conn.close()

# --- ȸ�� ���� ��û API ---
@app.route('/api/signup-request', methods=['POST'])
def signup_request():
    data = request.json
    
    # �����: ���ŵ� ������ Ȯ��
    print(f"ȸ������ ��û ������: {data}")
    
    # �ʼ� �ʵ� ����
    required_fields = ['user_id', 'name', 'phone', 'email', 'birth_date', 'gender', 'position']
    for field in required_fields:
        if not data.get(field):
            print(f"������ �ʵ�: {field}")
            return jsonify({"success": False, "message": f"{field}�� �ʼ� �׸��Դϴ�."}), 400
    
    # branch_name�� ������ �⺻�� ����
    if not data.get('branch_name'):
        data['branch_name'] = '������'
    
    # branch_code�� ������ branch_name�� �����ϰ� ����
    if not data.get('branch_code'):
        data['branch_code'] = data['branch_name']
    
    conn = get_db_connection()
    try:
        # �ߺ� ���̵� Ȯ�� (���� �����)
        existing_user = conn.execute(
            "SELECT user_id FROM Users WHERE user_id = ?", (data['user_id'],)
        ).fetchone()
        
        if existing_user:
            return jsonify({"success": False, "message": "�̹� ��� ���� ���̵��Դϴ�."}), 400
        
        # �ߺ� ��û Ȯ�� �� ó��
        existing_request = conn.execute(
            "SELECT id, status FROM Signup_Requests WHERE user_id = ?", 
            (data['user_id'],)
        ).fetchone()
        
        if existing_request:
            if existing_request['status'] == 'PENDING':
                return jsonify({"success": False, "message": "�̹� ��û�� ���̵��Դϴ�. ���� ��� ���Դϴ�."}), 400
            elif existing_request['status'] == 'APPROVED':
                return jsonify({"success": False, "message": "�̹� ���ε� ���̵��Դϴ�."}), 400
            elif existing_request['status'] == 'REJECTED':
                # ������ ��û�� ������Ʈ ����
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
                return jsonify({"success": True, "message": "��û ������ �����Ǿ� ���û�Ǿ����ϴ�."})
        
        # ���ο� ���� ��û ����
        conn.execute('''
            INSERT INTO Signup_Requests (user_id, name, phone, email, branch_code, branch_name, birth_date, gender, position, purpose)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['user_id'], data['name'], data['phone'], data['email'], 
            data['branch_code'], data['branch_name'], data['birth_date'], 
            data['gender'], data['position'], data.get('purpose', '')
        ))
        conn.commit()
        
        return jsonify({"success": True, "message": "���� ��û�� �Ϸ�Ǿ����ϴ�."})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- ���� ��û ��� ��ȸ API ---
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

# --- ���� ��û ����/���� API ---
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
        return jsonify({"success": False, "message": "�߸��� �׼��Դϴ�."}), 400
    
    admin_user = session.get('user_id')
    
    conn = get_db_connection()
    try:
        # ��û ���� ��ȸ
        signup_request = conn.execute(
            "SELECT * FROM Signup_Requests WHERE id = ? AND status = 'PENDING'", 
            (request_id,)
        ).fetchone()
        
        if not signup_request:
            return jsonify({"success": False, "message": "ó���� �� ���� ��û�Դϴ�."}), 404
        
        if action == 'approve':
            # ����� ���� ����
            default_password = 'Welcome123!'
            conn.execute('''
                INSERT INTO Users 
                (user_id, password, name, user_level, user_level_name, branch_code, branch_name, 
                 phone, email, birth_date, gender, position, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signup_request['user_id'], default_password, signup_request['name'], 
                'N', '�Ϲݴ����', signup_request['branch_code'], signup_request['branch_name'],
                signup_request['phone'], signup_request['email'], signup_request['birth_date'],
                signup_request['gender'], signup_request['position'], 'ACTIVE'
            ))
            
            # ��û ���� ������Ʈ
            conn.execute('''
                UPDATE Signup_Requests 
                SET status = 'APPROVED', processed_date = CURRENT_TIMESTAMP, 
                    processed_by = ?, admin_notes = ?
                WHERE id = ?
            ''', (admin_user, admin_notes, request_id))
            
            message = f"'{signup_request['user_id']}' ������ ���εǾ����ϴ�. �⺻ ��й�ȣ: {default_password}"
            
        else:  # reject
            # ��û ���� ������Ʈ
            conn.execute('''
                UPDATE Signup_Requests 
                SET status = 'REJECTED', processed_date = CURRENT_TIMESTAMP, 
                    processed_by = ?, admin_notes = ?
                WHERE id = ?
            ''', (admin_user, admin_notes, request_id))
            
            message = f"'{signup_request['user_id']}' ���� ��û�� �����Ǿ����ϴ�."
        
        conn.commit()
        return jsonify({"success": True, "message": message})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- ��û ���� ��ȸ API ---
@app.route('/api/check-signup-status', methods=['POST'])
def check_signup_status():
    data = request.json
    user_id = data.get('user_id')
    name = data.get('name')
    
    if not user_id or not name:
        return jsonify({"success": False, "message": "���̵�� �̸��� �Է����ּ���."}), 400
    
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
            return jsonify({"success": False, "message": "�ش� ��û ������ ã�� �� �����ϴ�."}), 404
        
        return jsonify({"success": True, "data": dict(signup_request)})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- ��û ���� �������� API ---
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
            return jsonify({"success": False, "message": "���� ������ ��û ������ ã�� �� �����ϴ�."}), 404
        
        return jsonify({"success": True, "data": dict(signup_request)})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- ���û API ---
@app.route('/api/resubmit-signup/<user_id>', methods=['PUT'])
def resubmit_signup(user_id):
    conn = get_db_connection()
    try:
        # ���� ��û�� �ִ��� Ȯ��
        existing_request = conn.execute(
            "SELECT id FROM Signup_Requests WHERE user_id = ? AND status IN ('PENDING', 'REJECTED')", 
            (user_id,)
        ).fetchone()
        
        if not existing_request:
            return jsonify({"success": False, "message": "���û�� �� �ִ� ��û�� �����ϴ�."}), 404
        
        # ���¸� PENDING���� �����ϰ� ��û���� ���� �ð����� ������Ʈ
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
        return jsonify({"success": True, "message": "���û�� �Ϸ�Ǿ����ϴ�."})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- ���� ���� API ---
@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    user_level = session.get('user_level', 'N')
    if user_level not in ['V', 'S']:
        return jsonify({"error": "Forbidden"}), 403
    
    conn = get_db_connection()
    try:
        # ���� ��Ȳ ��ȸ
        subscriptions = conn.execute('''
            SELECT us.*, u.name as user_name,
                   COALESCE(SUM(ph.amount), 0) as total_paid
            FROM User_Subscriptions us
            LEFT JOIN Users u ON us.user_id = u.user_id
            LEFT JOIN Payment_History ph ON us.user_id = ph.user_id
            GROUP BY us.user_id
            ORDER BY us.subscription_start_date DESC
        ''').fetchall()
        
        # ���� �̷� ��ȸ
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
        return jsonify({"success": False, "message": "�ʼ� �׸��� ��� �Է����ּ���."}), 400
    
    conn = get_db_connection()
    try:
        conn.execute('BEGIN TRANSACTION')
        
        # ���� ���� ���� Ȯ��
        existing = conn.execute(
            "SELECT * FROM User_Subscriptions WHERE user_id = ?", (user_id,)
        ).fetchone()
        
        # ���� ���� ��ȯ (UI���� ���� ���� DB �������� ��ȯ)
        if subscription_type == 'monthly':
            db_subscription_type = 'MONTHLY'
        elif subscription_type == 'annual':
            db_subscription_type = 'YEARLY'  # ANNUAL -> YEARLY�� ����
        elif subscription_type == 'free':
            db_subscription_type = 'FREE'
        else:
            db_subscription_type = subscription_type.upper()
        
        if existing:
            # ���� ���� ������Ʈ
            conn.execute('''
                UPDATE User_Subscriptions SET 
                    subscription_type=?, subscription_start_date=?, subscription_end_date=?, updated_date=CURRENT_TIMESTAMP
                WHERE user_id=?
            ''', (db_subscription_type, start_date, end_date, user_id))
        else:
            # �� ���� ����
            conn.execute('''
                INSERT INTO User_Subscriptions (user_id, subscription_type, subscription_start_date, subscription_end_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, db_subscription_type, start_date, end_date))
        
        # ���� �ݾ��� ������ ���� �̷� �߰�
        if payment_amount and float(payment_amount) > 0:
            from datetime import date
            today = date.today().strftime('%Y-%m-%d')
            
            # payment_type ����
            payment_type = 'MONTHLY' if db_subscription_type == 'MONTHLY' else \
                          'YEARLY' if db_subscription_type == 'YEARLY' else 'SIGNUP'
            
            conn.execute('''
                INSERT INTO Payment_History (user_id, payment_date, amount, payment_type, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, today, float(payment_amount), payment_type, payment_method, notes))
        
        conn.commit()
        return jsonify({"success": True, "message": "������ �����Ǿ����ϴ�."})
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
        return jsonify({"success": True, "message": "������ �����Ǿ����ϴ�."})
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
        # �����ϱ� ���� �ش� ���� �̷��� �����ϴ��� Ȯ��
        payment = conn.execute(
            "SELECT * FROM Payment_History WHERE id = ?", (payment_id,)
        ).fetchone()
        
        if not payment:
            return jsonify({"success": False, "message": "���� �̷��� ã�� �� �����ϴ�."}), 404
        
        # ���� �̷� ����
        conn.execute("DELETE FROM Payment_History WHERE id = ?", (payment_id,))
        conn.commit()
        
        return jsonify({"success": True, "message": "���� �̷��� �����Ǿ����ϴ�."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- ����� ���� API ---
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # ���ѿ� ���� ��ȸ ���� ����
        if check_permission(user_level, 'S'):  # �����ڴ� ��� ��� ��ȸ
            expenses = conn.execute('''
                SELECT e.*, u.name as registered_by_name, c.company_name
                FROM Expenses e
                LEFT JOIN Users u ON e.registered_by = u.user_id
                LEFT JOIN Company_Basic c ON e.biz_no = c.biz_no
                ORDER BY e.expense_date DESC
            ''').fetchall()
        else:  # �Ϲ� ����ڴ� ���� ��� ��븸 ��ȸ
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
        return jsonify({"success": True, "message": "����� ��ϵǾ����ϴ�."})
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
        # ���� Ȯ��: ������ ����� ����̰ų� �������� ��츸 ���� ����
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
        return jsonify({"success": True, "message": "��� ������ �����Ǿ����ϴ�."})
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
        # ���� Ȯ��: ������ ����� ����̰ų� �������� ��츸 ���� ����
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM Expenses WHERE id = ?", (expense_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        conn.execute("DELETE FROM Expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return jsonify({"success": True, "message": "����� �����Ǿ����ϴ�."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- C-Level ��ô���� API ---
@app.route('/api/clevel_targets', methods=['GET'])
def get_clevel_targets():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # ���ѿ� ���� ��ȸ ���� ����
        if check_permission(user_level, 'S'):  # �����ڴ� ��� Ÿ�� ��ȸ
            targets = conn.execute('''
                SELECT t.*, u.name as registered_by_name, c.company_name
                FROM CLevel_Targets t
                LEFT JOIN Users u ON t.registered_by = u.user_id
                LEFT JOIN Company_Basic c ON t.biz_no = c.biz_no
                ORDER BY t.created_date DESC
            ''').fetchall()
        else:  # �Ϲ� ����ڴ� ���� ��� Ÿ�ٸ� ��ȸ
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
        return jsonify({"success": True, "message": "C-Level Ÿ���� ��ϵǾ����ϴ�."})
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
        # ���� Ȯ��: ������ ����� Ÿ���̰ų� �������� ��츸 ���� ����
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
        return jsonify({"success": True, "message": "C-Level Ÿ�� ������ �����Ǿ����ϴ�."})
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
        # ���� Ȯ��: ������ ����� Ÿ���̰ų� �������� ��츸 ���� ����
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM CLevel_Targets WHERE id = ?", (target_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        conn.execute("DELETE FROM CLevel_Targets WHERE id = ?", (target_id,))
        conn.commit()
        return jsonify({"success": True, "message": "C-Level Ÿ���� �����Ǿ����ϴ�."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- ��ô��� ��� ���� API ---
@app.route('/api/pioneering_targets', methods=['GET'])
def get_pioneering_targets():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # ���ѿ� ���� ��ȸ ���� ����
        if check_permission(user_level, 'S'):  # �����ڴ� ��� Ÿ�� ��ȸ
            targets = conn.execute('''
                SELECT p.*, u.name as visitor_name, c.company_name
                FROM Pioneering_Targets p
                LEFT JOIN Users u ON p.visitor_id = u.user_id
                LEFT JOIN Company_Basic c ON REPLACE(p.biz_no, '-', '') = c.biz_no
                ORDER BY p.visit_date DESC, p.created_date DESC
            ''').fetchall()
        else:  # �Ϲ� ����ڴ� ���� ��� Ÿ�ٸ� ��ȸ
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
        return jsonify({"success": False, "message": "�α����� �ʿ��մϴ�."}), 401
    
    try:
        data = request.json
    except Exception as e:
        return jsonify({"success": False, "message": "�߸��� JSON �����Դϴ�."}), 400
    
    if not data:
        return jsonify({"success": False, "message": "�����Ͱ� ���۵��� �ʾҽ��ϴ�."}), 400
    
    user_id = session.get('user_id')
    biz_no = data.get('biz_no')
    visit_date = data.get('visit_date')
    notes = data.get('notes', '')
    visitor_id = data.get('visitor_id', user_id)
    
    if not biz_no or not visit_date:
        return jsonify({"success": False, "message": "����ڹ�ȣ�� �湮���ڴ� �ʼ��Դϴ�."}), 400
    
    conn = get_db_connection()
    try:
        # �ߺ� Ȯ��
        existing = conn.execute('''
            SELECT id FROM Pioneering_Targets 
            WHERE biz_no = ? AND visit_date = ? AND registered_by = ?
        ''', (biz_no, visit_date, user_id)).fetchone()
        
        if existing:
            return jsonify({"success": False, "message": "�̹� �ش� ��¥�� ����� ����Դϴ�."})
        
        # ����
        result = conn.execute('''
            INSERT INTO Pioneering_Targets 
            (biz_no, visit_date, visitor_id, notes, registered_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (biz_no, visit_date, visitor_id, notes, user_id))
        
        conn.commit()
        
        return jsonify({
            "success": True, 
            "message": "��ô ����� ���������� ��ϵǾ����ϴ�.", 
            "id": result.lastrowid
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"��� �� ������ �߻��߽��ϴ�: {str(e)}"}), 500
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
        # ���� Ȯ��: ������ ����� Ÿ���̰ų� �������� ��츸 ���� ����
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM Pioneering_Targets WHERE id = ?", (target_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        conn.execute("DELETE FROM Pioneering_Targets WHERE id = ?", (target_id,))
        conn.commit()
        return jsonify({"success": True, "message": "��ô ����� �����Ǿ����ϴ�."})
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
        return jsonify({"success": True, "message": "�湮 �Ϸ� ó���Ǿ����ϴ�."})
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
        return jsonify({'success': False, 'message': '������ �����ϴ�.'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'message': 'CSV ���ϸ� ���ε� �����մϴ�.'}), 400
    
    user_id = session.get('user_id')
    
    try:
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)
        
        conn = get_db_connection()
        inserted = 0
        
        for row in reader:
            if row.get('����ڹ�ȣ') and row.get('�湮����'):
                try:
                    conn.execute('''
                        INSERT INTO Pioneering_Targets 
                        (biz_no, visit_date, visitor_id, registered_by)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        row['����ڹ�ȣ'], row['�湮����'], 
                        row.get('�湮��ID', user_id), user_id
                    ))
                    inserted += 1
                except Exception as e:
                    continue  # �ߺ� ���� ������ �����ϰ� ���
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'inserted': inserted, 'message': f'{inserted}���� ��ϵǾ����ϴ�.'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'CSV ó�� �� ����: {str(e)}'}), 500

# --- ������� ���� API ---
@app.route('/api/sales_expenses', methods=['GET'])
def get_sales_expenses():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get('user_id')
    user_level = session.get('user_level', 'N')
    
    conn = get_db_connection()
    try:
        # ���ѿ� ���� ��ȸ ���� ����
        if check_permission(user_level, 'S'):  # �����ڴ� ��� ��� ��ȸ
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
        else:  # �Ϲ� ����ڴ� ���� ��� ��븸 ��ȸ
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
    
    # ���� ���� ���ε� ó��
    receipt_filenames = []
    if 'receipt_files' in request.files:
        files = request.files.getlist('receipt_files')
        
        # �ִ� 3�� ���� ����
        if len(files) > 3:
            return jsonify({"error": "�ִ� 3���� ���ϸ� ���ε� �����մϴ�."}), 400
        
        for file in files:
            if file and file.filename:
                # �̹��� ���� ���� üũ
                allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
                file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                
                if file_ext not in allowed_extensions:
                    return jsonify({"error": "�̹��� ���ϸ� ���ε� �����մϴ�."}), 400
                
                # ���ϸ� ������ ���� secure_filename ���
                filename = secure_filename(file.filename)
                # �ߺ� ������ ���� Ÿ�ӽ����� �߰�
                timestamp = str(int(time.time()))
                filename = f"{timestamp}_{filename}"
                
                # ���� ����
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                receipt_filenames.append(filename)
    
    # ���ϸ���� JSON ���·� ���� (���� ���� ����)
    receipt_data = ','.join(receipt_filenames) if receipt_filenames else None
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO Sales_Expenses 
            (expense_date, category, expense_type, amount, payment_method, description, receipt_image, registered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form.get('expense_date'), 
            request.form.get('expense_type'),  # category �ʵ�
            request.form.get('expense_type'),  # expense_type �ʵ� 
            request.form.get('amount'), 
            request.form.get('payment_method', '����ī��'),  # �⺻�� ����
            request.form.get('description'), 
            receipt_data, 
            user_id
        ))
        conn.commit()
        return jsonify({"success": True, "message": "��������� ��ϵǾ����ϴ�."})
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
        # ���� Ȯ��: ������ ����� ����̰ų� �������� ��츸 ���� ����
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM Sales_Expenses WHERE id = ?", (expense_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        # ���� ���ε� ó��
        receipt_filename = None
        if 'receipt_file' in request.files:
            file = request.files['receipt_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                receipt_filename = filename
        
        # ������ ���� ���ε���� ���� ��� ���� ���ϸ� ����
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
        return jsonify({"success": True, "message": "������� ������ �����Ǿ����ϴ�."})
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
        # ���� Ȯ��: ������ ����� ����̰ų� �������� ��츸 ���� ����
        if not check_permission(user_level, 'S'):
            existing = conn.execute(
                "SELECT registered_by FROM Sales_Expenses WHERE id = ?", (expense_id,)
            ).fetchone()
            if not existing or existing['registered_by'] != user_id:
                return jsonify({"error": "Permission denied"}), 403
        
        conn.execute("DELETE FROM Sales_Expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return jsonify({"success": True, "message": "��������� �����Ǿ����ϴ�."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- ��ô��� ��� CSV ó�� API ---
@app.route('/api/pioneering_targets_csv', methods=['GET', 'POST'])
def pioneering_targets_csv():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        # CSV �ٿ�ε�
        conn = get_db_connection()
        rows = conn.execute('''
            SELECT p.id, p.biz_no, b.company_name, p.visit_date, p.visitor_id, 
                   CASE WHEN p.is_visited = 1 THEN '�Ϸ�' ELSE '����' END as visit_status,
                   p.notes, p.registered_by, p.created_date
            FROM Pioneering_Targets p
            LEFT JOIN Company_Basic b ON REPLACE(p.biz_no, '-', '') = b.biz_no
            ORDER BY p.id
        ''').fetchall()
        conn.close()
        
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['��ȣ', '����ڹ�ȣ', 'ȸ���', '�湮����', '�湮��ID', '�湮����', '�޸�', '�����', '�����'])
        for row in rows:
            # ����ڹ�ȣ�� �湮���ڿ��� ������ ����
            biz_no = row['biz_no'].replace('-', '') if row['biz_no'] else ''
            visit_date = row['visit_date'].replace('-', '') if row['visit_date'] else ''
            
            cw.writerow([row['id'], biz_no, row['company_name'], visit_date, 
                        row['visitor_id'], row['visit_status'], row['notes'], row['registered_by'], row['created_date']])
        
        output = si.getvalue().encode('utf-8-sig')
        return Response(output, mimetype='text/csv', 
                       headers={"Content-Disposition": "attachment;filename=pioneering_targets.csv"})
    
    else:
        # CSV ���ε�
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '������ ���õ��� �ʾҽ��ϴ�.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '������ ���õ��� �ʾҽ��ϴ�.'}), 400
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': 'CSV ���ϸ� ���ε� �����մϴ�.'}), 400
        
        # ���ڵ� ���� �� ó��
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
                # �ʼ� �ʵ� Ȯ��
                if not all([row.get('����ڹ�ȣ'), row.get('�湮����'), row.get('�湮��ID')]):
                    continue
                
                # ����ڹ�ȣ�� �湮���� ���� ���� (������ �߰�)
                biz_no = row.get('����ڹ�ȣ', '').replace('-', '')
                if len(biz_no) == 10:  # �Ϲ� ����ڹ�ȣ
                    biz_no = f"{biz_no[:3]}-{biz_no[3:5]}-{biz_no[5:]}"
                elif len(biz_no) == 13:  # ���ε�Ϲ�ȣ
                    biz_no = f"{biz_no[:6]}-{biz_no[6:]}"
                
                visit_date = row.get('�湮����', '').replace('-', '')
                if len(visit_date) == 8:  # YYYYMMDD ����
                    visit_date = f"{visit_date[:4]}-{visit_date[4:6]}-{visit_date[6:]}"
                
                # �湮���¸� is_visited�� ��ȯ
                visit_status = row.get('�湮����', '����')
                is_visited = 1 if visit_status == '�Ϸ�' else 0
                
                conn.execute('''
                    INSERT INTO Pioneering_Targets (biz_no, visit_date, visitor_id, is_visited, notes, registered_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    biz_no, visit_date, row.get('�湮��ID'),
                    is_visited, row.get('�޸�', ''), user_id
                ))
                inserted += 1
            
            conn.commit()
            return jsonify({'success': True, 'message': f'{inserted}���� ��ô����� ��ϵǾ����ϴ�.', 'inserted': inserted})
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            conn.close()

# --- ������� CSV ó�� API ---
@app.route('/api/sales_expenses_csv', methods=['GET', 'POST'])
def sales_expenses_csv():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        # CSV �ٿ�ε�
        conn = get_db_connection()
        user_id = session.get('user_id')
        user_level = session.get('user_level', 'N')
        
        # ���ѿ� ���� ��ȸ ���� ����
        if check_permission(user_level, 'S'):
            # �����ڴ� ��ü ��ȸ
            rows = conn.execute('''
                SELECT id, expense_date, expense_type, amount, payment_method, 
                       description, receipt_filename, registered_by, created_date
                FROM Sales_Expenses ORDER BY expense_date DESC
            ''').fetchall()
        else:
            # �Ϲ� ����ڴ� ���� ��ϰǸ� ��ȸ
            rows = conn.execute('''
                SELECT id, expense_date, expense_type, amount, payment_method, 
                       description, receipt_filename, registered_by, created_date
                FROM Sales_Expenses WHERE registered_by = ? ORDER BY expense_date DESC
            ''', (user_id,)).fetchall()
        
        conn.close()
        
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['��ȣ', '��¥', '�׸�', '�ݾ�', '�������', '����', '����������', '�����', '�����'])
        for row in rows:
            cw.writerow([row['id'], row['expense_date'], row['expense_type'], row['amount'], 
                        row['payment_method'], row['description'], row['receipt_filename'], 
                        row['registered_by'], row['created_date']])
        
        output = si.getvalue().encode('utf-8-sig')
        return Response(output, mimetype='text/csv', 
                       headers={"Content-Disposition": "attachment;filename=sales_expenses.csv"})
    
    else:
        # CSV ���ε�
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '������ �����ϴ�.'}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': 'CSV ���ϸ� ���ε� �����մϴ�.'}), 400
        
        # ���ڵ� ���� �� ó��
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
                # �ʼ� �ʵ� Ȯ��
                if not all([row.get('��¥'), row.get('�׸�'), row.get('�ݾ�')]):
                    continue
                
                conn.execute('''
                    INSERT INTO Sales_Expenses (expense_date, expense_type, amount, payment_method, description, registered_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('��¥'), row.get('�׸�'), row.get('�ݾ�'),
                    row.get('�������', '����'), row.get('����', ''), user_id
                ))
                inserted += 1
            
            conn.commit()
            return jsonify({'success': True, 'message': f'{inserted}���� ��������� ��ϵǾ����ϴ�.', 'inserted': inserted})
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            conn.close()

@app.route('/api/change-password', methods=['POST'])
def api_change_password():
    """��й�ȣ ���� API"""
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "�α����� �ʿ��մϴ�."}), 401
    
    data = request.get_json()
    new_password = data.get('new_password')
    
    if not new_password:
        return jsonify({"success": False, "message": "�� ��й�ȣ�� �Է����ּ���."}), 400
    
    # ��й�ȣ ���⼺ �˻�
    import re
    password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,20}$'
    if not re.match(password_pattern, new_password):
        return jsonify({"success": False, "message": "��й�ȣ�� 8-20�ڸ��� �빮��, �ҹ���, ����, Ư�����ڸ� ��� �����ؾ� �մϴ�."}), 400
    
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    try:
        # ����� ���� Ȯ��
        user = conn.execute("SELECT password FROM Users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            return jsonify({"success": False, "message": "����ڸ� ã�� �� �����ϴ�."}), 404
        
        # ���� ��й�ȣ�� �������� Ȯ�� (������ ���� �ź�)
        if user['password'] == new_password:
            return jsonify({"success": False, "message": "���� ��й�ȣ�� �ٸ� ��й�ȣ�� �Է����ּ���."}), 400
        
        # �� ��й�ȣ�� ������Ʈ
        conn.execute("""
            UPDATE Users 
            SET password = ?, password_changed_date = CURRENT_TIMESTAMP, updated_date = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (new_password, user_id))
        
        conn.commit()
        
        # ���� �ʱ�ȭ (�ٽ� �α����ϵ���)
        session.clear()
        
        return jsonify({"success": True, "message": "��й�ȣ�� ���������� ����Ǿ����ϴ�."})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # �� ���� �� ���̺� �ʱ�ȭ
    init_user_tables()
    init_business_tables()
    app.run(host='0.0.0.0', port=5000, debug=True)