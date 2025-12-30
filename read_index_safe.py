import os

file_path = 'templates/index.html'

def read_file():
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='cp949') as f:
                lines = f.readlines()
                return lines
        except Exception as e:
            print(f"Error reading file: {e}")
            return []

lines = read_file()
for i in range(350, 370):
    if i < len(lines):
        print(f"{i+1}: {lines[i].rstrip()}")
