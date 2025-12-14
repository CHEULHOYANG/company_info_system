#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# Read file
with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='cp949', errors='ignore') as f:
    content = f.read()

# Find all patterns with rep
rep_patterns = re.findall(r'<td[^>]*>.*?rep\.[a-z_]+.*?</td>', content, re.DOTALL | re.IGNORECASE)
print("=== REP PATTERNS ===")
for i, pattern in enumerate(rep_patterns[:5]):  # Show first 5
    print(f"\n{i+1}. {pattern[:200]}")

# Find all patterns with holder  
holder_patterns = re.findall(r'<td[^>]*>.*?holder\.[a-z_]+.*?</td>', content, re.DOTALL | re.IGNORECASE)
print("\n\n=== HOLDER PATTERNS ===")
for i, pattern in enumerate(holder_patterns[:5]):  # Show first 5
    print(f"\n{i+1}. {pattern[:200]}")
