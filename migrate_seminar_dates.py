import sqlite3
import re
from datetime import datetime

DATABASE = 'company_database.db'

def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return None

def parse_korean_date_string(date_str):
    if not date_str:
        return None
    date_str = date_str.strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    try:
        # Regex to match "M월 D일" with optional spaces
        match = re.search(r'(\d+)\s*월\s*(\d+)\s*일', date_str)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            year = 2026 
            return f"{year}-{month:02d}-{day:02d}"
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
    return None

def normalize_time_string(time_str):
    if not time_str:
        return None
    # Replace "-" with "~" and fix spaces
    # Example: "10:00 - 11:50" -> "10:00 ~ 11:50"
    # Example: "10:30 ~ 12: 30" -> "10:30 ~ 12:30"
    temp = time_str.replace('-', '~').replace('  ', ' ')
    parts = temp.split('~')
    if len(parts) == 2:
        start = parts[0].strip()
        end = parts[1].strip()
        # Fix "12: 30" -> "12:30"
        start = start.replace(': ', ':').replace(' :', ':')
        end = end.replace(': ', ':').replace(' :', ':')
        return f"{start} ~ {end}"
    return time_str

def migrate():
    conn = get_db_connection()
    if not conn:
        return

    try:
        print("Starting migration...")
        rows = conn.execute('SELECT id, date, time FROM ys_seminars').fetchall()
        print(f"Found {len(rows)} seminars.")
        
        updated_count = 0
        for row in rows:
            seminar_id = row['id']
            original_date = row['date']
            original_time = row['time']
            
            new_date = parse_korean_date_string(original_date)
            new_time = normalize_time_string(original_time)
            
            updates = []
            params = []
            
            if new_date and new_date != original_date:
                updates.append("date = ?")
                params.append(new_date)
                print(f"[ID {seminar_id}] Date: '{original_date}' -> '{new_date}'")
            
            if new_time and new_time != original_time:
                updates.append("time = ?")
                params.append(new_time)
                print(f"[ID {seminar_id}] Time: '{original_time}' -> '{new_time}'")
                
            if updates:
                params.append(seminar_id)
                sql = f"UPDATE ys_seminars SET {', '.join(updates)} WHERE id = ?"
                conn.execute(sql, tuple(params))
                updated_count += 1
        
        conn.commit()
        print(f"Migration complete. Updated {updated_count} rows.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
