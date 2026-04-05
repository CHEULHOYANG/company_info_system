# -*- coding: utf-8 -*-
"""
Integrated Batch Data Upload Script (v2) - Enhanced
- Supports XLSX input for data tables
- Modes: 'validate' (generation + dry-run/count) and 'execute' (DB update)
- Returns JSON statistics for backend parsing
"""

import os
import sys
import subprocess
import time
import sqlite3
import pandas as pd
import shutil
import json
import argparse
from datetime import datetime

# Configuration
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_PATH relative to data directory (one level up)
DB_PATH = os.path.join(os.path.dirname(DATA_DIR), "company_database.db")

# Scripts to run for Generation
GENERATION_SCRIPTS = [
    "basic.py",                    # Company_Basic
    "fanance.py",                  # Company_Financial
    "Company_Additional.py",       # Company_Additional
    "Company_Representative.py",   # Company_Representative
    "Company_Shareholder.py"       # Company_Shareholder
]

# File Mapping (Preferred: XLSX, Fallback: CSV)
# Key matches the table name text used in logic
TABLE_FILES = {
    "Company_Basic": ["Company_Basic_Output.xlsx", "Company_Basic_Output.csv"],
    "Company_Financial": ["Company_Financial_Output.xlsx", "Company_Financial_Output.csv"],
    "Company_Shareholder": ["Company_Shareholder_Output.xlsx", "Company_Shareholder_Output.csv"],
    "Company_Representative": ["Company_Representative_Output.xlsx", "Company_Representative_Output.csv"],
    "Company_Additional": ["Company_Additional_Output.xlsx", "Company_Additional_Output.csv"]
}

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    # Prefix regular logs so frontend can filter if needed, 
    # but for now we just print.
    print(f"[{timestamp}] {message}", flush=True)

def json_result(key, value):
    """Print a JSON object on a separate line for the backend to parse"""
    print(json.dumps({"type": "result", "key": key, "value": value}), flush=True)

def progress_event(event_type, table, **kwargs):
    """Print a progress event for real-time UI updates"""
    data = {"type": event_type, "table": table}
    data.update(kwargs)
    print(json.dumps(data), flush=True)

def cleanup_old_files():
    """Delete existing Output files to ensure fresh generation"""
    log("Cleaning up old Output files...")
    for key, files in TABLE_FILES.items():
        for filename in files:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                    # log(f"  Deleted old {filename}")
                except Exception as e:
                    log(f"  Warning: Could not delete {filename}: {e}")

def check_source_file():
    source_file = "251102_insert.xlsx"
    if os.path.exists(source_file):
        size_mb = os.path.getsize(source_file) / (1024 * 1024)
        mtime = datetime.fromtimestamp(os.path.getmtime(source_file)).strftime('%Y-%m-%d %H:%M:%S')
        log(f"Source File: {source_file} ({size_mb:.2f} MB)")
        return True
    else:
        log(f"ERROR: Source file {source_file} not found!")
        return False

def run_generation_scripts():
    """Optimized: Executes the conversion logic using Pandas directly for speed"""
    log("=== Step 1: generating Output files from Excel (Optimized) ===")
    source_file = "251102_insert.xlsx"
    
    try:
        import pandas as pd
        log("Reading source Excel...")
        # Read the main sheet. Skip first 2 rows to start data at row 3 (0-indexed 2)
        # We read the whole sheet into memory once.
        df_source = pd.read_excel(source_file, sheet_name="법인사업자", header=None)
        # Data starts from row index 2
        df_data = df_source.iloc[2:].copy()
        
        # 1. Company_Basic (using mapping)
        log("Generating Company_Basic...")
        mapping_file = "company_basic.xlsx"
        if os.path.exists(mapping_file):
            df_mapping = pd.read_excel(mapping_file, sheet_name="company_basic")
            mapping_dict = {} # csv_header -> source_col (1-indexed)
            for _, row in df_mapping.iterrows():
                if pd.notna(row[0]) and pd.notna(row[1]):
                    mapping_dict[str(row[0]).strip()] = int(row[1])
            
            # Forced / Manual mapping as in basic.py
            manual = {
                "biz_no": 24, "company_name": 2, "company_size": 3, "company_type": 4,
                "corporate_reg_no": 25, "establish_date": 26, "industry_code": 31,
                "industry_name": 32, "zip_code": 33, "jibun_address": 34, "address": 35,
                "region": 36, "city_district": 37, "phone_number": 38, "email": 39,
                "fax_number": 40, "representative_name": 44, "national_pension": 20,
                "pension_count": 22, "employee_count": 22, "pension_date": 23,
                "ked_transaction_yn": 161, "patent_transaction_yn": 164, "group_transaction_yn": 167,
                "gfc_transaction_yn": 168
            }
            mapping_dict.update(manual)
            
            basic_rows = []
            headers = list(mapping_dict.keys())
            for _, row in df_data.iterrows():
                # Col indices in mapping are 1-based, pandas iloc is 0-based
                biz_no_val = row.iloc[24-1]
                if pd.notna(biz_no_val) and str(biz_no_val).strip() != "0":
                    item = []
                    for h in headers:
                        col_idx = mapping_dict[h] - 1
                        val = row.iloc[col_idx] if col_idx < len(row) else ""
                        if h == "establish_date" and isinstance(val, (datetime, pd.Timestamp)):
                            val = val.strftime('%Y-%m-%d')
                        item.append(val)
                    basic_rows.append(item)
            pd.DataFrame(basic_rows, columns=headers).to_excel("Company_Basic_Output.xlsx", index=False)
            pd.DataFrame(basic_rows, columns=headers).to_csv("Company_Basic_Output.csv", index=False)

        # 2. Company_Financial
        log("Generating Company_Financial...")
        fin_rows = []
        fin_headers = ["biz_no", "fiscal_year", "rating1", "rating2", "rating3", "sales_revenue", "operating_income", "net_income", "total_assets", "total_liabilities", "total_equity", "retained_earnings", "capital_surplus", "earned_reserve", "additional_paid_in_capital", "corporate_tax", "land_asset", "building_asset", "investment_real_ground", "investment_real_building", "rental_income", "rent_amt", "advances_paid", "advances_received", "capital_stock_value", "undistributed_retained_earnings", "current_assets", "cash_equivalents", "short_term_loan", "short_term_deposit", "principal_short_long_term_bonds", "interest_income", "capital_reserve", "shares_issued_count"]
        for _, row in df_data.iterrows():
            biz_no = str(row.iloc[24-1]).strip()
            if biz_no and biz_no != "0":
                # Static data
                r1 = str(row.iloc[7-1]) if pd.notna(row.iloc[7-1]) else ""
                r2 = str(row.iloc[6-1]) if pd.notna(row.iloc[6-1]) else ""
                r3 = str(row.iloc[5-1]) if pd.notna(row.iloc[5-1]) else ""
                
                def get_n(v, m=1000):
                    try: return float(v) * m if pd.notna(v) else 0
                    except: return 0
                
                # Shared among years
                ta = get_n(row.iloc[139-1]); tl = get_n(row.iloc[137-1]); cs = get_n(row.iloc[138-1])
                er = get_n(row.iloc[125-1]); apic = get_n(row.iloc[126-1]); la = get_n(row.iloc[117-1])
                ba = get_n(row.iloc[118-1]); irg = get_n(row.iloc[119-1]); irb = get_n(row.iloc[120-1])
                ri = get_n(row.iloc[121-1]); ramt = get_n(row.iloc[122-1]); adp = get_n(row.iloc[127-1])
                adr = get_n(row.iloc[128-1]); csv = get_n(row.iloc[129-1]); ure = get_n(row.iloc[130-1])
                ca = get_n(row.iloc[131-1]); ce = get_n(row.iloc[132-1]); stl = get_n(row.iloc[133-1])
                std = get_n(row.iloc[134-1]); sltb = get_n(row.iloc[135-1]); ii = get_n(row.iloc[136-1])
                cr = get_n(row.iloc[138-1]); sic = get_n(row.iloc[140-1], 1)

                years = [
                    (2024, 100, 101, 102, 123, 144), # User logic was 100,101,102...
                    (2023, 103, 104, 105, 123, 145),
                    (2022, 106, 107, 108, 123, 146)
                ]
                for yr, s_col, o_col, e_col, r_col, t_col in years:
                    sales = get_n(row.iloc[s_col-1], 1000000)
                    op_inc = get_n(row.iloc[o_col-1], 1000000)
                    te = get_n(row.iloc[e_col-1])
                    ret = get_n(row.iloc[r_col-1])
                    tax = get_n(row.iloc[t_col-1])
                    fin_rows.append([biz_no, yr, r1, r2, r3, sales, op_inc, op_inc, ta, tl, te, ret, cs, er, apic, tax, la, ba, irg, irb, ri, ramt, adp, adr, csv, ure, ca, ce, stl, std, sltb, ii, cr, sic])
        pd.DataFrame(fin_rows, columns=fin_headers).to_excel("Company_Financial_Output.xlsx", index=False)

        # 3. Company_Representative
        log("Generating Company_Representative...")
        rep_rows = []
        rep_headers = ["biz_no", "name", "gender", "age", "is_gfc", "birth_date"]
        for _, row in df_data.iterrows():
            biz_no = str(row.iloc[24-1]).strip()
            if biz_no and biz_no != "0":
                name = str(row.iloc[44-1]).strip() if pd.notna(row.iloc[44-1]) else ""
                if name:
                    gender = "M" if "남" in str(row.iloc[45-1]) else ("F" if "여" in str(row.iloc[45-1]) else "")
                    age = int(row.iloc[46-1]) if pd.notna(row.iloc[46-1]) else 0
                    rep_rows.append([biz_no, name, gender, age, "N", ""])
        pd.DataFrame(rep_rows, columns=rep_headers).to_excel("Company_Representative_Output.xlsx", index=False)

        # 4. Company_Shareholder
        log("Generating Company_Shareholder...")
        sha_rows = []
        sha_headers = ["biz_no", "shareholder_name", "ownership_percent", "relationship", "shareholder_type", "management_type", "silent_partner_relationship"]
        # In Shareholder.py: Rep1=44, Rep2=52, Rep3=60. SH1=65... (each 7 cols)
        for _, row in df_data.iterrows():
            biz_no = str(row.iloc[24-1]).strip()
            if biz_no and biz_no != "0":
                # Get Rep names for "representative-shareholder same" check
                rep1 = str(row.iloc[44-1]).strip() if pd.notna(row.iloc[44-1]) else ""
                rep2 = str(row.iloc[52-1]).strip() if pd.notna(row.iloc[52-1]) else ""
                rep3 = str(row.iloc[60-1]).strip() if pd.notna(row.iloc[60-1]) else ""
                reps = [rep1, rep2, rep3]

                # SH1=65, SH2=72, SH3=79, SH4=86, SH5=93
                for idx, start_col in enumerate([65, 72, 79, 86, 93]):
                    name = str(row.iloc[start_col-1]).strip() if pd.notna(row.iloc[start_col-1]) else ""
                    if name and name != "0":
                        rel = str(row.iloc[start_col+1-1]) if pd.notna(row.iloc[start_col+1-1]) else ""
                        sil_rel = str(row.iloc[start_col+2-1]) if pd.notna(row.iloc[start_col+2-1]) else ""
                        perc = get_n(row.iloc[start_col+6-1], 1)
                        m_type = "대표자-주주 동일" if name in reps else ""
                        sha_rows.append([biz_no, name, perc, rel, f"주주{idx+1}", m_type, sil_rel])
        pd.DataFrame(sha_rows, columns=sha_headers).to_excel("Company_Shareholder_Output.xlsx", index=False)

        # 5. Company_Additional
        log("Generating Company_Additional...")
        add_rows = []
        add_headers = ["biz_no", "patent_applications_count", "registered_patents_count", "has_research_institute", "research_institute_date", "is_innobiz", "innobiz_cert_date", "innobiz_expiry_date", "is_mainbiz", "mainbiz_cert_date", "mainbiz_expiry_date", "is_venture", "venture_cert_date", "venture_expiry_date", "group_agreement_yn", "gfc_yn"]
        for _, row in df_data.iterrows():
            biz_no = str(row.iloc[24-1]).strip()
            if biz_no and biz_no != "0":
                def get_b(v): 
                    s = str(v).strip().upper() if pd.notna(v) else ""
                    return "1" if s in ["Y", "1", "YES", "TRUE", "여"] else "0"
                def get_d(v):
                    if isinstance(v, (datetime, pd.Timestamp)): return v.strftime('%Y-%m-%d')
                    return str(v).strip() if pd.notna(v) and str(v).strip() != "0" else ""
                
                item = [
                    biz_no,
                    get_n(row.iloc[166-1], 1), get_n(row.iloc[165-1], 1),
                    get_b(row.iloc[153-1]), get_d(row.iloc[154-1]),
                    get_b(row.iloc[155-1]), get_d(row.iloc[156-1]), get_d(row.iloc[157-1]),
                    get_b(row.iloc[158-1]), get_d(row.iloc[159-1]), get_d(row.iloc[160-1]),
                    get_b(row.iloc[161-1]), get_d(row.iloc[162-1]), get_d(row.iloc[163-1]),
                    get_b(row.iloc[167-1]), get_b(row.iloc[168-1])
                ]
                add_rows.append(item)
        pd.DataFrame(add_rows, columns=add_headers).to_excel("Company_Additional_Output.xlsx", index=False)

        log("Generation complete (Optimized).")
        return True
        
    except Exception as e:
        log(f"CRITICAL ERROR in optimized generation: {e}")
        import traceback
        log(traceback.format_exc())
        return False

def load_data_frame(table_name):
    """Smart loader: tries XLSX then CSV"""
    files = TABLE_FILES.get(table_name, [])
    for f in files:
        if os.path.exists(f):
            try:
                if f.endswith('.xlsx'):
                    return pd.read_excel(f)
                else:
                    return pd.read_csv(f) # Default utf-8
            except Exception as e:
                log(f"Error reading {f}: {e}")
    return None

def ensure_base_tables(conn):
    """Create necessary tables if they don't exist"""
    cursor = conn.cursor()
    
    # Company_Basic
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Company_Basic (
            biz_no VARCHAR(12) PRIMARY KEY,
            company_name VARCHAR(255),
            company_size VARCHAR(50),
            company_type VARCHAR(50),
            industry_code VARCHAR(10),
            industry_name VARCHAR(255),
            zip_code VARCHAR(10),
            jibun_address VARCHAR(500),
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
        )
    ''')

    # Company_Financial
    cursor.execute('''
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
        )
    ''')

    # Company_Shareholder
    cursor.execute('''
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
        )
    ''')

    # Company_Representative
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Company_Representative (
            company_representative_id INTEGER PRIMARY KEY,
            biz_no VARCHAR(12),
            name VARCHAR(100),
            gender CHAR(1),
            age INTEGER,
            birth_date DATE,
            is_gfc CHAR(1),
            FOREIGN KEY (biz_no) REFERENCES Company_Basic (biz_no)
        )
    ''')

    # Company_Additional
    cursor.execute('''
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
        )
    ''')
    conn.commit()

    # [Migration] Ensure jibun_address exists in Company_Basic
    cursor.execute("PRAGMA table_info(Company_Basic)")
    cols = [row[1] for row in cursor.fetchall()]
    if "jibun_address" not in cols:
        try:
            cursor.execute("ALTER TABLE Company_Basic ADD COLUMN jibun_address VARCHAR(500)")
            conn.commit()
            log("Added jibun_address column to Company_Basic table via migration.")
        except Exception as e:
            log(f"Migration error: {e}")

def connect_db():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        ensure_base_tables(conn)
        return conn
    except Exception as e:
        log(f"Database connection failed: {e}")
        return None

def is_masked(name):
    return '*' in str(name)

def fuzzy_name_match(masked_name, real_name):
    if not masked_name or not real_name:
        return False
    s_masked = str(masked_name).strip()
    s_real = str(real_name).strip()
    if len(s_masked) < 2 or len(s_real) < 2:
        return s_masked == s_real
    return s_masked[0] == s_real[0] and s_masked[-1] == s_real[-1]

# ---------------- Processing Functions ----------------

def process_company_basic(conn, df, execute=False):
    log("Processing Company_Basic...")
    
    # Pre-processing
    if 'biz_no' in df.columns:
        df['biz_no'] = df['biz_no'].astype(str).str.replace(r'[\s-]', '', regex=True)
    
    total_rows = len(df)
    log(f"  Found {total_rows} rows")
    json_result("Company_Basic_Found", total_rows)
    
    if not execute or conn is None:
        return {"found": total_rows, "updated": 0, "inserted": 0, "error": 0}

    # Emit table start event
    progress_event("table_start", "Company_Basic", total=total_rows)

    cursor = conn.cursor()
    count_updated = 0
    count_inserted = 0
    count_error = 0
    
    cursor.execute("PRAGMA table_info(Company_Basic)")
    db_cols = [row[1] for row in cursor.fetchall()]

    for i, (_, row) in enumerate(df.iterrows()):
        if (i + 1) % 50 == 0:
            print(".", end="", flush=True)
        
        # Emit progress every 10 rows
        if (i + 1) % 10 == 0 or i == 0:
            progress_event("progress", "Company_Basic", current=i+1, total=total_rows)
            
        biz_no = row.get('biz_no')
        if not biz_no:
            count_error += 1
            if count_error == 1: json_result("LastError", f"[Company_Basic] BizNo missing. Row: {row.to_dict()}")
            continue
        
        try:
            cursor.execute("SELECT 1 FROM Company_Basic WHERE biz_no = ?", (biz_no,))
            exists = cursor.fetchone()
            
            data_to_save = {}
            for col in db_cols:
                if col in row:
                    data_to_save[col] = row[col]
            
            if exists:
                # UPDATE
                update_data = {k: v for k, v in data_to_save.items() if k != 'biz_no'}
                if update_data:
                    set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
                    values = list(update_data.values()) + [biz_no]
                    cursor.execute(f"UPDATE Company_Basic SET {set_clause} WHERE biz_no = ?", values)
                    count_updated += 1
            else:
                # INSERT
                cols = list(data_to_save.keys())
                placeholders = ", ".join(["?" for _ in cols])
                values = list(data_to_save.values())
                cursor.execute(f"INSERT INTO Company_Basic ({', '.join(cols)}) VALUES ({placeholders})", values)
                count_inserted += 1
        except Exception as e:
            count_error += 1
            if count_error == 1: json_result("LastError", f"[Company_Basic] {str(e)}")
            log(f"  [Error] Basic biz_no={biz_no}: {e}")
            
    conn.commit()
    print("") # Newline after dots
    log(f"  Inserted: {count_inserted}, Updated: {count_updated}, Errors: {count_error}")
    json_result("Company_Basic_Inserted", count_inserted)
    json_result("Company_Basic_Updated", count_updated)
    json_result("Company_Basic_Error", count_error)
    progress_event("table_done", "Company_Basic", inserted=count_inserted, updated=count_updated, error=count_error)
    return {"found": total_rows, "updated": count_updated, "inserted": count_inserted, "error": count_error}

def process_company_representative(conn, df, execute=False):
    log("Processing Company_Representative...")
    if 'biz_no' in df.columns:
        df['biz_no'] = df['biz_no'].astype(str).str.replace(r'[\s-]', '', regex=True)
    
    total_rows = len(df)
    log(f"  Found {total_rows} rows")
    json_result("Company_Representative_Found", total_rows)

    if not execute or conn is None:
        return

    cursor = conn.cursor()
    count_inserted = 0
    count_updated = 0
    count_error = 0
    
    # Emit table start event
    progress_event("table_start", "Company_Representative", total=total_rows)
    
    for i, (_, row) in enumerate(df.iterrows()):
        if (i + 1) % 50 == 0: print(".", end="", flush=True)
        if (i + 1) % 10 == 0 or i == 0:
            progress_event("progress", "Company_Representative", current=i+1, total=total_rows)

        biz_no = row.get('biz_no')
        new_name = str(row.get('name', '')).strip()
        if not new_name:
            count_error += 1
            if count_error == 1: json_result("LastError", f"[Company_Representative] Name missing. Row: {row.to_dict()}")
            continue
            
        try:
            cursor.execute("SELECT company_representative_id, name FROM Company_Representative WHERE biz_no = ?", (biz_no,))
            existing_reps = cursor.fetchall()
            
            match_found = False
            target_id = None
            
            # 1. Exact Match
            for rid, rname in existing_reps:
                if rname == new_name:
                    match_found = True; target_id = rid; break
            
            # 2. Masked Match
            if not match_found and is_masked(new_name):
                for rid, rname in existing_reps:
                    if not is_masked(rname) and fuzzy_name_match(new_name, rname):
                        match_found = True; target_id = rid
                        row['name'] = rname # Keep DB name
                        break
            
            if target_id:
                # Update (simple fields)
                sql = "UPDATE Company_Representative SET gender=?, age=?, is_gfc=? WHERE company_representative_id=?"
                cursor.execute(sql, (row.get('gender',''), row.get('age',0), row.get('is_gfc','N'), target_id))
                count_updated += 1
            else:
                # Insert
                sql = "INSERT INTO Company_Representative (biz_no, name, gender, age, is_gfc, birth_date) VALUES (?, ?, ?, ?, ?, ?)"
                cursor.execute(sql, (biz_no, new_name, row.get('gender',''), row.get('age',0), row.get('is_gfc','N'), row.get('birth_date','')))
                count_inserted += 1
        except Exception as e:
            count_error += 1
            if count_error == 1: json_result("LastError", f"[Company_Representative] {str(e)}")
            log(f"  [Error] Rep biz_no={biz_no}: {e}")
        
    conn.commit()
    print("")
    log(f"  Inserted: {count_inserted}, Updated: {count_updated}, Errors: {count_error}")
    json_result("Company_Representative_Inserted", count_inserted)
    json_result("Company_Representative_Updated", count_updated)
    json_result("Company_Representative_Error", count_error)
    progress_event("table_done", "Company_Representative", inserted=count_inserted, updated=count_updated, error=count_error)

def process_company_shareholder(conn, df, execute=False):
    log("Processing Company_Shareholder...")
    if 'biz_no' in df.columns:
        df['biz_no'] = df['biz_no'].astype(str).str.replace(r'[\s-]', '', regex=True)
        
    total_rows = len(df)
    log(f"  Found {total_rows} rows")
    json_result("Company_Shareholder_Found", total_rows)
    
    if not execute or conn is None:
        return

    cursor = conn.cursor()
    count_inserted = 0
    count_updated = 0
    count_error = 0
    
    # Emit table start event
    progress_event("table_start", "Company_Shareholder", total=total_rows)
    
    # Strategy: Delete & Re-insert for involved companies
    # 1. Identify companies in this batch
    unique_biz_nos = df['biz_no'].unique().tolist()
    if not unique_biz_nos:
        return
        
    log(f"  Deleting existing shareholders for {len(unique_biz_nos)} companies...")
    
    # Chunk the delete to avoid "too many SQL variables"
    DELETE_CHUNK = 500
    for i in range(0, len(unique_biz_nos), DELETE_CHUNK):
        chunk = unique_biz_nos[i:i + DELETE_CHUNK]
        placeholders = ','.join(['?'] * len(chunk))
        cursor.execute(f"DELETE FROM Company_Shareholder WHERE biz_no IN ({placeholders})", chunk)
    
    # 2. Bulk Insert New Data
    log("  Inserting new shareholder data...")
    
    CHUNK_SIZE = 100
    insert_data_list = []
    insert_cols = ['biz_no', 'shareholder_name', 'ownership_percent', 'relationship', 
                   'shareholder_type', 'management_type', 'silent_partner_relationship', 'total_shares_owned']
                   
    for i, (_, row) in enumerate(df.iterrows()):
        if (i + 1) % 50 == 0: print(".", end="", flush=True)
        if (i + 1) % 10 == 0 or i == 0:
            progress_event("progress", "Company_Shareholder", current=i+1, total=total_rows)
            
        biz_no = row.get('biz_no')
        csv_name = str(row.get('shareholder_name', '')).strip()
        
        # Skip invalid rows
        if not csv_name:
            count_error += 1
            continue

        csv_stock = 0
        if 'total_shares_owned' in row:
             try: csv_stock = int(float(str(row['total_shares_owned']).replace(',', '')))
             except: csv_stock = 0

        # Prepare Data
        vals = [
            biz_no,
            csv_name,
            row.get('ownership_percent', 0),
            row.get('relationship', ''),
            row.get('shareholder_type', ''),
            row.get('management_type', ''),
            row.get('silent_partner_relationship', ''),
            csv_stock
        ]
        
        insert_data_list.append(vals)
        count_inserted += 1 # We treat all as inserted now

        # Execute Chunk
        if len(insert_data_list) >= CHUNK_SIZE:
             placeholders = ", ".join(["?" for _ in insert_cols])
             cursor.executemany(f"INSERT INTO Company_Shareholder ({', '.join(insert_cols)}) VALUES ({placeholders})", insert_data_list)
             insert_data_list = []
             conn.commit() # Intermediate Save

    # Final Flush
    if insert_data_list:
        try:
            placeholders = ", ".join(["?" for _ in insert_cols])
            cursor.executemany(f"INSERT INTO Company_Shareholder ({', '.join(insert_cols)}) VALUES ({placeholders})", insert_data_list)
        except Exception as e:
            log(f"  [Error] Final Bulk Insert failed: {e}")
            count_error += len(insert_data_list) # Rough estimate

    conn.commit()
    print("")
    log(f"  Inserted: {count_inserted}, Updated: 0 (Replaced), Errors: {count_error}")
    json_result("Company_Shareholder_Inserted", count_inserted)
    json_result("Company_Shareholder_Updated", 0)
    json_result("Company_Shareholder_Error", count_error)
    progress_event("table_done", "Company_Shareholder", inserted=count_inserted, updated=0, error=count_error)

def process_company_financial(conn, df, execute=False):
    log("Processing Company_Financial...")
    if 'biz_no' in df.columns:
        df['biz_no'] = df['biz_no'].astype(str).str.replace(r'[\s-]', '', regex=True)
    
    total_rows = len(df)
    log(f"  Found {total_rows} rows")
    json_result("Company_Financial_Found", total_rows)
    
    if not execute or conn is None:
        return

    cursor = conn.cursor()
    
    # Get columns dynamically
    cursor.execute("PRAGMA table_info(Company_Financial)")
    db_cols = [row[1] for row in cursor.fetchall() if row[1] != 'company_financial_id']

    count_inserted = 0
    count_updated = 0
    count_error = 0
    
    # Emit table start event
    progress_event("table_start", "Company_Financial", total=total_rows)
    
    # Strategy: Delete & Re-insert for involved (biz_no, fiscal_year)
    # 1. Identify unique keys in this batch
    keys_to_delete = df[['biz_no', 'fiscal_year']].drop_duplicates().values.tolist()
    if not keys_to_delete:
        return

    log(f"  Deleting existing financials for {len(keys_to_delete)} records...")
    
    # Chunk the delete
    DELETE_CHUNK = 500
    for i in range(0, len(keys_to_delete), DELETE_CHUNK):
        chunk = keys_to_delete[i:i + DELETE_CHUNK]
        # For composite key delete, it's tricker in SQLite without tuple syntax validation
        # simpler to loop or use reduced logic? 
        # Actually standard SQL: DELETE FROM table WHERE (col1, col2) IN ((val1, val2), ...) is supported in newer SQLite
        # But safest is: DELETE FROM table WHERE biz_no = ? AND fiscal_year = ?
        cursor.executemany("DELETE FROM Company_Financial WHERE biz_no = ? AND fiscal_year = ?", chunk)
        
    # 2. Bulk Insert New Data
    log("  Inserting new financial data...")
    
    CHUNK_SIZE = 100
    insert_data_list = []
    # Dynamic columns based on DB schema + trusting DF columns match DB cols roughly
    # We should stick to DB cols order
    insert_cols = [col for col in db_cols if col != 'company_financial_id'] # ID is auto-inc
    
    for i, (_, row) in enumerate(df.iterrows()):
        if (i + 1) % 50 == 0: print(".", end="", flush=True)
        if (i + 1) % 10 == 0 or i == 0:
            progress_event("progress", "Company_Financial", current=i+1, total=total_rows)
        
        biz_no = row.get('biz_no')
        fiscal_year = row.get('fiscal_year')
        
        if not biz_no or not fiscal_year:
            count_error += 1
            continue

        data_list = []
        for col in insert_cols:
            val = row.get(col)
            if pd.isna(val): val = None
            elif hasattr(val, 'item'): val = val.item()
            data_list.append(val)
            
        insert_data_list.append(data_list)
        count_inserted += 1

        # Execute Chunk
        if len(insert_data_list) >= CHUNK_SIZE:
             placeholders = ", ".join(["?" for _ in insert_cols])
             cursor.executemany(f"INSERT INTO Company_Financial ({', '.join(insert_cols)}) VALUES ({placeholders})", insert_data_list)
             insert_data_list = []
             conn.commit()

    # Final Flush
    if insert_data_list:
        try:
            placeholders = ", ".join(["?" for _ in insert_cols])
            cursor.executemany(f"INSERT INTO Company_Financial ({', '.join(insert_cols)}) VALUES ({placeholders})", insert_data_list)
        except Exception as e:
            log(f"  [Error] Final Bulk Insert failed: {e}")
            count_error += len(insert_data_list)

    conn.commit()
    print("")
    log(f"  Inserted: {count_inserted}, Updated: 0 (Replaced), Errors: {count_error}")
    json_result("Company_Financial_Inserted", count_inserted)
    json_result("Company_Financial_Updated", 0)
    json_result("Company_Financial_Error", count_error)
    progress_event("table_done", "Company_Financial", inserted=count_inserted, updated=0, error=count_error)

def process_generic_table(conn, df, table_name, pk_cols, execute=False):
    log(f"Processing {table_name}...")
    if 'biz_no' in df.columns:
        df['biz_no'] = df['biz_no'].astype(str).str.replace(r'[\s-]', '', regex=True)
    df.columns = df.columns.str.strip()
    
    total_rows = len(df)
    log(f"  Found {total_rows} rows")
    json_result(f"{table_name}_Found", total_rows)
    
    if not execute or conn is None:
        return

    # Multiplier logic for Financial (Implicitly handled by generation script, we trust the Input DF)

    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    db_cols = [row[1] for row in cursor.fetchall()]

    count_inserted = 0
    count_updated = 0
    count_error = 0
    
    # Emit table start event
    progress_event("table_start", table_name, total=total_rows)
    
    for i, (_, row) in enumerate(df.iterrows()):
        if (i + 1) % 50 == 0: print(".", end="", flush=True)
        if (i + 1) % 10 == 0 or i == 0:
            progress_event("progress", table_name, current=i+1, total=total_rows)
        
        try:
            where_parts = [f"{pk} = ?" for pk in pk_cols]
            where_vals = [row[pk] for pk in pk_cols]
            
            cursor.execute(f"SELECT count(*) FROM {table_name} WHERE {' AND '.join(where_parts)}", where_vals)
            exists = cursor.fetchone()[0] > 0
            
            data = {col: row[col] for col in db_cols if col in row}
            
            if exists:
                update_data = {k: v for k, v in data.items() if k not in pk_cols}
                if update_data:
                    set_parts = [f"{k}=?" for k in update_data.keys()]
                    sql = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
                    cursor.execute(sql, list(update_data.values()) + where_vals)
                    count_updated += 1
            else:
                cols = list(data.keys())
                placeholders = ",".join(["?" for _ in cols])
                sql = f"INSERT INTO {table_name} ({','.join(cols)}) VALUES ({placeholders})"
                cursor.execute(sql, list(data.values()))
                count_inserted += 1
        except Exception as e:
            count_error += 1
            if count_error == 1: json_result("LastError", f"[{table_name}] {str(e)}")
            log(f"  [Error] {table_name} row {i}: {e}")
        
    conn.commit()
    print("")
    log(f"  Inserted: {count_inserted}, Updated: {count_updated}, Errors: {count_error}")
    json_result(f"{table_name}_Inserted", count_inserted)
    json_result(f"{table_name}_Updated", count_updated)
    json_result(f"{table_name}_Error", count_error)
    progress_event("table_done", table_name, inserted=count_inserted, updated=count_updated, error=count_error)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=['validate', 'execute'], default='validate', help="Operation mode")
    parser.add_argument("--skip-gen", action="store_true", help="Skip generation step")
    parser.add_argument("--db-path", type=str, help="Absolute path to the SQLite database")
    args = parser.parse_args()

    mode = args.mode
    
    # Update DB_PATH if provided
    global DB_PATH
    if args.db_path:
        DB_PATH = args.db_path
        
    log(f"=== Batch Upload V2 Started (Mode: {mode}) ===")
    log(f"Database Path: {DB_PATH}")
    
    # Verify DB exists
    if mode == 'execute':
        if os.path.exists(DB_PATH):
            log(f"DB File exists: {os.path.getsize(DB_PATH)} bytes")
        else:
            log(f"WARNING: DB File NOT found at {DB_PATH}. It will be created on connect, but tables might be missing.")

    # 1. Validation Phase (Generation)
    if not check_source_file():
        return

    if not args.skip_gen:
        cleanup_old_files()
        if not run_generation_scripts():
            log("Generation failed or partial.")
            if mode == 'execute': 
                log("Aborting execution due to generation failure.")
                return

    # 2. Execution/Validation Phase
    log(f"=== Step 2: Processing Data (Mode: {mode}) ===")
    
    conn = None
    if mode == 'execute':
        conn = connect_db()
        if not conn:
            log("CRITICAL: Could not connect to database.")
            return

    # 1. Basic
    df_basic = load_data_frame("Company_Basic")
    if df_basic is not None:
        process_company_basic(conn, df_basic, execute=(mode == 'execute'))

    # 2. Representative
    df_rep = load_data_frame("Company_Representative")
    if df_rep is not None:
        process_company_representative(conn, df_rep, execute=(mode == 'execute'))
        
    # 3. Shareholder
    df_share = load_data_frame("Company_Shareholder")
    if df_share is not None:
        process_company_shareholder(conn, df_share, execute=(mode == 'execute'))

    # 4. Financial (New Logic)
    df_fin = load_data_frame("Company_Financial")
    if df_fin is not None:
        process_company_financial(conn, df_fin, execute=(mode == 'execute'))

    # 5. Additional
    df_add = load_data_frame("Company_Additional")
    if df_add is not None:
        process_generic_table(conn, df_add, "Company_Additional", ["biz_no"], execute=(mode == 'execute'))

    if conn:
        conn.close()
        
    log("=== Batch Upload Complete ===")

if __name__ == "__main__":
    main()
