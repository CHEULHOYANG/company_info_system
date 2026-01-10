
with open('f:/company_project_system/web_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if '/lys' in line or 'lys_main.html' in line:
            print(f"{i+1}: {line.strip()}")
