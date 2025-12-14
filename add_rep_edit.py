import re

# Read the file
with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Find the line with rep.name and add edit button
modified = []
for i, line in enumerate(lines):
    modified.append(line)
    
    # Add edit button for representative name if it contains asterisk
    if 'rep.name' in line and '<td>' in line:
        # Check if next few lines don't already have edit button
        has_edit = any('edit-rep-btn' in lines[j] for j in range(max(0, i-2), min(len(lines), i+5)))
        if not has_edit:
            indent = ' ' * (len(line) - len(line.lstrip()))
            # Add edit button HTML after the name display
            edit_html = f'''{indent}                            <div id="rep-name-display-{{{{ loop.index }}}}" style="display: inline-block;">
{indent}                                <span id="rep-name-text-{{{{ loop.index }}}}">{{{{ rep.name }}}}</span>
{indent}                                {{% if rep.name and '*' in rep.name %}}
{indent}                                <button id="edit-rep-btn-{{{{ loop.index }}}}" onclick="editRepresentativeName({{{{ loop.index }}}}, '{{{{ rep.name }}}}')"
{indent}                                    style="margin-left: 8px; padding: 4px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">수정</button>
{indent}                                {{% endif %}}
{indent}                            </div>
{indent}                            <div id="rep-name-edit-{{{{ loop.index }}}}" style="display: none;">
{indent}                                <input type="text" id="rep-name-input-{{{{ loop.index }}}}" value="{{{{ rep.name }}}}"
{indent}                                    style="padding: 6px; border: 2px solid #007bff; border-radius: 4px; font-size: 14px; width: 120px;">
{indent}                                <button onclick="saveRepresentativeName({{{{ loop.index }}}}, '{{{{ rep.name }}}}')"
{indent}                                    style="margin-left: 4px; padding: 6px 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">저장</button>
{indent}                                <button onclick="cancelEditRepresentativeName({{{{ loop.index }}}})"
{indent}                                    style="margin-left: 4px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">취소</button>
{indent}                            </div>
'''
            # Replace the current line with the edit HTML
            modified[-1] = line.replace('{{ rep.name }}', edit_html)

# Write back
with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
    f.writelines(modified)

print("Representative edit button added successfully!")
