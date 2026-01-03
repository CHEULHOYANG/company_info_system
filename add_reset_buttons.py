#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add resetAllStatusButtons function and update loadMemoAndHistory
"""

# Read file
with open('g:/company_project_system/templates/individual_list.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "// 상태 버튼 선택"
# Add resetAllStatusButtons function before selectStatus
insert_line = None
for i, line in enumerate(lines):
    if '// 상태 버튼 선택' in line or 'function selectStatus(btn, status)' in line:
        # Check if resetAllStatusButtons already exists nearby
        context = ''.join(lines[max(0, i-10):i])
        if 'resetAllStatusButtons' not in context:
            insert_line = i
            break

if insert_line:
    # Insert the resetAllStatusButtons function
    new_function = '''        // 모든 상태 버튼 선택 해제
        function resetAllStatusButtons() {
            document.querySelectorAll('.status-btn').forEach(btn => {
                btn.style.background = 'white';
                btn.style.color = '#666';
                btn.style.borderColor = '#e0e0e0';
            });
        }

'''
    lines.insert(insert_line, new_function)
    print(f"✅ Added resetAllStatusButtons function at line {insert_line}")
else:
    print("❌ Could not find insertion point")

# Now find the else block in loadMemoAndHistory and update it
updated = False
for i, line in enumerate(lines):
    if '// 초기 상태: 아무 버튼도 선택하지 않음' in line:
        # Check next line
        if i + 1 < len(lines) and 'selected_status' in lines[i + 1]:
            # Add resetAllStatusButtons call
            indent = ' ' * 24  # 6 levels of 4 spaces
            lines[i] = f"{indent}// 초기 상태: 모든 버튼 선택 해제\n"
            lines.insert(i + 1, f"{indent}resetAllStatusButtons();\n")
            updated = True
            print(f"✅ Updated loadMemoAndHistory at line {i}")
            break

if not updated:
    print("⚠️  Could not find loadMemoAndHistory else block (may already be updated)")

# Save
with open('g:/company_project_system/templates/individual_list.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n✅ File updated successfully!")
print("\n🔄 브라우저에서 Ctrl+Shift+R (Hard Refresh)를 눌러 캐시를 지우세요!")
