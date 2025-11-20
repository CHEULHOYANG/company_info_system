
import os

file_path = 'templates/company_detail.html'
output_path = 'js_section.txt'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except UnicodeDecodeError:
    try:
        with open(file_path, 'r', encoding='cp949') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        lines = []

with open(output_path, 'w', encoding='utf-8') as out:
    # JS section likely starts after HTML
    start = 1600
    for i in range(start, len(lines)):
        out.write(f"{i+1}: {lines[i]}")
