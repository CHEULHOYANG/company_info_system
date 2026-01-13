
import sqlite3
import os

# Connect to the database
# Based on web_app.py logic, it tries to use a persistent disk path first if on Render, 
# but locally it uses 'company_database.db' in the app directory.
DB_PATH = os.path.join(os.getcwd(), 'company_database.db')

def fix_profile():
    print(f"Connecting to database at: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Error: Database file not found!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check all team members for Samsung SDS
        cursor.execute("SELECT id, name, bio FROM ys_team_members WHERE bio LIKE '%삼성SDS%'")
        rows = cursor.fetchall()
        
        if not rows:
            print("No team members found with 'Samsung SDS' in bio.")
        
        for row in rows:
            member_id, name, bio = row
            print(f"Found 'Samsung SDS' in profile of: {name}")
            print(f"Current Bio: {bio}")
            
            # Remove Samsung SDS
            # Patterns: "삼성SDS, ", "삼성SDS,", "삼성SDS "
            new_bio = bio.replace("삼성SDS, ", "").replace("삼성SDS,", "").replace("삼성SDS", "").strip()
            
            # Clean up leading/trailing punctuation/spaces
            new_bio = new_bio.strip(', ')
            
            print(f"New Bio: {new_bio}")
            
            cursor.execute("UPDATE ys_team_members SET bio = ? WHERE id = ?", (new_bio, member_id))
            print(f"Updated bio for {name}")
            
        conn.commit()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_profile()
