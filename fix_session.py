#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""세션 체크 수정 스크립트"""

with open('web_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# logged_in을 user_id로 변경
content = content.replace(
    "if not session.get('logged_in'):",
    "if 'user_id' not in session:"
)

with open('web_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✔ 세션 체크 수정 완료!")
