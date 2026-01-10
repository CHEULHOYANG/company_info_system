
import os

file_path = 'web_app.py'

with open(file_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("BOM removed.")
