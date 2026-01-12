import sqlite3
import json

def inspect_ys_tables():
    try:
        conn = sqlite3.connect('company_database.db')
        cursor = conn.cursor()
        
        # Get all tables starting with ys_
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ys_%'")
        tables = cursor.fetchall()
        
        result = {}
        
        for table_name in tables:
            name = table_name[0]
            # Get schema
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{name}'")
            schema = cursor.fetchone()[0]
            
            # Get row count
            cursor.execute(f"SELECT count(*) FROM {name}")
            count = cursor.fetchone()[0]
            
            result[name] = {
                'schema': schema,
                'count': count
            }
            
        print(json.dumps(result, indent=2))
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_ys_tables()
