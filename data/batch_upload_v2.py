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
    """Executes the Python scripts that convert Excel to Output Files"""
    log("=== Step 1: generating Output files from Excel ===")
    success_count = 0
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    for script in GENERATION_SCRIPTS:
        script_path = os.path.join(DATA_DIR, script)
        if not os.path.exists(script_path):
            log(f"ERROR: Script not found: {script}")
            continue
            
        try:
            log(f"Running {script}...")
            # Run using same python interpreter
            result = subprocess.run(
                [sys.executable, script],
                capture_output=True,
                text=True,
                cwd=DATA_DIR,
                encoding='utf-8',
                env=env
            )
            
            if result.returncode == 0:
                log(f"  [OK] {script}")
                success_count += 1
            else:
                log(f"  [FAIL] {script}")
                log(f"    Error: {result.stderr.strip()}")
                
        except Exception as e:
            log(f"  [FAIL] Exception running {script}: {e}")
            
    log(f"Generation complete. Success: {success_count}/{len(GENERATION_SCRIPTS)}")
    return success_count > 0

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

def connect_db():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
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
    
    for i, (_, row) in enumerate(df.iterrows()):
        if (i + 1) % 50 == 0: print(".", end="", flush=True)
        if (i + 1) % 10 == 0 or i == 0:
            progress_event("progress", "Company_Shareholder", current=i+1, total=total_rows)
        biz_no = row.get('biz_no')
        csv_name = str(row.get('shareholder_name', '')).strip()
        
        csv_stock = 0
        if 'total_shares_owned' in row:
             try: csv_stock = int(float(str(row['total_shares_owned']).replace(',', '')))
             except: csv_stock = 0
        
        if not csv_name:
            count_error += 1
            continue
            
        try:
            cursor.execute("SELECT company_shareholder_id, shareholder_name, total_shares_owned FROM Company_Shareholder WHERE biz_no = ?", (biz_no,))
            existing = cursor.fetchall()
            
            match_found = False
            target_id = None
            
            # 1. Exact Name
            for sid, sname, sstock in existing:
                if sname == csv_name:
                    match_found = True; target_id = sid; break
            
            # 2. Masked + Stock Match
            if not match_found and is_masked(csv_name):
                for sid, sname, sstock in existing:
                    db_stock = sstock if sstock else 0
                    if fuzzy_name_match(csv_name, sname) and (csv_stock == db_stock) and (csv_stock > 0):
                        match_found = True; target_id = sid
                        row['shareholder_name'] = sname
                        break
            
            cols_map = {
                'shareholder_name': row.get('shareholder_name'),
                'ownership_percent': row.get('ownership_percent', 0),
                'relationship': row.get('relationship', ''),
                'shareholder_type': row.get('shareholder_type', ''),
                'management_type': row.get('management_type', ''),
                'silent_partner_relationship': row.get('silent_partner_relationship', ''),
                'total_shares_owned': csv_stock
            }
            
            if target_id:
                set_clauses = [f"{k} = ?" for k in cols_map.keys()]
                cursor.execute(f"UPDATE Company_Shareholder SET {', '.join(set_clauses)} WHERE company_shareholder_id = ?", list(cols_map.values()) + [target_id])
                count_updated += 1
            else:
                cols_map['biz_no'] = biz_no
                cols = list(cols_map.keys())
                placeholders = ", ".join(["?" for _ in cols])
                cursor.execute(f"INSERT INTO Company_Shareholder ({', '.join(cols)}) VALUES ({placeholders})", list(cols_map.values()))
                count_inserted += 1
        except Exception as e:
            count_error += 1
            log(f"  [Error] Shareholder biz_no={biz_no}: {e}")
            
    conn.commit()
    print("")
    log(f"  Inserted: {count_inserted}, Updated: {count_updated}, Errors: {count_error}")
    json_result("Company_Shareholder_Inserted", count_inserted)
    json_result("Company_Shareholder_Updated", count_updated)
    json_result("Company_Shareholder_Error", count_error)
    progress_event("table_done", "Company_Shareholder", inserted=count_inserted, updated=count_updated, error=count_error)

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
    
    for i, (_, row) in enumerate(df.iterrows()):
        if (i + 1) % 50 == 0: print(".", end="", flush=True)
        if (i + 1) % 10 == 0 or i == 0:
            progress_event("progress", "Company_Financial", current=i+1, total=total_rows)
        
        biz_no = row.get('biz_no')
        fiscal_year = row.get('fiscal_year')
        
        if not biz_no or not fiscal_year:
            count_error += 1
            continue
            
        try:
            # Check existence by (biz_no, fiscal_year) - composite key
            cursor.execute("SELECT COUNT(*) FROM Company_Financial WHERE biz_no = ? AND fiscal_year = ?", (biz_no, fiscal_year))
            exists = cursor.fetchone()[0] > 0
            
            data_to_save = {}
            for col in db_cols:
                if col in row:
                    val = row[col]
                    # Handle NaN values
                    if pd.isna(val):
                        val = None
                    elif hasattr(val, 'item'):
                        val = val.item()  # Convert numpy types to Python types
                    data_to_save[col] = val
            
            if exists:
                # Update - exclude biz_no and fiscal_year from SET clause
                update_data = {k: v for k, v in data_to_save.items() if k not in ('biz_no', 'fiscal_year')}
                if update_data:
                    set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
                    values = list(update_data.values()) + [biz_no, fiscal_year]
                    cursor.execute(f"UPDATE Company_Financial SET {set_clause} WHERE biz_no = ? AND fiscal_year = ?", values)
                count_updated += 1
            else:
                # Insert
                cols = list(data_to_save.keys())
                placeholders = ", ".join(["?" for _ in cols])
                values = list(data_to_save.values())
                cursor.execute(f"INSERT INTO Company_Financial ({', '.join(cols)}) VALUES ({placeholders})", values)
                count_inserted += 1
                
        except Exception as e:
            count_error += 1
            log(f"  [Error] Financial {biz_no}/{fiscal_year}: {e}")
            
    conn.commit()
    print("")
    log(f"  Inserted: {count_inserted}, Updated: {count_updated}, Errors: {count_error}")
    json_result("Company_Financial_Inserted", count_inserted)
    json_result("Company_Financial_Updated", count_updated)
    json_result("Company_Financial_Error", count_error)
    progress_event("table_done", "Company_Financial", inserted=count_inserted, updated=count_updated, error=count_error)

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
