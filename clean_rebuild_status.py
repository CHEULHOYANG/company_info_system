#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Clean up individual_list.html and rebuild status selector properly:
1. Remove all duplicate status button code
2. Create ONE clean status selector section
3. Equal-width buttons (flex-based grid)
4. Green save button (distinct from status buttons)
5. Clean separation between sections
"""

import re

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find ALL occurrences of status button sections and remove them
# We'll rebuild from scratch
patterns_to_remove = [
    r'<div[^>]*id="memo_status_group"[^>]*>.*?</div>\s*</div>',
    r'<div[^>]*style="margin-top: 16px; padding: 16px[^"]*">.*?</div>',
    r'<button[^>]*class="status-btn"[^>]*>.*?</button>',
]

for pattern in patterns_to_remove:
    content = re.sub(pattern, '', content, flags=re.DOTALL)

# Find the memo textarea section - we'll add status selector after it
memo_textarea_pattern = r'(<textarea[^>]*id="detail_memo"[^>]*>.*?</textarea>)'

# Create the clean, properly designed status selector
clean_status_selector = r'''\1
                    
                    <!-- Status Selector Section -->
                    <div style="margin-top: 20px; padding: 16px; background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); border-radius: 8px; border: 1px solid #e8e8e8;">
                        <div style="font-size: 13px; font-weight: 600; color: #2c3e50; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                            <span style="width: 3px; height: 14px; background: #4a90e2; border-radius: 2px;"></span>
                            진행 상태 선택
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 14px;">
                            <button type="button" class="status-btn" data-status="접촉대기" 
                                    onclick="selectStatusClean(this, '접촉대기')"
                                    style="padding: 10px 8px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666;">
                                접촉대기
                            </button>
                            <button type="button" class="status-btn" data-status="접촉중"
                                    onclick="selectStatusClean(this, '접촉중')"
                                    style="padding: 10px 8px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666;">
                                접촉중
                            </button>
                            <button type="button" class="status-btn" data-status="접촉해제"
                                    onclick="selectStatusClean(this, '접촉해제')"
                                    style="padding: 10px 8px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666;">
                                접촉해제
                            </button>
                            <button type="button" class="status-btn" data-status="완료"
                                    onclick="selectStatusClean(this, '완료')"
                                    style="padding: 10px 8px; border: 2px solid #4a90e2; background: #4a90e2; color: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s;">
                                완료
                            </button>
                            <button type="button" class="status-btn" data-status="실패"
                                    onclick="selectStatusClean(this, '실패')"
                                    style="padding: 10px 8px; border: 2px solid #e0e0e0; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; color: #666;">
                                실패
                            </button>
                        </div>
                        <input type="hidden" id="selected_status" value="완료">
                        <button onclick="saveMemo()" 
                                style="width: 100%; padding: 13px; background: linear-gradient(135deg, #28a745 0%, #34ce57 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; box-shadow: 0 3px 6px rgba(40,167,69,0.3); transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px;"
                                onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 5px 10px rgba(40,167,69,0.35)'"
                                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 3px 6px rgba(40,167,69,0.3)'">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                                <polyline points="17 21 17 13 7 13 7 21"></polyline>
                                <polyline points="7 3 7 8 15 8"></polyline>
                            </svg>
                            메모 및 상태 저장
                        </button>
                    </div>'''

content = re.sub(memo_textarea_pattern, clean_status_selector, content, flags=re.DOTALL)

# Remove old selectStatus function and add clean one
old_function_pattern = r'function selectStatus.*?\{.*?\n\s+\}'
new_function = '''function selectStatusClean(btn, status) {
            document.querySelectorAll('.status-btn').forEach(b => {
                b.style.background = 'white';
                b.style.color = '#666';
                b.style.borderColor = '#e0e0e0';
            });
            btn.style.background = '#4a90e2';
            btn.style.color = 'white';
            btn.style.borderColor = '#4a90e2';
            document.getElementById('selected_status').value = status;
        }'''

content = re.sub(old_function_pattern, new_function, content, flags=re.DOTALL)

# Update saveMemo to use the new hidden input
content = re.sub(
    r"const status = document\.querySelector\('input\[name=\"memo_status\"\]:checked'\)\?\.value.*?;",
    "const status = document.getElementById('selected_status')?.value || '완료';",
    content
)

# Update loadMemoAndHistory
content = re.sub(
    r"const radioBtn = document\.querySelector.*?memo_status.*?\);.*?if.*?radioBtn.*?\).*?radioBtn\.checked = true;",
    """const currentStatus = row.dataset.status || '완료';
            document.getElementById('selected_status').value = currentStatus;
            const statusBtn = document.querySelector(`.status-btn[data-status="\${currentStatus}"]`);
            if (statusBtn) selectStatusClean(statusBtn, currentStatus);""",
    content,
    flags=re.DOTALL
)

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Clean status selector created!")
print("\nKey improvements:")
print("1. ✅ Single, non-duplicate status section")
print("2. ✅ Equal-width buttons using CSS Grid")
print("3. ✅ GREEN save button with icon (clearly distinct)")
print("4. ✅ Clean visual hierarchy")
print("5. ✅ Proper spacing and professional design")
