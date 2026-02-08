import sqlite3
import os

DB_PATH = r"g:\company_project_system\company_database.db"

def add_column_if_not_exists(cursor, table, column, col_type):
    try:
        cursor.execute(f"SELECT {column} FROM {table} LIMIT 1")
    except sqlite3.OperationalError:
        print(f"Adding column {column} to {table}")
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            print(f"  Success")
        except Exception as e:
            print(f"  Failed: {e}")
    except Exception as e:
        print(f"Error checking {column} in {table}: {e}")

def update_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Company_Basic
    add_column_if_not_exists(cursor, "Company_Basic", "employee_count", "INTEGER")

    # Company_Additional
    add_column_if_not_exists(cursor, "Company_Additional", "group_agreement_yn", "CHAR(1)")
    add_column_if_not_exists(cursor, "Company_Additional", "gfc_yn", "CHAR(1)")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_schema()
