with open('web_app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'def lys_admin_seminars' in line:
            print(f"{i+1}: {line.strip()}")
