#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LYS 테이블 추가 및 manage_seminars 수정 스크립트
"""
import sqlite3

# 1. 테이블 생성
conn = sqlite3.connect('company_database.db')
cursor = conn.cursor()

print("📦 누락된 테이블 생성 중...")

# TeamMembers 테이블
cursor.execute('''
    CREATE TABLE IF NOT EXISTS TeamMembers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        position TEXT,
        phone TEXT,
        bio TEXT,
        photo_url TEXT,
        display_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
print("✅ TeamMembers 테이블 생성")

# QuizQuestions 테이블  
cursor.execute('''
    CREATE TABLE IF NOT EXISTS QuizQuestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL,
        display_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
print("✅ QuizQuestions 테이블 생성")

# Inquiries 테이블
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        company TEXT,
        content TEXT,
        checklist TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
print("✅ Inquiries 테이블 생성")

conn.commit()
conn.close()

print("\n✅ 모든 테이블 생성 완료!")

# 2. web_app.py 수정
print("\n📝 web_app.py 수정 중...")

with open('web_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# manage_seminars 함수에서 request.json을 request.get_json()으로 변경
content = content.replace(
    "        if request.method == 'POST':\r\n            data = request.json",
    "        if request.method == 'POST':\r\n            data = request.get_json(force=True)\r\n            if not data:\r\n                print(f'세미나 등록 오류: 데이터 없음')\r\n                return jsonify({\"success\": False, \"message\": \"데이터가 없습니다.\"}), 400"
)

# 에러 로깅 개선
old_except = "    except Exception as e:\r\n        return jsonify({\"success\": False, \"message\": str(e)}), 500"
new_except = "    except Exception as e:\r\n        print(f'세미나 관리 오류: {e}')\r\n        import traceback\r\n        traceback.print_exc()\r\n        return jsonify({\"success\": False, \"message\": str(e)}), 500"

content = content.replace(old_except, new_except, 1)  # manage_seminars 함수만

with open('web_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ web_app.py 수정 완료!")
print("\n🔄 서버를 재시작해주세요!")
