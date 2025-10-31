# Company Information Management System - AI Agent Instructions

## System Overview
Flask-based Korean company information management system with multi-tier user authentication, financial data analysis, and tax calculation tools. **Main file: `web_app.py` (4700+ lines)**. Database: SQLite with Korean (CP949) encoding support and robust deployment handling.

## Architecture & Data Flow

### Core Components
- **`web_app.py`**: Monolithic Flask application with all routes, business logic, and database operations
- **Database**: SQLite with advanced path handling - Company_Basic, Company_Financial, Contact_History, Users, User_Subscriptions, Pioneering_Targets, Sales_Expenses
- **File Upload System**: `uploads/` folder for receipts and documents via `UPLOAD_FOLDER` config
- **Authentication**: 4-tier user system (V=메인관리자, S=서브관리자, M=매니저, N=일반담당자)
- **Templates**: Korean-language Jinja2 templates with CP949 encoding support via custom loader

### Key Data Models
```python
# Users table with hierarchical permissions
user_levels = {'V': 4, 'S': 3, 'M': 2, 'N': 1}  # Higher = more permissions

# Company data split across:
# - Company_Basic: core company info  
# - Company_Financial: financial statements (3-year history)
# - Contact_History: user interaction tracking
# - Pioneering_Targets: sales visit planning with completion tracking
# - Sales_Expenses: expense management with receipt storage
```

### Permission System & Data Access
- **V (메인관리자)**: Full system access, user management, all data visibility
- **S (서브관리자)**: User management, all contact history, all expenses
- **M (매니저)**: Own + team data access, limited management functions  
- **N (일반담당자)**: Own data only (contact history, expenses, pioneering targets)

## Development Patterns

### Database Operations
```python
# Always use connection pattern:
conn = get_db_connection()
try:
    # DB operations
    conn.commit()
except Exception as e:
    conn.rollback()
    raise e
finally:
    conn.close()
```

### Korean Time Handling
```python
# All timestamps use Korean timezone (KST)
KST = pytz.timezone('Asia/Seoul')
formatted_datetime = format_kst_datetime()  # Use this for DB timestamps
```

### Template Encoding
- Custom `CP949FileSystemLoader` handles mixed encoding (CP949/UTF-8)
- Templates fallback from CP949 to UTF-8 encoding
- All user-facing text in Korean

### API Response Pattern
```python
# Standard JSON response format:
return jsonify({"success": True/False, "message": "Korean message", "data": optional})
```

## Critical Workflows

### User Authentication Flow
1. Login via `/login` → session-based auth
2. Permission checks use `check_permission(user_level, required_level)`  
3. User data stored in session: user_id, user_name, user_level, branch_code

### Company Data Management
- Search/filter via `query_companies_data()` with complex joins
- Financial calculations in `calculate_unlisted_stock_value()`
- Export to Excel limited to 500 records (performance constraint)

### Sales Management System (NEW)
- **Pioneering Targets**: `/sales_management` - visit planning with date tracking
- **Expense Management**: Receipt upload to `uploads/` folder with multi-file support
- **CSV Operations**: Bulk import/export for pioneering targets and expenses via `/api/*_csv` endpoints
- **Permission-based data access**: Users see only own data, managers see team data

### Contact History Tracking  
- Permissions filter data visibility (`registered_by` field)
- Future date validation with 1-minute tolerance
- CSV import/export via `/api/contact_history_csv`

## Environment-Specific Behavior

### Database Path Logic & Recovery
```python
# Advanced render.com detection with fallback:
if os.environ.get('RENDER'):
    # Production: preserve existing DB or create in /data folder
    # Fallback to emergency DB if main DB fails
else:
    # Local: use company_database.db in project root
```

### Database Management Utilities (RENDER-SPECIFIC)
- `/check_tables` - Verify table existence and row counts
- `/fix_db` - Create missing tables on Render deployment
- `/upload_database` & `/download_database` - Database backup/restore
- `init_emergency_database()` - In-memory fallback with basic admin user

### Initialization Order  
1. `get_db_connection()` with error recovery logic
2. `init_user_tables()` - User management tables
3. `init_business_tables()` - Company data + Sales_Expenses + Pioneering_Targets tables
4. All preserve existing data, only create missing tables

## UI/UX Conventions
- Korean language throughout (forms, errors, navigation)
- Gradient backgrounds with glass-morphism effects
- Subscription status display with days remaining calculation
- Role-based menu visibility (user management for S+ levels only)

## Tax Calculator Modules
Separate routes for Korean tax calculations:
- `/gift_tax` - 증여세
- `/transfer_tax` - 양도소득세  
- `/income_tax` - 종합소득세
- `/social_ins_tax` - 4대보험료
- `/acquisition_tax` - 취득세
- `/retirement_pay` - 퇴직금

## File Management & Uploads
- **Receipt Storage**: `uploads/` folder with `UPLOAD_FOLDER` config
- **Multi-file Support**: Comma-separated filenames in database
- **File Security**: `secure_filename()` for safe uploads
- **Viewing Routes**: `/view_receipt/<id>` and `/download_receipt/<id>`

## New API Endpoints (Sales Management)
```python
# Pioneering targets management
/api/pioneering_targets (GET, POST)
/api/pioneering_targets/<id> (DELETE, PUT)
/api/pioneering_targets_csv (GET: export, POST: import)

# Sales expenses management  
/api/sales_expenses (GET, POST)
/api/sales_expenses/<id> (PUT, DELETE)
/api/sales_expenses_csv (GET: export, POST: import)
```

## Security & Validation
- Password rules: 8-20 chars, upper/lower/digit/special chars required
- Password change API: `/api/change-password` with complexity validation
- Session-based authentication with logout route
- SQL injection protection via parameterized queries
- File upload validation and secure storage

## Performance Considerations
- Excel export capped at 500 records
- Pagination: 20 items per page (index), 50 items (API)
- Large file reading with limit/offset parameters
- Background processes supported via `isBackground` flag

## File Structure Notes
- `create_user_table.sql`: User schema with sample data
- `table.py`: Database maintenance utility (Korean comments) for Contact_History cleanup
- `uploads/`: File storage for receipts and documents (auto-created)
- `templates/sales_management.html`: Tabbed interface for pioneering/expenses/contact management
- Templates use mixed encoding (CP949/UTF-8 fallback)

## Development Tips
- Always test database connections with error recovery logic
- Use `check_permission()` for role-based access control
- Render deployment requires special DB path handling
- CSV import supports Korean headers with encoding detection (UTF-8-sig, CP949)
- File uploads require `multipart/form-data` and `secure_filename()`
- Korean timezone (KST) must be used for all date operations

When working with this codebase, always consider Korean timezone, preserve existing data, respect the hierarchical permission system, and handle file uploads securely.