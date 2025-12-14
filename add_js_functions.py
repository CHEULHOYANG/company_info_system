#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Read file
with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='cp949', errors='ignore') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Function to add JavaScript functions at the end
js_functions = '''
    <script>
        // 대표자명 수정 함수
        function editRepresentativeName(index, oldName) {
            document.getElementById('rep-name-display-' + index).style.display = 'none';
            document.getElementById('rep-name-edit-' + index).style.display = 'inline-block';
        }

        function cancelEditRepresentativeName(index) {
            document.getElementById('rep-name-display-' + index).style.display = 'inline-block';
            document.getElementById('rep-name-edit-' + index).style.display = 'none';
            const originalText = document.getElementById('rep-name-text-' + index).innerText;
            document.getElementById('rep-name-input-' + index).value = originalText;
        }

        function saveRepresentativeName(index, oldName) {
            const newName = document.getElementById('rep-name-input-' + index).value.trim();
            if (!newName) {
                alert('이름을 입력해주세요.');
                return;
            }

            let bizNo = '{{ company.basic.biz_no }}';

            fetch('/api/update_representative_name', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    biz_no: bizNo,
                    representative_name: newName
                })
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    document.getElementById('rep-name-text-' + index).innerText = newName;
                    document.getElementById('rep-name-display-' + index).style.display = 'inline-block';
                    document.getElementById('rep-name-edit-' + index).style.display = 'none';
                    alert('대표자명이 수정되었습니다.');
                    if (!newName.includes('*')) {
                        const btn = document.getElementById('edit-rep-btn-' + index);
                        if (btn) btn.style.display = 'none';
                    }
                } else {
                    alert('수정 실패: ' + (result.message || '알 수 없는 오류'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('오류가 발생했습니다.');
            });
        }

        // 주주명 수정 함수
        function editShareholderName(index, oldName) {
            document.getElementById('shareholder-name-display-' + index).style.display = 'none';
            document.getElementById('shareholder-name-edit-' + index).style.display = 'inline-block';
        }

        function cancelEditShareholderName(index) {
            document.getElementById('shareholder-name-display-' + index).style.display = 'inline-block';
            document.getElementById('shareholder-name-edit-' + index).style.display = 'none';
            const originalText = document.getElementById('shareholder-name-text-' + index).innerText;
            document.getElementById('shareholder-name-input-' + index).value = originalText;
        }

        function saveShareholderName(index, oldName) {
            const newName = document.getElementById('shareholder-name-input-' + index).value.trim();
            if (!newName) {
                alert('주주명을 입력해주세요.');
                return;
            }

            let bizNo = '{{ company.basic.biz_no }}';

            fetch('/api/update-shareholder', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    biz_no: bizNo,
                    old_shareholder_name: oldName,
                    new_shareholder_name: newName
                })
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    document.getElementById('shareholder-name-text-' + index).innerText = newName;
                    document.getElementById('shareholder-name-display-' + index).style.display = 'inline-block';
                    document.getElementById('shareholder-name-edit-' + index).style.display = 'none';
                    alert('주주명이 수정되었습니다.');
                    if (!newName.includes('*')) {
                        const btn = document.getElementById('edit-shareholder-btn-' + index);
                        if (btn) btn.style.display = 'none';
                    }
                } else {
                    alert('수정 실패: ' + (result.message || '알 수 없는 오류'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('오류가 발생했습니다.');
            });
        }
    </script>
'''

# Find </body> tag and insert JavaScript before it
for i in range(len(lines) - 1, -1, -1):
    if '</body>' in lines[i]:
        lines.insert(i, js_functions + '\n')
        print(f"✓ Inserted JavaScript functions before line {i+1}")
        break

# Write back
with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✓ JavaScript functions added successfully!")
print("Now you need to manually add edit buttons to the HTML where rep.name and holder.shareholder_name are displayed.")
