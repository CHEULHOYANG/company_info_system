#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to fix individual_list.html popup:
1. Replace memo_status dropdown with radio buttons
2. Remove history_status dropdown to eliminate confusion
3. Make layout more compact
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace memo_status dropdown with radio buttons
old_memo_status = r'''<select id="memo_status"
                        style="padding: 8px; border: 1px solid var\(--border-color\); border-radius: 4px;">
                        <option value="접촉대기">접촉대기</option>
                        <option value="접촉중">접촉중</option>
                        <option value="접촉해제">접촉해제</option>
                        <option value="완료">완료</option>
                        <option value="실패">실패</option>
                    </select>'''

new_memo_status = '''<div id="memo_status_group" style="display: flex; gap: 10px; align-items: center;">
                        <label style="font-size: 0.9rem; font-weight: 500; margin: 0;">접촉 상태:</label>
                        <label style="display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: 0.9rem;">
                            <input type="radio" name="memo_status" value="접촉대기" style="cursor: pointer;">
                            <span>접촉대기</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: 0.9rem;">
                            <input type="radio" name="memo_status" value="접촉중" style="cursor: pointer;">
                            <span>접촉중</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: 0.9rem;">
                            <input type="radio" name="memo_status" value="완료" checked style="cursor: pointer;">
                            <span>완료</span>
                        </label>
                    </div>'''

content = re.sub(
    r'<select id="memo_status"\s+style="[^"]+">.*?</select>',
    new_memo_status,
    content,
    flags=re.DOTALL
)

# 2. Remove history_status dropdown completely
content = re.sub(
    r'<select id="history_status"[^>]*>.*?</select>\s*',
    '',
    content,
    flags=re.DOTALL
)

# 3. Update JavaScript to read radio button value instead of select
# Find saveMemo function and update it
content = re.sub(
    r"const status = document\.getElementById\('memo_status'\)\.value;",
    "const status = document.querySelector('input[name=\"memo_status\"]:checked')?.value || '완료';",
    content
)

# 4. Update loadMemoAndHistory to set radio button instead of select
content = re.sub(
    r"document\.getElementById\('memo_status'\)\.value = status;",
    "const radioBtn = document.querySelector(`input[name=\"memo_status\"][value=\"${status}\"]`); if (radioBtn) radioBtn.checked = true;",
    content
)

# 5. Remove history_status from addHistory function
# The function should no longer try to read history_status
content = re.sub(
    r"const historyStatus = document\.getElementById\('history_status'\)\.value;[^\n]*\n",
    "",
    content
)

# Also remove any status-related code in addHistory
content = re.sub(
    r"if \(historyStatus\) \{[^}]+\}[^\n]*\n",
    "",
    content
)

# Write back
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ individual_list.html modified successfully!")
print("\nChanges made:")
print("1. Replaced memo_status dropdown with radio buttons (접촉대기, 접촉중, 완료)")
print("2. Removed history_status dropdown to eliminate confusion")
print("3. Updated JavaScript to handle radio button values")
print("4. Contact history now only uses history_type (전화, 방문, etc.)")
