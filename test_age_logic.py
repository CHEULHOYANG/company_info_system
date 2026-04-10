
from datetime import date, datetime

def calculate_age(birth_date_str):
    if not birth_date_str:
        return None
        
    s = str(birth_date_str).strip()
    
    # Check for masking
    if '*' in s:
        return None
        
    # Try parsing
    dt = None
    formats = ['%Y%m%d', '%Y-%m-%d', '%y%m%d']
    
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt).date()
            break
        except ValueError:
            continue
            
    if not dt:
        return None
        
    today = date.today()
    
    # Adjust for 2-digit year logic if needed?
    # e.g. 951005 -> 1995? 2095?
    # Python's %y pivots at 69 (00-68 -> 2000s, 69-99 -> 1900s).
    # Given the company context (established 1995), a rep birthdate like '95...' is ambiguous. 
    # But usually full YYYYMMDD is preferred. If 6 digits, we might need logic.
    # Assuming mostly YYYYMMDD or masked.
    
    # If year < 100, assume 1900s or 2000s based on pivot?
    # Let's rely on standard strptime for now, or ensure 4 digit year is prioritized.
    
    # Calculate international age
    age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
    return age

# Test cases
test_cases = [
    ("19800101", 46), # Assuming 2026
    ("1990-05-05", 35), # Assuming 2026-02
    ("6*******", None),
    ("198001**", None),
    ("invalid", None),
    (None, None)
]

print(f"Today: {date.today()}")

for date_str, expected in test_cases:
    result = calculate_age(date_str)
    print(f"Input: {date_str}, Output: {result}, Excepted: {expected}")
    
