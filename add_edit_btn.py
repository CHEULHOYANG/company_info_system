# Add CSS style for edit-btn-small and JavaScript functions
content = open('g:/company_project_system/templates/detail.html', encoding='cp949').read()

# 1. Add CSS for .edit-btn-small after .delete-btn-small
css_to_find = '''    .delete-btn-small:hover {
        background: #c82333;
    }'''

css_replacement = '''    .delete-btn-small:hover {
        background: #c82333;
    }
    
    /* 수정 버튼 스타일 (소형) */
    .edit-btn-small {
        padding: 3px 8px;
        border: none;
        border-radius: 4px;
        background: #17a2b8;
        color: white;
        cursor: pointer;
        font-size: 11px;
        margin-right: 4px;
    }
    .edit-btn-small:hover {
        background: #138496;
    }'''

if css_to_find in content:
    content = content.replace(css_to_find, css_replacement)
    print("SUCCESS: Added CSS for edit-btn-small")
else:
    print("ERROR: Could not find CSS pattern")

# 2. Add JavaScript functions for editRepresentative and editShareholder
# Find the deleteRepresentative function and add editRepresentative before it
js_to_find = '''async function deleteRepresentative(bizNo, repName, rowIndex) {'''

js_replacement = '''// 대표자 정보 수정
async function editRepresentative(bizNo, currentName, currentBirthDate) {
    const newName = prompt('대표자명을 입력하세요:', currentName);
    if (newName === null) return;
    
    const newBirthDate = prompt('생년월일을 입력하세요 (YYYYMMDD):', currentBirthDate);
    if (newBirthDate === null) return;
    
    try {
        const response = await fetch('/api/update_representative_info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                biz_no: bizNo, 
                old_name: currentName, 
                new_name: newName,
                birth_date: newBirthDate
            })
        });
        const result = await response.json();
        if (result.success) {
            alert('대표자 정보가 수정되었습니다.');
            location.reload();
        } else {
            alert('수정 실패: ' + (result.message || '알 수 없는 오류'));
        }
    } catch (error) {
        alert('오류 발생: ' + error.message);
    }
}

// 주주 정보 수정
async function editShareholder(bizNo, currentName, currentStockQty) {
    const newName = prompt('주주명을 입력하세요:', currentName);
    if (newName === null) return;
    
    const newStockQty = prompt('주식수를 입력하세요:', currentStockQty);
    if (newStockQty === null) return;
    
    try {
        const response = await fetch('/api/update_shareholder_info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                biz_no: bizNo, 
                old_name: currentName, 
                new_name: newName,
                stock_quantity: newStockQty
            })
        });
        const result = await response.json();
        if (result.success) {
            alert('주주 정보가 수정되었습니다.');
            location.reload();
        } else {
            alert('수정 실패: ' + (result.message || '알 수 없는 오류'));
        }
    } catch (error) {
        alert('오류 발생: ' + error.message);
    }
}

async function deleteRepresentative(bizNo, repName, rowIndex) {'''

if js_to_find in content:
    content = content.replace(js_to_find, js_replacement)
    print("SUCCESS: Added JavaScript functions")
else:
    print("ERROR: Could not find JavaScript pattern")

with open('g:/company_project_system/templates/detail.html', 'w', encoding='cp949') as f:
    f.write(content)

print("File saved with CSS and JavaScript")
