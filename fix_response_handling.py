#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
응답 처리 로직도 수정
"""

with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== 응답 처리 로직 수정 ===\n")

# 라인 1112: const data → const result
if 1111 < len(lines) and 'const data = await response.json()' in lines[1111]:
    lines[1111] = lines[1111].replace('const data', 'const result')
    print("✅ 라인 1112: const data → const result")

# 라인 1115: Array.isArray(data) → result.success && result.data
if 1114 < len(lines):
    old_line = lines[1114]
    if 'Array.isArray(data)' in old_line:
        lines[1114] = old_line.replace('Array.isArray(data) && data.length', 'result.success && result.data && result.data.length')
        print("✅ 라인 1115: 조건문 수정")

# 라인 1116: displayContactHistory(data) → displayContactHistory(result.data)
if 1115 < len(lines) and 'displayContactHistory(data)' in lines[1115]:
    lines[1115] = lines[1115].replace('displayContactHistory(data)', 'displayContactHistory(result.data)')
    print("✅ 라인 1116: displayContactHistory 인자 수정")

# 파일 저장
with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n=== ✅ 응답 처리 수정 완료! ===")
