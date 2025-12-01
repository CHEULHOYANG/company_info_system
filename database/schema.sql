-- Company Information Management System - Database Schema
-- Generated: 2025-12-01
-- This file contains all table definitions for the system

-- =====================================================
-- 1. Users & Authentication Tables
-- =====================================================

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
    email TEXT,
    position TEXT,
    hire_date TEXT DEFAULT (date('now')),
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    last_login DATETIME,
    password_changed_date TEXT DEFAULT (date('now')),
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Password_History (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    password TEXT NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

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
    position TEXT DEFAULT '∆¿¿Â',
    purpose TEXT,
    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    requested_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_date DATETIME,
    processed_by TEXT,
    admin_notes TEXT
);

CREATE TABLE IF NOT EXISTS User_Subscriptions (
    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    subscription_start_date DATE,
    subscription_end_date DATE,
    subscription_type TEXT DEFAULT 'MONTHLY' CHECK (subscription_type IN ('MONTHLY', 'YEARLY', 'FREE')),
    total_paid_amount INTEGER DEFAULT 0,
    is_first_month_free BOOLEAN DEFAULT 1,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

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
);

CREATE TABLE IF NOT EXISTS Branches (
    branch_code TEXT PRIMARY KEY,
    branch_name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    manager_id TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. Company Information Tables
-- =====================================================

CREATE TABLE IF NOT EXISTS Company_Basic (
    biz_no VARCHAR(12) PRIMARY KEY,
    company_name VARCHAR(255),
    company_size VARCHAR(50),
    company_type VARCHAR(50),
    industry_code VARCHAR(10),
    industry_name VARCHAR(255),
    zip_code VARCHAR(10),
    address VARCHAR(500),
    region VARCHAR(50),
    city_district VARCHAR(50),
    phone_number VARCHAR(20),
    email VARCHAR(255),
    fax_number VARCHAR(20),
    gfc_transaction_yn CHAR(1),
    group_transaction_yn CHAR(1),
    ked_transaction_yn CHAR(1),
    patent_transaction_yn CHAR(1),
    establish_date DATE,
    corporate_reg_no VARCHAR(20),
    representative_name VARCHAR(100),
    national_pension INTEGER,
    pension_count INTEGER,
    pension_date DATE
);

CREATE TABLE IF NOT EXISTS Company_Financial (
    biz_no VARCHAR(12),
    fiscal_year INTEGER,
    rating1 VARCHAR(20),
    rating2 VARCHAR(20),
    rating3 VARCHAR(20),
    sales_revenue BIGINT,
    operating_income BIGINT,
    net_income BIGINT,
    total_assets BIGINT,
    total_liabilities BIGINT,
    total_equity BIGINT,
    retained_earnings BIGINT,
    capital_surplus BIGINT,
    earned_reserve BIGINT,
    additional_paid_in_capital BIGINT,
    corporate_tax BIGINT,
    land_asset BIGINT,
    building_asset BIGINT,
    investment_real_ground BIGINT,
    investment_real_building BIGINT,
    rental_income BIGINT,
    rent_amt BIGINT,
    advances_paid BIGINT,
    advances_received BIGINT,
    capital_stock_value BIGINT,
    undistributed_retained_earnings BIGINT,
    current_assets BIGINT,
    cash_equivalents BIGINT,
    short_term_loan BIGINT,
    short_term_deposit BIGINT,
    principal_short_long_term_bonds BIGINT,
    interest_income BIGINT,
    capital_reserve BIGINT,
    shares_issued_count INTEGER,
    PRIMARY KEY (biz_no, fiscal_year),
    FOREIGN KEY (biz_no) REFERENCES Company_Basic (biz_no)
);

CREATE TABLE IF NOT EXISTS Company_Representative (
    company_representative_id INTEGER PRIMARY KEY,
    biz_no VARCHAR(12),
    name VARCHAR(100),
    gender CHAR(1),
    age INTEGER,
    birth_date DATE,
    is_gfc CHAR(1),
    FOREIGN KEY (biz_no) REFERENCES Company_Basic (biz_no)
);

CREATE TABLE IF NOT EXISTS Company_Shareholder (
    company_shareholder_id INTEGER PRIMARY KEY,
    biz_no VARCHAR(12),
    shareholder_name VARCHAR(100),
    ownership_percent NUMERIC,
    relationship VARCHAR(100),
    shareholder_type VARCHAR(50),
    management_type VARCHAR(50),
    silent_partner_relationship VARCHAR(100),
    total_shares_owned BIGINT,
    FOREIGN KEY (biz_no) REFERENCES Company_Basic (biz_no)
);

CREATE TABLE IF NOT EXISTS Company_Additional (
    company_additional_id INTEGER PRIMARY KEY,
    biz_no VARCHAR(12),
    patent_applications_count INTEGER,
    registered_patents_count INTEGER,
    has_research_institute CHAR(1),
    research_institute_date DATE,
    is_innobiz CHAR(1),
    innobiz_cert_date DATE,
    innobiz_expiry_date DATE,
    is_mainbiz CHAR(1),
    mainbiz_cert_date DATE,
    mainbiz_expiry_date DATE,
    is_venture CHAR(1),
    venture_cert_date DATE,
    venture_expiry_date DATE,
    FOREIGN KEY (biz_no) REFERENCES Company_Basic (biz_no)
);

-- =====================================================
-- 3. Contact & Sales Management Tables
-- =====================================================

CREATE TABLE IF NOT EXISTS Contact_History (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    biz_no TEXT,
    contact_datetime TEXT,
    contact_type TEXT,
    contact_person TEXT,
    memo TEXT,
    registered_by TEXT
);

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
);

CREATE TABLE IF NOT EXISTS Sales_Expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_date DATE NOT NULL,
    category TEXT NOT NULL,
    amount INTEGER NOT NULL,
    description TEXT,
    receipt_image TEXT,
    status TEXT DEFAULT 'PENDING',
    registered_by TEXT NOT NULL,
    approved_by TEXT,
    approved_date DATETIME,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    expense_type TEXT,
    payment_method TEXT,
    receipt_filename TEXT,
    FOREIGN KEY (registered_by) REFERENCES Users(user_id),
    FOREIGN KEY (approved_by) REFERENCES Users(user_id)
);

-- =====================================================
-- 4. Sales Pipeline Tables (NEW)
-- =====================================================

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
);

-- Legacy history table (for backward compatibility)
CREATE TABLE IF NOT EXISTS history (
    history_id INTEGER PRIMARY KEY,
    contact_datetime TEXT,
    biz_no TEXT,
    contact_type TEXT,
    contact_person TEXT,
    memo TEXT,
    registered_by TEXT
);
