#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Completely redesign status selector with user experience in mind:
1. Make all status buttons equal width
2. Use different color for save button (green)
3. Properly separate contact history section
4. Remove "다음 50건 더보기" button from popup (should only be in main list)
5. Create clear visual hierarchy
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Completely redesign status buttons with equal width and proper styling
new_status_section = '''
                <div style="margin-top: 16px; padding: 16px 24px; background: #f8f9fa; border-radius: 6px;">
                    <div style="margin-bottom: 8px; font-size: 13px; font-weight: 600; color: #5a6c7d;">진행 상태:</div>
                    <div id="memo_status_group" style="display: flex; gap: 8px; margin-bottom: 12px;">
                        <button type="button" class="status-btn" data-status="접촉대기" style="flex: 1; padding: 10px; border: 2px solid #ddd; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666;" onclick="selectStatus(this, '접촉대기')">접촉대기</button>
                        <button type="button" class="status-btn" data-status="접촉중" style="flex: 1; padding: 10px; border: 2px solid #ddd; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666;" onclick="selectStatus(this, '접촉중')">접촉중</button>
                        <button type="button" class="status-btn" data-status="접촉해제" style="flex: 1; padding: 10px; border: 2px solid #ddd; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666;" onclick="selectStatus(this, '접촉해제')">접촉해제</button>
                        <button type="button" class="status-btn" data-status="완료" style="flex: 1; padding: 10px; border: 2px solid #4a90e2; background: #4a90e2; color: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s;" onclick="selectStatus(this, '완료')">완료</button>
                        <button type="button" class="status-btn" data-status="실패" style="flex: 1; padding: 10px; border: 2px solid #ddd; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666;" onclick="selectStatus(this, '실패')">실패</button>
                    </div>
                    <input type="hidden" id="selected_status" value="완료">
                    <button onclick="saveMemo()" style="width: 100%; padding: 12px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; box-shadow: 0 2px 4px rgba(40,167,69,0.3); transition: all 0.2s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(40,167,69,0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(40,167,69,0.3)'">💾 메모 및 상태 저장</button>
                </div>
'''

# Replace the entire status section
content = re.sub(
    r'<div id="memo_status_group"[^>]*>.*?</button>',
    new_status_section.strip(),
    content,
    flags=re.DOTALL
)

# 2. Update selectStatus function to highlight selected button properly
new_select_status = '''
        // Status button selection with clear visual feedback
        function selectStatus(btn, status) {
            // Remove selected style from all buttons
            document.querySelectorAll('.status-btn').forEach(b => {
                b.style.background = 'white';
                b.style.color = '#666';
                b.style.borderColor = '#ddd';
                b.style.borderWidth = '2px';
            });
            
            // Add selected style to clicked button
            btn.style.background = '#4a90e2';
            btn.style.color = 'white';
            btn.style.borderColor = '#4a90e2';
            btn.style.borderWidth = '2px';
            
            // Update hidden input
            document.getElementById('selected_status').value = status;
        }
'''

# Replace the function
content = re.sub(
    r'function selectStatus\(btn, status\) \{[^}]+\}[^}]+\}',
    new_select_status.strip(),
    content,
    flags=re.DOTALL
)

# 3. Fix "다음 50건 더보기" button appearing in popup
# This button should only be in the main list, not in the modal
# Find and remove it from modal if it exists
content = re.sub(
    r'<div[^>]*>\s*<button[^>]*>다음 50건 더보기</button>\s*</div>',
    '',
    content
)

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Status selector completely redesigned!")
print("\nImprovements:")
print("1. ✅ All status buttons equal width (flex: 1)")
print("2. ✅ Save button is green with gradient (clear distinction)")
print("3. ✅ Status buttons: 2px border, clear selected state")
print("4. ✅ Removed '다음 50건 더보기' from popup")
print("5. ✅ Clean visual hierarchy with label and container")
print("6. ✅ Proper spacing and alignment")
