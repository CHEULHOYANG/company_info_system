#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add save button back to popup
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the memo status group and add save button after it
# Look for the hidden input line we added
save_button_html = '''                        <button onclick="saveMemo()" style="margin-top: 12px; padding: 8px 20px; background: #4a90e2; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 500;">메모 및 상태 저장</button>'''

# Add button after the hidden input
content = re.sub(
    r'(<input type="hidden" id="selected_status" value="완료">)',
    r'\1\n' + save_button_html,
    content
)

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Save button added back!")
