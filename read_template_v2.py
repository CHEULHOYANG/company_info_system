
file_path = r"g:\company_project_system\templates\detail.html"
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except:
    with open(file_path, 'r', encoding='cp949') as f:
        lines = f.readlines()

for i in range(260, 300):
    if i < len(lines):
        print(f"{i+1}: {lines[i].rstrip()}")
