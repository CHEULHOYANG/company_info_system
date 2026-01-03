#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Clean rebuild of status selector - Step by step approach:
1. Find current radio button status selector
2. Replace with clean button-based design
3. Add all 5 status options
4. Green save button
5. Maintain all existing functionality
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Find the current "접촉 상태:" section and replace carefully
# Look for the label and radio buttons
pattern = r'(<label[^>]*>접촉 상태:</label>\s*<div[^>]*>)(.*?)(</div>\s*</div>)'

replacement = r'''\1
                        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 14px;">
                            <button type="button" class="status-btn" data-status="접촉대기" 
                                    onclick="selectStatus(this, '접촉대기')"
                                    style="padding: 10px 6px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666; white-space: nowrap;">
                                접촉대기
                            </button>
                            <button type="button" class="status-btn" data-status="접촉중"
                                    onclick="selectStatus(this, '접촉중')"
                                    style="padding: 10px 6px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666; white-space: nowrap;">
                                접촉중
                            </button>
                            <button type="button" class="status-btn" data-status="접촉해제"
                                    onclick="selectStatus(this, '접촉해제')"
                                    style="padding: 10px 6px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666; white-space: nowrap;">
                                접촉해제
                            </button>
                            <button type="button" class="status-btn" data-status="완료"
                                    onclick="selectStatus(this, '완료')"
                                    style="padding: 10px 6px; border: 2px solid #4a90e2; background: #4a90e2; color: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; white-space: nowrap;">
                                완료
                            </button>
                            <button type="button" class="status-btn" data-status="실패"
                                    onclick="selectStatus(this, '실패')"
                                    style="padding: 10px 6px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666; white-space: nowrap;">
                                실패
                            </button>
                        </div>
                        <input type="hidden" id="selected_status" value="완료">
                        <button onclick="saveMemo()" 
                                style="width: 100%; padding: 13px; background: linear-gradient(135deg, #28a745 0%, #34ce57 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; box-shadow: 0 3px 6px rgba(40,167,69,0.25); transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px;"
                                onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 5px 10px rgba(40,167,69,0.35)'"
                                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 3px 6px rgba(40,167,69,0.25)'">
                            <span style="font-size: 16px;">💾</span>
                            메모 및 상태 저장
                        </button>
                    \3'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Step 2: Add the selectStatus JavaScript function (if not exists)
if 'function selectStatus' not in content:
    select_status_function = '''
        // Status button selection
        function selectStatus(btn, status) {
            document.querySelectorAll('.status-btn').forEach(b => {
                b.style.background = 'white';
                b.style.color = '#666';
                b.style.borderColor = '#e0e0e0';
            });
            btn.style.background = '#4a90e2';
            btn.style.color = 'white';
            btn.style.borderColor = '#4a90e2';
            document.getElementById('selected_status').value = status;
        }
'''
    # Find the last </script> tag and add before it
    content = re.sub(r'(</script>\s*$)', select_status_function + r'\1', content, flags=re.MULTILINE)

# Step 3: Update saveMemo function to use hidden input
content = re.sub(
    r"const status = document\.querySelector\('input\[name=\"contact_status\"\]:checked'\)\?\.value \|\| '접촉대기';",
    "const status = document.getElementById('selected_status')?.value || '완료';",
    content
)

# Also check for other variations
content = re.sub(
    r"document\.querySelector\('input\[name=\"contact_status\"\]:checked'\)",
    "document.getElementById('selected_status')",
    content
)

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Status selector cleanly rebuilt!")
print("\nChanges:")
print("1. ✅ Replaced radio buttons with 5 equal-width button grid")
print("2. ✅ Added missing statuses: 접촉해제, 실패")
print("3. ✅ Green gradient save button with icon")
print("4. ✅ Clean JavaScript function for selection")
print("5. ✅ Updated saveMemo to use hidden input")
print("\nReady for testing!")
