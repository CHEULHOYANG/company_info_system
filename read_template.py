
import os

file_path = r"g:\company_project_system\templates\detail.html"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except UnicodeDecodeError:
    with open(file_path, 'r', encoding='cp949') as f:
        lines = f.readlines()

for i, line in enumerate(lines):
    if "<th>생년월일</th>" in line:
        print(f"Match at {i+1}")
        for j in range(max(0, i-5), min(len(lines), i+20)):
             print(f"{j+1}: {lines[j].rstrip()}")
