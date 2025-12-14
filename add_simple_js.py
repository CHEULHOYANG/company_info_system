#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add minimal JavaScript for edit functionality
"""

# Read with binary
with open(r'g:\company_project_system\templates\detail.html', 'rb') as f:
    content = f.read().decode('cp949')

# Simple JavaScript to add
simple_js = '''
<script>
function editRep(idx) {
    const name = prompt('새로운 이름을 입력하세요:', document.getElementById('rep-name-' + idx).innerText);
    if (name) {
        fetch('/api/update_representative_name', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({biz_no: '{{ company.basic.biz_no }}', representative_name: name})
        }).then(r => r.json()).then(d => { if(d.success) { document.getElementById('rep-name-' + idx).innerText = name; alert('수정되었습니다'); location.reload(); } else { alert('실패: ' + d.message); } });
    }
}
function editShare(idx) {
    const oldName = document.getElementById('share-name-' + idx).innerText;
    const name = prompt('새로운 이름을 입력하세요:', oldName);
    if (name) {
        fetch('/api/update-shareholder', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({biz_no: '{{ company.basic.biz_no }}', old_shareholder_name: oldName, new_shareholder_name: name})
        }).then(r => r.json()).then(d => { if(d.success) { document.getElementById('share-name-' + idx).innerText = name; alert('수정되었습니다'); location.reload(); } else { alert('실패: ' + d.message); } });
    }
}
</script>
'''

# Insert before </body>
if '</body>' in content:
    content = content.replace('</body>', simple_js + '\n</body>')
    print("✓ JavaScript added before </body>")
else:
    print("✗ Could not find </body> tag")

# Write back
with open(r'g:\company_project_system\templates\detail.html', 'wb') as f:
    f.write(content.encode('cp949'))

print("✓ File updated successfully!")
print("\n🎉 DONE! Restart server and refresh page to see edit buttons.")
