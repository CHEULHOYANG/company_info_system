#!/usr/bin/env python
# -*- coding: utf-8 -*-

# detail.html 수정 스크립트 - window 객체에 함수 할당

with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== detail.html 수정 시작 ===\n")

# 1. 라인 1103: loadContactHistory 함수 시작 부분에 window 할당 추가
if 'async function loadContactHistory()' in lines[1102]:
    # 함수 정의 바로 다음에 window 할당 추가
    lines.insert(1103, '                    window.loadContactHistory = loadContactHistory;\n')
    print("✅ 라인 1104에 window.loadContactHistory 할당 추가")

# 2. API 엔드포인트 변경 (이제 라인이 하나 밀렸으므로 1111 -> 1112)
for i, line in enumerate(lines):
    if i > 1108 and i < 1114 and '/api/history_search' in line:
        lines[i] = line.replace('/api/history_search', '/api/contact_history')
        print(f"✅ 라인 {i+1}: API 엔드포인트 변경")
        
        # 주석도 수정
        if '// 기존  API 사용' in lines[i-1]:
            lines[i-1] = lines[i-1].replace('// 기존 API 사용 (/api/history_search)', '// contact_history 테이블에서 biz_no로 직접 조회')
            print(f"✅ 라인 {i}: 주석 수정")
        break

# 3. 응답 처리 로직 변경
for i, line in enumerate(lines):
    if i > 1110 and i < 1116:
        # const data → const result
        if 'const data = await response.json()' in line:
            lines[i] = line.replace('const data', 'const result')
            print(f"✅ 라인 {i+1}: const data → const result")
        
        # 주석 변경
        if '// 기존 API는 배열로 직접 반환함' in line:
            lines[i] = line.replace('// 기존 API는 배열로 직접 반환함', '// API는 {success: true, data: [...]} 형식으로 반환')
            print(f"✅ 라인 {i+1}: 주석 수정")
        
        # 조건문 변경
        if 'Array.isArray(data) && data.length' in line:
            lines[i] = line.replace('Array.isArray(data) && data.length', 'result.success && result.data && result.data.length')
            print(f"✅ 라인 {i+1}: 조건문 수정")
        
        # 함수 호출 변경
        if 'displayContactHistory(data)' in line:
            lines[i] = line.replace('displayContactHistory(data)', 'displayContactHistory(result.data)')
            print(f"✅ 라인 {i+1}: 함수 호출 인자 수정")

# 4. displayContactHistory 함수 시작 부분에 window 할당 추가
for i, line in enumerate(lines):
    if i > 1126 and 'function displayContactHistory(historyList)' in line:
        lines.insert(i+1, '                        window.displayContactHistory = displayContactHistory;\n')
        print(f"✅ 라인 {i+2}에 window.displayContactHistory 할당 추가")
        break

# 파일 저장
with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n=== detail.html 수정 완료! ===")
print("\n수정 내용 요약:")
print("  1. window.loadContactHistory 할당 추가")
print("  2. window.displayContactHistory 할당 추가")
print("  3. API 엔드포인트: /api/history_search → /api/contact_history")
print("  4. 응답 처리: data → result.data")
