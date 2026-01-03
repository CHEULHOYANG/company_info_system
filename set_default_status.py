#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Update initial status to select 접촉대기 button instead of leaving unselected
"""

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the else block in loadMemoAndHistory
old_else_block = '''} else {
                        // 초기 상태: 모든 버튼 선택 해제
                        resetAllStatusButtons();
                        document.getElementById('selected_status').value = '';
                    }'''

new_else_block = '''} else {
                        // 초기 상태: 접촉대기 선택
                        const 접촉대기Btn = document.querySelector('.status-btn[data-status="접촉대기"]');
                        if (접촉대기Btn) selectStatus(접촉대기Btn, '접촉대기');
                    }'''

if old_else_block in content:
    content = content.replace(old_else_block, new_else_block)
    print("✅ Updated initial status to select 접촉대기")
else:
    print("❌ Could not find target block")
    # Try to find it and show context
    if '// 초기 상태: 모든 버튼 선택 해제' in content:
        print("Found comment but block structure different")
    exit(1)

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ File updated successfully!")
print("\n📌 이제 초기 상태일 때 자동으로 '접촉대기' 버튼이 선택됩니다.")
print("🔄 브라우저에서 Ctrl+Shift+R로 새로고침하세요!")
