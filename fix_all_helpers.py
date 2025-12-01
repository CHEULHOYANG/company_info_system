#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 모든 접촉이력 관련 함수를 window 객체에 할당

with open(r'g:\company_project_system\templates\detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# formatDateTime 함수 찾아서 window 할당 추가
if '        function formatDateTime(dateTimeStr)' in content:
    content = content.replace(
        '        function formatDateTime(dateTimeStr) {',
        '        window.formatDateTime = function formatDateTime(dateTimeStr) {'
    )
    print("✅ formatDateTime을 window에 할당")

# formatDateTimeForInput 함수 찾아서 window 할당 추가  
if '        function formatDateTimeForInput(dateTimeStr)' in content:
    content = content.replace(
        '        function formatDateTimeForInput(dateTimeStr) {',
        '        window.formatDateTimeForInput = function formatDateTimeForInput(dateTimeStr) {'
    )
    print("✅ formatDateTimeForInput을 window에 할당")

# editContactHistory 함수
if '    async function editContactHistory(historyId)' in content:
    content = content.replace(
        '    async function editContactHistory(historyId) {',
        '    window.editContactHistory = async function editContactHistory(historyId) {'
    )
    print("✅ editContactHistory를 window에 할당")

# deleteContactHistory 함수
if '    async function deleteContactHistory(historyId)' in content:
    content = content.replace(
        '    async function deleteContactHistory(historyId) {',
        '    window.deleteContactHistory = async function deleteContactHistory(historyId) {'
    )
    print("✅ deleteContactHistory를 window에 할당")

# 저장
with open(r'g:\company_project_system\templates\detail.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ 모든 헬퍼 함수를 window에 할당 완료!")
