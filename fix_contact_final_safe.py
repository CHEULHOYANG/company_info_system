#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
detail.html 접촉이력 기능 완전 수정 스크립트
간단하고 명확하게 2가지만 수정:
1. loadContactHistory와 displayContactHistory를 window 객체에 할당
2. formatDateTime를 window 객체에 할당
"""

import re

with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("=== detail.html 수정 시작 ===\n")

# 1. loadContactHistory 함수를 window에 할당 (async function 형태)
original_load = r'async function loadContactHistory\(\) \{'
new_load = 'window.loadContactHistory = async function() {'
if re.search(original_load, content):
    content = re.sub(original_load, new_load, content, count=1)
    print("✅ loadContact History를 window에 할당")

# 2. displayContactHistory 함수를 window에 할당
original_display = r'function displayContactHistory\(historyList\) \{'
new_display = 'window.displayContactHistory = function(historyList) {'
if re.search(original_display, content):
    content = re.sub(original_display, new_display, content, count=1)
    print("✅ displayContactHistory를 window에 할당")

# 3. formatDateTime 함수를 window에 할당  
original_format = r'function formatDateTime\(dateTimeStr\) \{'
new_format = 'window.formatDateTime = function(dateTimeStr) {'
if re.search(original_format, content):
    content = re.sub(original_format, new_format, content, count=1)
    print("✅ formatDateTime을 window에 할당")

# 파일에 저장
with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n=== ✅ 수정 완료! ===")
print("\n다음 단계:")
print("  1. Flask 서버 재시작 (Ctrl+C 후 다시 실행)")
print("  2. 브라우저에서 Ctrl+Shift+R로 새로고침")
print("  3. 접촉이력 관리 탭 클릭")
