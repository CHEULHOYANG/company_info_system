import os

file_path = r'g:\company_project_system\templates\user_management.html'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if '<option value="V">V - 메인관리자</option>' in line:
        indent = line[:line.find('<')]
        line_to_add = f'{indent}<option value="VIP">VIP - VIP관리자</option>\n'
        if line_to_add not in new_lines:
            new_lines.append(line_to_add)
        new_lines.append(line)
    elif "'V': '메인관리자'," in line:
        indent = line[:line.find("'")]
        line_to_add = f"{indent}'VIP': 'VIP관리자',\n"
        if line_to_add not in new_lines:
            new_lines.append(line_to_add)
        new_lines.append(line)
    elif ".level-v {" in line:
        indent = line[:line.find(".")]
        line_to_add = f"{indent}.level-vip {{ background: linear-gradient(135deg, #f1c40f 0%, #f39c12 100%); color: white; padding: 2px 8px; border-radius: 15px; font-size: 11px; }}\n"
        if line_to_add not in new_lines:
            new_lines.append(line_to_add)
        new_lines.append(line)
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Updated successfully")
