import re

# 파일 읽기
with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 필요한 모든 함수 찾기
functions_to_move = [
    'formatDateTime',
    'formatDateTimeForInput',
    'submitContactHistory',
    'editContactHistory',
    'updateContactHistory',
    'deleteContactHistory',
    'closeEditContactModal'
]

# 전역 변수도 필요
global_vars = ['let contactEditingId = null;']

# <script> 태그 찾기 (45번 라인 근처)
script_start = content.find('    <script>')
script_insert_pos = content.find('\n', script_start) + 1

# 추가할 코드 생성
additional_code = "\n    // 접촉이력 관련 전역 변수 및 헬퍼 함수들\n"
additional_code += "    let contactEditingId = null;\n\n"

# formatDateTime 함수
additional_code += """    function formatDateTime(dateTimeStr) {
        if (!dateTimeStr) return '';
        const dt = new Date(dateTimeStr);
        return dt.toLocaleString('ko-KR', { 
            year: 'numeric', 
            month: '2-digit', 
            day: '2-digit', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

"""

# formatDateTimeForInput 함수
additional_code += """    function formatDateTimeForInput(dateTimeStr) {
        if (!dateTimeStr) return '';
        const dt = new Date(dateTimeStr);
        const year = dt.getFullYear();
        const month = String(dt.getMonth() + 1).padStart(2, '0');
        const day = String(dt.getDate()).padStart(2, '0');
        const hours = String(dt.getHours()).padStart(2, '0');
        const minutes = String(dt.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }

"""

# loadContactHistory 함수 바로 앞에 삽입
load_contact_pos = content.find('    async function loadContactHistory()')
if load_contact_pos > 0:
    content = content[:load_contact_pos] + additional_code + content[load_contact_pos:]
    print("✅ 헬퍼 함수들이 추가되었습니다!")
else:
    print("❌ loadContactHistory 함수를 찾을 수 없습니다!")
    
# 파일 저장
with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ detail.html 파일이 수정되었습니다!")
