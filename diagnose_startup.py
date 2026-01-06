
try:
    print("Importing web_app...")
    import web_app
    print("Import successful.")

    print("Checking specific functions...")
    from web_app import get_db_connection
    conn = get_db_connection()
    print("DB Connection successful.")
    
    print("Checking Seminars table...")
    try:
        conn.execute("SELECT * FROM Seminars LIMIT 1")
        print("Seminars table exists.")
    except Exception as e:
        print(f"Seminars table error: {e}")

    print("Checking SeminarRegistrations table...")
    try:
        conn.execute("SELECT * FROM SeminarRegistrations LIMIT 1")
        print("SeminarRegistrations table exists.")
    except Exception as e:
        print(f"SeminarRegistrations table error: {e}")

    print("Checking ys_inquiries table...")
    try:
        conn.execute("SELECT * FROM ys_inquiries LIMIT 1")
        print("ys_inquiries table exists.")
    except Exception as e:
        print(f"ys_inquiries table error: {e}")
        
    conn.close()
    print("Diagnosis complete.")

except Exception as e:
    print(f"CRITICAL FAILURE: {e}")
    import traceback
    traceback.print_exc()
