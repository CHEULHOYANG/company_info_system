#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to unify contact status fields in individual_list.html
and convert to radio buttons
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the section with contact history tabs
# Look for the area around line 560-580 where "접촉 히스토리" is mentioned

# Print the relevant section for debugging
start_idx = content.find('접촉 히스토리')
if start_idx != -1:
    print("Found '접촉 히스토리' at index:", start_idx)
    print("\nContext (500 chars before and after):")
    print(content[max(0, start_idx-500):start_idx+500])
    print("\n" + "="*80 + "\n")

# Find the history section with tabs
# Pattern: look for the select dropdown with "전화" and "상태변경" options
pattern = r'(<div[^>]*>\s*<select[^>]*name=["\']?history_type["\']?[^>]*>.*?</select>\s*</div>)'
matches = list(re.finditer(pattern, content, re.DOTALL))

print(f"Found {len(matches)} history_type select elements")
for i, match in enumerate(matches):
    print(f"\nMatch {i+1}:")
    print(match.group()[:300])

# Save for manual review
with open('g:/company_project_system/individual_list_section.txt', 'w', encoding='utf-8') as f:
    section_start = max(0, start_idx - 1000)
    section_end = min(len(content), start_idx + 1500)
    f.write(content[section_start:section_end])
    print("\nSaved relevant section to individual_list_section.txt for review")

print("\nSearching for status-related fields...")
# Find all select elements
selects = re.findall(r'<select[^>]*>(.*?)</select>', content, re.DOTALL)
for i, select in enumerate(selects):
    if '전화' in select or '상태변경' in select or '접촉' in select:
        print(f"\nSelect #{i+1} (relevant):")
        print(select[:200])
