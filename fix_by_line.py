#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
정확한 라인만 수정하는 스크립트
"""

with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== 파일 읽기 완료 ===")
print(f"총 라인 수: {len(lines)}\n")

#라인 1111: /api/history_search → /api/contact_history
if 1110 < len(lines):
    original_line = lines[1110]
    if '/api/history_search' in original_line:
        lines[1110] = original_line.replace('/api/history_search', '/api/contact_history')
        print("✅ 라인 1111: API 엔드포인트 변경")
        print(f"   이전: {original_line.strip()}")
        print(f"   이후: {lines[1110].strip()}\n")

# 라인 1103: async function loadContactHistory() → window.loadContactHistory = async function()
if 1102 < len(lines):
    original_line = lines[1102]
    if 'async function loadContactHistory()' in original_line:
        lines[1102] = original_line.replace('async function loadContactHistory()', 'window.loadContactHistory = async function()')
        print("✅ 라인 1103: loadContactHistory window 할당")
        print(f"   이전: {original_line.strip()}")
        print(f"   이후: {lines[1102].strip()}\n")

# 라인 1127: function displayContactHistory(historyList) → window.displayContactHistory = function(historyList)
if 1126 < len(lines):
    original_line = lines[1126]
    if 'function displayContactHistory(historyList)' in original_line:
        lines[1126] = original_line.replace('function displayContactHistory(historyList)', 'window.displayContactHistory = function(historyList)')
        print("✅ 라인 1127: displayContactHistory window 할당")
        print(f"   이전: {original_line.strip()}")
        print(f"   이후: {lines[1126].strip()}\n")

# 파일 저장
with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("=== ✅ 파일 수정 완료! ===")
