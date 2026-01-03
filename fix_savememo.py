#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix saveMemo function to use selected_status
"""

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace old radio button code with new hidden input code
old_code = 'const status = document.querySelector(\'input[name="memo_status"]:checked\')?.value || \'완료\';'
new_code = 'const status = document.getElementById(\'selected_status\')?.value || \'완료\';'

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Found and replaced old code!")
else:
    # Try variations
    variations = [
        'const status = document.querySelector(\'input[name=\\"memo_status\\"]:checked\')?.value || \'완료\';',
        'const status = document.querySelector("input[name=\\"memo_status\\"]:checked")?.value || "완료";',
        'const status = document.querySelector("input[name=\'memo_status\']:checked")?.value || \'완료\';'
    ]
    
    found = False
    for var in variations:
        if var in content:
            content = content.replace(var, new_code)
            print(f"✅ Found variation and replaced: {var[:50]}...")
            found = True
            break
    
    if not found:
        print("❌ Could not find target code to replace")
        print("Searching for any line containing 'memo_status'...")
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'memo_status' in line and 'saveMemo' not in line:
                print(f"Line {i}: {line.strip()}")
        exit(1)

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ File updated successfully!")
print(f"Changed: {old_code}")
print(f"To:     {new_code}")
