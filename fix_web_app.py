import os

file_path = 'f:/company_project_system/web_app.py'
new_content_path = 'f:/company_project_system/new_content.txt'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep lines up to 7235 (index 7235)
kept_lines = lines[:7235]

with open(new_content_path, 'r', encoding='utf-8') as f:
    new_content = f.read()

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(kept_lines)
    f.write(new_content)
