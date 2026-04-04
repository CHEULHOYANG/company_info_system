import sqlite3
import re
import sys

def validate_email(email):
    """Simple regex based email validation"""
    if not email:
        return False
    # Basic email regex
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, str(email).strip()))

def run_batch():
    try:
        conn = sqlite3.connect('g:/company_project_system/company_database.db')
        cursor = conn.cursor()
        
        # Get all companies with email
        cursor.execute("SELECT biz_no, email FROM Company_Basic WHERE email IS NOT NULL AND email != ''")
        rows = cursor.fetchall()
        
        valid_count = 0
        invalid_count = 0
        
        for biz_no, email in rows:
            is_valid = validate_email(email)
            status = 'Y' if is_valid else 'N'
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                
            cursor.execute("UPDATE Company_Basic SET email_usable = ? WHERE biz_no = ?", (status, biz_no))
            
        # Update companies with no email to 'N'
        cursor.execute("UPDATE Company_Basic SET email_usable = 'N' WHERE email IS NULL OR email = ''")
        
        conn.commit()
        conn.close()
        
        print(f"Batch completed. Valid emails: {valid_count}, Invalid emails: {invalid_count}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    run_batch()
