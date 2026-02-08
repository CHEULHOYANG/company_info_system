import sqlite3
import os

DB_PATH = r"G:\company_project_system\company_database.db"

def update_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop existing table
    print("Dropping existing Company_Financial table...")
    cursor.execute("DROP TABLE IF EXISTS Company_Financial")

    # Create new table
    print("Creating new Company_Financial table...")
    # SQL based on user request:
    # biz_no varchar 12 PK (FK to Company_Basic)
    # fiscal_year INT FK
    # ...
    # Note: SQLite doesn't strictly enforce lengths, but we use them for clarity.
    # User said PK is biz_no, but fiscal_year is also FK (part of PK?).
    # A financial record is unique by (biz_no, fiscal_year).
    
    create_sql = """
    CREATE TABLE Company_Financial (
        company_financial_id INTEGER PRIMARY KEY AUTOINCREMENT,
        biz_no VARCHAR(12) NOT NULL,
        fiscal_year INTEGER NOT NULL,
        rating1 VARCHAR(20),
        rating2 VARCHAR(20),
        rating3 VARCHAR(20),
        sales_revenue DECIMAL(18,2),
        operating_income DECIMAL(18,2),
        net_income DECIMAL(18,2),
        total_assets DECIMAL(18,2),
        total_liabilities DECIMAL(18,2),
        total_equity DECIMAL(18,2),
        retained_earnings DECIMAL(18,2),
        capital_surplus DECIMAL(18,2),
        earned_reserve DECIMAL(18,2),
        additional_paid_in_capital DECIMAL(18,2),
        corporate_tax DECIMAL(18,2),
        land_asset DECIMAL(18,2),
        building_asset DECIMAL(18,2),
        investment_real_ground DECIMAL(18,2),
        investment_real_building DECIMAL(18,2),
        rental_income DECIMAL(18,2),
        rent_amt DECIMAL(18,2),
        advances_paid DECIMAL(18,2),
        advances_received DECIMAL(18,2),
        capital_stock_value DECIMAL(18,2),
        undistributed_retained_earnings DECIMAL(18,2),
        current_assets DECIMAL(18,2),
        cash_equivalents DECIMAL(18,2),
        short_term_loan DECIMAL(18,2),
        short_term_deposit DECIMAL(18,2),
        principal_short_long_term_bonds DECIMAL(18,2),
        interest_income DECIMAL(18,2),
        capital_reserve DECIMAL(18,2),
        shares_issued_count INTEGER,
        
        FOREIGN KEY (biz_no) REFERENCES Company_Basic(biz_no),
        UNIQUE(biz_no, fiscal_year)
    )
    """
    
    try:
        cursor.execute(create_sql)
        print("Table created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_schema()
