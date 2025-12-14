#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Read file
with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='cp949', errors='ignore') as f:
    lines = f.readlines()

# Show line 263 (rep.name)
print("=== LINE 263 (rep.name) ===")
for i in range(260, 270):
    if i < len(lines):
        print(f"{i+1}: {lines[i].rstrip()}")

print("\n\n=== LINE 318 (holder.shareholder_name) ===")
for i in range(315, 325):
    if i < len(lines):
        print(f"{i+1}: {lines[i].rstrip()}")
