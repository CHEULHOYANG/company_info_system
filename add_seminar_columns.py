import sqlite3

def add_columns():
    conn = sqlite3.connect('company_database.db')
    cursor = conn.cursor()
    
    try:
        # Check if instructor column exists
        cursor.execute("PRAGMA table_info(Seminars)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'instructor' not in columns:
            print("Adding 'instructor' column to Seminars table...")
            cursor.execute("ALTER TABLE Seminars ADD COLUMN instructor TEXT")
            print("Column added.")
        else:
            print("'instructor' column already exists.")
            
    except Exception as e:
        print(f"Error adding columns: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns()
