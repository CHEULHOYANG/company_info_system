import re

# 파일 읽기
with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 정확한 교체를 위한 패턴
old_pattern = r'''                            // 기존 API 사용 \(/api/history_search\)
                            const response = await fetch\(`/api/history_search\?biz_no=\$\{bizNo\}`\);
                            const data = await response\.json\(\);

                            // 기존 API는 배열로 직접 반환함
                            if \(Array\.isArray\(data\) && data\.length > 0\) \{
                                displayContactHistory\(data\);'''

new_code = '''                            // contact_history 테이블에서 biz_no로 직접 조회
                            const response = await fetch(`/api/contact_history?biz_no=${bizNo}`);
                            const result = await response.json();

                            // API는 {success: true, data: [...]} 형식으로 반환
                            if (result.success && result.data && result.data.length > 0) {
                                displayContactHistory(result.data);'''

# 교체 수행
new_content = re.sub(old_pattern, new_code, content)

# 변경사항 확인
if content != new_content:
    # 파일 쓰기
    with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ 성공적으로 수정되었습니다!")
    print("- API 엔드포인트: /api/history_search → /api/contact_history")
    print("- 응답 처리: Array.isArray(data) → result.success && result.data")
else:
    print("❌ 변경사항이 없습니다. 패턴을 확인해주세요.")
