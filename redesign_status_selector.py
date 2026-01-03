#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add missing status options and redesign status selector:
1. Add "접촉해제" and "실패" options
2. Convert from radio buttons to button-based UI
3. Position below grid as shown in reference image
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace the radio button group with button-based status selector
old_status_group = r'<div id="memo_status_group"[^>]*>.*?</div>\s*</div>'

new_status_group = '''<div id="memo_status_group" style="display: flex; gap: 8px; flex-wrap: wrap; padding: 8px 0;">
                        <button type="button" class="status-btn" data-status="접촉대기" style="padding: 6px 14px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all 0.2s;" onclick="selectStatus(this, '접촉대기')">접촉대기</button>
                        <button type="button" class="status-btn" data-status="접촉중" style="padding: 6px 14px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all 0.2s;" onclick="selectStatus(this, '접촉중')">접촉중</button>
                        <button type="button" class="status-btn" data-status="접촉해제" style="padding: 6px 14px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all 0.2s;" onclick="selectStatus(this, '접촉해제')">접촉해제</button>
                        <button type="button" class="status-btn" data-status="완료" style="padding: 6px 14px; border: 1px solid #4a90e2; background: #4a90e2; color: white; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all 0.2s;" onclick="selectStatus(this, '완료')">완료</button>
                        <button type="button" class="status-btn" data-status="실패" style="padding: 6px 14px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all 0.2s;" onclick="selectStatus(this, '실패')">실패</button>
                        <input type="hidden" id="selected_status" value="완료">
                    </div>
                    <div style="margin-top: 8px;">'''

content = re.sub(old_status_group, new_status_group, content, flags=re.DOTALL)

# 2. Add JavaScript function to handle status selection
status_js = '''
        // Status button selection
        function selectStatus(btn, status) {
            // Remove selected style from all buttons
            document.querySelectorAll('.status-btn').forEach(b => {
                b.style.background = 'white';
                b.style.color = '#333';
                b.style.borderColor = '#ddd';
            });
            
            // Add selected style to clicked button
            btn.style.background = '#4a90e2';
            btn.style.color = 'white';
            btn.style.borderColor = '#4a90e2';
            
            // Update hidden input
            document.getElementById('selected_status').value = status;
        }
'''

# Add the function before closing script tag
if 'function selectStatus' not in content:
    content = content.replace('</script>', status_js + '\n    </script>')

# 3. Update saveMemo to use hidden input instead of radio button
content = re.sub(
    r"const status = document\.querySelector\('input\[name=\"memo_status\"\]:checked'\)\?\.value \|\| '완료';",
    "const status = document.getElementById('selected_status').value || '완료';",
    content
)

# 4. Update loadMemoAndHistory to select button instead of radio
content = re.sub(
    r"const radioBtn = document\.querySelector\(`input\[name=\"memo_status\"\]\[value=\"\$\{status\}\"\]`\); if \(radioBtn\) radioBtn\.checked = true;",
    """const statusBtn = document.querySelector(`.status-btn[data-status="${status}"]`);
            if (statusBtn) {
                selectStatus(statusBtn, status);
            }""",
    content
)

# 5. Add CSS for status buttons
status_css = '''
        /* Status button styles */
        .status-btn:hover {
            opacity: 0.8;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .status-btn:active {
            transform: translateY(0);
        }
'''

if '.status-btn:hover' not in content:
    content = content.replace('</style>', status_css + '\n    </style>')

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Status selector redesigned successfully!")
print("\nChanges:")
print("1. Added missing status options: 접촉해제, 실패")
print("2. Converted radio buttons to button-based UI")
print("3. Total 5 status buttons: 접촉대기, 접촉중, 접촉해제, 완료, 실패")
print("4. Added selectStatus() JavaScript function")
print("5. Updated saveMemo and loadMemoAndHistory functions")
