# Company Information Management System - AI Agent Instructions

## System Overview
Flask-based Korean company information management system with multi-tier user authentication, financial data analysis, and tax calculation tools. Primary database: SQLite with Korean (CP949) encoding support.

## Architecture & Data Flow

### Core Components
- **`web_app.py`**: Main Flask application (2000+ lines) - all routes, business logic, and database operations
- **Database**: SQLite with Company_Basic, Company_Financial, Contact_History, Users, User_Subscriptions tables
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
```

### Permission System
- **V (메인관리자)**: Full system access, user management
- **S (서브관리자)**: User management, all contact history
- **M (매니저)**: Own contact history + team data
- **N (일반담당자)**: Own contact history only

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

### Contact History Tracking
- Permissions filter data visibility (`registered_by` field)
- Future date validation with 1-minute tolerance
- CSV import/export via `/api/contact_history_csv`

## Environment-Specific Behavior

### Database Path Logic
```python
# render.com detection:
if os.environ.get('RENDER'):
    # Production: preserve existing DB or create in /data folder
else:
    # Local: use company_database.db in project root
```

### Initialization Order
1. `init_user_tables()` - User management tables
2. `init_business_tables()` - Company data tables
3. Both preserve existing data, only create missing tables

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

## Security & Validation
- Password rules: 8-20 chars, upper/lower/digit/special chars required
- Password history tracking (prevents reuse of last 5 passwords)
- Session-based authentication with logout route
- SQL injection protection via parameterized queries

## Performance Considerations
- Excel export capped at 500 records
- Pagination: 20 items per page (index), 50 items (API)
- Large file reading with limit/offset parameters
- Background processes supported via `isBackground` flag

## File Structure Notes
- `create_user_table.sql`: User schema with sample data
- `table.py`: Database maintenance utility (Korean comments)
- `static/contact_history_csv.csv`: Contact history template
- Templates use mixed encoding (CP949/UTF-8 fallback)

When working with this codebase, always consider Korean timezone, preserve existing data, and respect the hierarchical permission system.