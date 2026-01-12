import sqlite3

def export_ys_tables():
    db_path = 'company_database.db'
    output_file = 'ys_migration.sql'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables starting with ys_
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ys_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("BEGIN TRANSACTION;\n\n")
        
        for table in tables:
            print(f"Exporting {table}...")
            
            # 1. Get Schema
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
            create_statement = cursor.fetchone()[0]
            # Ensure IF NOT EXISTS is used to avoid errors if table exists
            if "CREATE TABLE" in create_statement and "IF NOT EXISTS" not in create_statement:
                create_statement = create_statement.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
            
            f.write(f"-- Schema for {table}\n")
            f.write(f"{create_statement};\n\n")
            
            # 2. Get Data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if rows:
                f.write(f"-- Data for {table}\n")
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                col_names = ", ".join(columns)
                
                for row in rows:
                    # Format values for SQL
                    values = []
                    for val in row:
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, (int, float)):
                            values.append(str(val))
                        else:
                            # Escape single quotes
                            safe_val = str(val).replace("'", "''")
                            values.append(f"'{safe_val}'")
                    
                    val_str = ", ".join(values)
                    # Use INSERT OR REPLACE to update existing records or insert new ones
                    f.write(f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({val_str});\n")
                f.write("\n")
        
        f.write("COMMIT;\n")
    
    conn.close()
    print(f"Migration SQL written to {output_file}")

if __name__ == "__main__":
    export_ys_tables()
