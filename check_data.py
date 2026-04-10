import sqlite3

def check_records():
    conn = sqlite3.connect('company_database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    bzs = ['1372158570', '4661700872', '2340102966', '1074368934', '1220641318']
    
    for bz in bzs:
        # Search for the record by normalizing the stored business_number
        cursor.execute("SELECT * FROM individual_business_owners WHERE REPLACE(REPLACE(business_number, '-', ''), ' ', '') = ?", (bz,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            # Print only relevant fields to avoid overwhelming output
            relevant = {k: d[k] for k in ['company_name', 'revenue', 'net_income', 'employee_count', 'financial_year', 'business_number'] if k in d}
            print(f"{bz}: {relevant}")
        else:
            print(f"{bz}: Not Found")
    
    conn.close()

if __name__ == "__main__":
    check_records()
