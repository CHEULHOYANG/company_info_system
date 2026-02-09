
import os

file_path = r'g:\company_project_system\templates\user_management.html'

try:
    with open(file_path, 'r', encoding='cp949') as f:
        lines = f.readlines()
except UnicodeDecodeError:
    # Fallback to euc-kr or latin-1 if cp949 fails
    try:
        with open(file_path, 'r', encoding='euc-kr') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            lines = f.readlines()

for i, line in enumerate(lines):
    if 'deleteSignupRequest' in line or ('fetch' in line and 'signup-requests' in line):
        print(f"{i+1}: {line.strip()}")
