
file_path = r"g:\company_project_system\templates\detail.html"
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except:
    with open(file_path, 'r', encoding='cp949') as f:
        lines = f.readlines()

for i, line in enumerate(lines):
    if "gender" in line:
        print(f"{i+1}: {line.strip()}")
