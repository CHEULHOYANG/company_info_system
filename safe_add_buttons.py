#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Safely add edit buttons to detail.html by using line-based replacement
"""
import os
import shutil
from datetime import datetime

# Backup first
backup_file = r'g:\company_project_system\templates\detail.html.backup_' + datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(r'g:\company_project_system\templates\detail.html', backup_file)
print(f"✓ Backup created: {backup_file}")

# Read with binary mode to preserve encoding
with open(r'g:\company_project_system\templates\detail.html', 'rb') as f:
    content_bytes = f.read()

# Try to decode
try:
    content = content_bytes.decode('utf-8')
    encoding = 'utf-8'
except:
    content = content_bytes.decode('cp949')
    encoding = 'cp949'

print(f"✓ File encoding detected: {encoding}")

# Split into lines
lines = content.split('\n')

# Find and modify lines
modified_count = 0

for i, line in enumerate(lines):
    # Replace rep.name
    if '{{ rep.name }}' in line and '<td>' in line and '</td>' in line:
        # Simple replacement - just add ID to the td for now
        new_line = line.replace(
            '{{ rep.name }}',
            '<span id="rep-name-{{ loop.index }}">{{ rep.name }}</span>{% if rep.name and "*" in rep.name %}<button onclick="editRep({{ loop.index }})" style="margin-left:8px;padding:4px 8px;background:#007bff;color:white;border:none;border-radius:4px;cursor:pointer;font-size:11px;">수정</button>{% endif %}'
        )
        lines[i] = new_line
        modified_count += 1
        print(f"✓ Modified line {i+1} (rep.name)")
    
    # Replace holder.shareholder_name
    if '{{ holder.shareholder_name }}' in line and '<td>' in line and '</td>' in line:
        new_line = line.replace(
            '{{ holder.shareholder_name }}',
            '<span id="share-name-{{ loop.index }}">{{ holder.shareholder_name }}</span>{% if holder.shareholder_name and "*" in holder.shareholder_name %}<button onclick="editShare({{ loop.index }})" style="margin-left:8px;padding:4px 8px;background:#007bff;color:white;border:none;border-radius:4px;cursor:pointer;font-size:11px;">수정</button>{% endif %}'
        )
        lines[i] = new_line
        modified_count += 1
        print(f"✓ Modified line {i+1} (holder.shareholder_name)")

# Rejoin
new_content = '\n'.join(lines)

# Write back with same encoding
with open(r'g:\company_project_system\templates\detail.html', 'wb') as f:
    f.write(new_content.encode(encoding))

print(f"\n✓ Successfully modified {modified_count} lines")
print(f"✓ File saved with {encoding} encoding")
print(f"\n⚠ If something goes wrong, restore from: {backup_file}")
