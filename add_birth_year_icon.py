#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add calendar icon and age to birth year display
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the HTML to show icon in the label
content = re.sub(
    r'(<div><strong>생년</strong>)',
    r'<div><strong>📅 생년</strong>',
    content
)

# 2. Update JavaScript to calculate and display age
# Find the line that sets detail_birth_year and update it to include age calculation
old_js = r"document\.getElementById\('detail_birth_year'\)\.textContent = row\.dataset\.birthYear \|\| '-';"

new_js = '''const birthYear = row.dataset.birthYear || '-';
            const birthYearSpan = document.getElementById('detail_birth_year');
            if (birthYear !== '-') {
                const currentYear = new Date().getFullYear();
                const age = currentYear - parseInt(birthYear);
                birthYearSpan.textContent = `${birthYear} (${age}세)`;
            } else {
                birthYearSpan.textContent = '-';
            }'''

content = re.sub(old_js, new_js, content)

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Added calendar icon and age calculation!")
print("\nChanges:")
print("1. Added 📅 icon to birth year label")
print("2. Display format: YYYY (XX세)")
print("3. Age is automatically calculated from birth year")
