#!/usr/bin/env python
# -*- coding: utf-8 -*-

# detail.html의 정확히 2줄만 수정하는 스크립트

with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 라인 1111: API 엔드포인트 변경
if 'history_search' in lines[1110]:  # 0-indexed이므로 1111번 라인은 인덱스 1110
    lines[1110] = lines[1110].replace('/api/history_search', '/api/contact_history')
    print(f"✅ 라인 1111 수정완료: /api/history_search → /api/contact_history")
else:
    print(f"⚠️  라인 1111에 history_search가 없습니다: {lines[1110].strip()}")

# 라인 1112: 변수명 변경 (data → result)
if 'const data = await response.json()' in lines[1111]:
    lines[1111] = lines[1111].replace('const data', 'const result')
    print(f"✅ 라인 1112 수정완료: const data → const result")
else:
    print(f"⚠️  라인 1112에 'const data'가 없습니다: {lines[1111].strip()}")

# 라인 1115: 조건문 변경 (Array.isArray(data) → result.success && result.data)
if 'Array.isArray(data)' in lines[1114]:
    lines[1114] = lines[1114].replace('Array.isArray(data) && data.length', 'result.success && result.data && result.data.length')
    print(f"✅ 라인 1115 수정완료: Array.isArray(data) → result.success && result.data")
else:
    print(f"⚠️  라인 1115에 'Array.isArray(data)'가 없습니다: {lines[1114].strip()}")

# 라인 1116: displayContactHistory 인자 변경 (data → result.data)
if 'displayContactHistory(data)' in lines[1115]:
    lines[1115] = lines[1115].replace('displayContactHistory(data)', 'displayContactHistory(result.data)')
    print(f"✅ 라인 1116 수정완료: displayContactHistory(data) → displayContactHistory(result.data)")
else:
    print(f"⚠️  라인 1116에 'displayContactHistory(data)'가 없습니다: {lines[1115].strip()}")

# 파일 저장
with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n✅ detail.html 파일 수정 완료!")
print("\n수정된 내용:")
print("  - API 엔드포인트: /api/history_search → /api/contact_history")
print("  - 응답 처리: data → result, Array 체크 → success 체크")
