import sqlite3
import os

DB_PATH = 'company_database.db'

def migrate_db():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Modify Seminars Table
    print("Checking Seminars table for max_attendees...")
    cursor.execute("PRAGMA table_info(Seminars)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'max_attendees' not in columns:
        print("Adding max_attendees column to Seminars...")
        try:
            cursor.execute("ALTER TABLE Seminars ADD COLUMN max_attendees TEXT")
            print("max_attendees added.")
        except Exception as e:
            print(f"Error adding max_attendees: {e}")
    else:
        print("max_attendees column already exists.")

    # 2. Create SeminarSessions Table
    print("Creating SeminarSessions table...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SeminarSessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seminar_id INTEGER,
                session_time TEXT,
                title TEXT,
                instructor TEXT,
                location TEXT,
                description TEXT,
                FOREIGN KEY (seminar_id) REFERENCES Seminars (id) ON DELETE CASCADE
            )
        ''')
        print("SeminarSessions table checked/created.")
    except Exception as e:
        print(f"Error creating SeminarSessions table: {e}")

    # 3. Verify ys_questions Table
    print("Checking ys_questions table for display_order...")
    cursor.execute("PRAGMA table_info(ys_questions)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'display_order' not in columns:
        print("Adding display_order column to ys_questions...")
        try:
            cursor.execute("ALTER TABLE ys_questions ADD COLUMN display_order INTEGER DEFAULT 0")
            print("display_order added.")
        except Exception as e:
            print(f"Error adding display_order: {e}")
    else:
        print("display_order column already exists.")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_db()
