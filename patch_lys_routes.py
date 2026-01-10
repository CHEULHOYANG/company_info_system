#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
web_app.py에 LYS Admin 라우트를 추가하는 스크립트
"""

def patch_web_app():
    # web_app.py 읽기
    with open('web_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. init_lys_tables 함수에 테이블 추가
    init_lys_insert = '''
        # 팀원 테이블
        conn.execute('''
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
        
        # 진단 질문 테이블
        conn.execute('''
    CREATE TABLE IF NOT EXISTS QuizQuestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL,
        display_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
        
        # 상담 문의 테이블
        conn.execute('''
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
        '''
    
    # init_lys_tables에서 conn.commit() 직전에 추가
    content = content.replace(
        "        conn.commit()\r\n    except Exception as e:\r\n        print(f\"Error initializing LYS tables: {e}\")",
        init_lys_insert + "\r\n        conn.commit()\r\n    except Exception as e:\r\n        print(f\"Error initializing LYS tables: {e}\")"
    )
    
    # 2. 라우트 추가 - manage_blog 함수 다음에 추가
    routes_to_add = '''

# ============================================
# LYS Admin Page and Additional API Routes  
# ============================================

@app.route('/lys/admin')
def lys_admin():
    """LYS Admin 페이지"""
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 팀원 데이터
        cursor.execute("SELECT * FROM TeamMembers ORDER BY display_order")
        team_members = [dict(row) for row in cursor.fetchall()]
        
        # 뉴스/블로그 데이터  
        cursor.execute("SELECT * FROM BlogPosts ORDER BY created_at DESC")
        news_items = [dict(row) for row in cursor.fetchall()]
        
        # 상담 문의 데이터
        cursor.execute("SELECT * FROM Inquiries ORDER BY created_at DESC")
        inquiries = []
        for row in cursor.fetchall():
            inq = dict(row)
            # checklist JSON 파싱
            try:
                import json
                if inq.get('checklist'):
                    inq['checklist'] = json.loads(inq['checklist'])
                else:
                    inq['checklist'] = []
            except:
                inq['checklist'] = []
            inquiries.append(inq)
        
        # 진단 질문 데이터
        cursor.execute("SELECT * FROM QuizQuestions ORDER BY display_order")
        quiz_questions = [dict(row) for row in cursor.fetchall()]
        
        # 세미나 데이터
        cursor.execute("SELECT * FROM Seminars ORDER BY date DESC")
        seminars = [dict(row) for row in cursor.fetchall()]
        
        # 세미나 신청자 데이터
        cursor.execute("SELECT * FROM SeminarRegistrations ORDER BY created_at DESC")
        seminar_registrations = [dict(row) for row in cursor.fetchall()]
        
        return render_template('lys_admin.html', 
                             team_members=team_members,
                             news_items=news_items,
                             inquiries=inquiries,
                             quiz_questions=quiz_questions,
                             seminars=seminars,
                             seminar_registrations=seminar_registrations)
    except Exception as e:
        print(f"Error loading LYS admin: {e}")
        return f"Error: {str(e)}", 500
    finally:
        conn.close()

@app.route('/api/lys/save-all', methods=['POST'])
def api_lys_save_all():
    """팀원, 뉴스, 질문 데이터 일괄 저장"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 팀원 데이터 업데이트/삽입
        if 'team' in data:
            for idx, member in enumerate(data['team']):
                if member.get('id'):
                    # 기존 멤버 업데이트
                    cursor.execute("""
                        UPDATE TeamMembers 
                        SET name=?, position=?, phone=?, bio=?, photo_url=?, display_order=?
                        WHERE id=?
                    """, (member.get('name'), member.get('position'), member.get('phone'),
                          member.get('bio'), member.get('photo_url'), idx, member['id']))
                else:
                    # 신규 멤버 삽입
                    cursor.execute("""
                        INSERT INTO TeamMembers (name, position, phone, bio, photo_url, display_order)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (member.get('name'), member.get('position'), member.get('phone'),
                          member.get('bio'), member.get('photo_url'), idx))
        
        # 뉴스 데이터 업데이트/삽입
        if 'news' in data:
            for news_item in data['news']:
               if news_item.get('id'):
                    # 기존 뉴스 업데이트
                    cursor.execute("""
                        UPDATE BlogPosts
                        SET title=?, category=?, summary=?, link_url=?, publish_date=?
                        WHERE id=?
                    """, (news_item.get('title'), news_item.get('category'), news_item.get('summary'),
                          news_item.get('link_url'), news_item.get('publish_date'), news_item[' id']))
                else:
                    # 신규 뉴스 삽입
                    cursor.execute("""
                        INSERT INTO BlogPosts (title, category, summary, link_url, publish_date)
                        VALUES (?, ?, ?, ?, ?)
                    """, (news_item.get('title'), news_item.get('category'), news_item.get('summary'),
                          news_item.get('link_url'), news_item.get('publish_date')))
        
        # 질문 데이터 업데이트/삽입
        if 'questions' in data:
            for question in data['questions']:
                if question.get('id'):
                    # 기존 질문 업데이트
                    cursor.execute("""
                        UPDATE QuizQuestions
                        SET question_text=?, display_order=?
                        WHERE id=?
                    """, (question.get('question_text'), question.get('display_order'), question['id']))
                else:
                    # 신규 질문 삽입
                    cursor.execute("""
                        INSERT INTO QuizQuestions (question_text, display_order)
                        VALUES (?, ?)
                    """, (question.get('question_text'), question.get('display_order')))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "저장되었습니다."})
    except Exception as e:
        print(f"Error in save-all: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/lys/news/<int:id>', methods=['DELETE'])
def api_lys_delete_news(id):
    """뉴스 삭제"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM BlogPosts WHERE id=?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/lys/question/<int:id>', methods=['DELETE'])
def api_lys_delete_question(id):
    """질문 삭제"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM QuizQuestions WHERE id=?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/lys/question/<int:id>/move', methods=['POST'])
def api_lys_move_question(id):
    """질문 순서 이동"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        data = request.json
        direction = data.get('direction')  # 'up' or 'down'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 현재 질문의 order 가져오기
        cursor.execute("SELECT display_order FROM QuizQuestions WHERE id=?", (id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Question not found"}), 404
        
        current_order = row[0] if row[0] is not None else 0
        
        if direction == 'up':
            # 이전 질문과 order 교체
            cursor.execute("""
                UPDATE QuizQuestions 
                SET display_order = display_order + 1 
                WHERE display_order = ?
            """, (current_order - 1,))
            cursor.execute("UPDATE QuizQuestions SET display_order = ? WHERE id = ?", 
                         (current_order - 1, id))
        elif direction == 'down':
            # 다음 질문과 order 교체
            cursor.execute("""
                UPDATE QuizQuestions 
                SET display_order = display_order - 1 
                WHERE display_order = ?
            """, (current_order + 1,))
            cursor.execute("UPDATE QuizQuestions SET display_order = ? WHERE id = ?", 
                         (current_order + 1, id))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/lys/inquiry/<int:id>', methods=['DELETE'])
def api_lys_delete_inquiry(id):
    """문의 삭제"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM Inquiries WHERE id=?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/lys/upload', methods=['POST'])
def api_lys_upload():
    """이미지 업로드"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
    
    try:
        # 파일 저장
        import os
        from werkzeug.utils import secure_filename
        import time
        
        filename = secure_filename(file.filename)
        timestamp = int(time.time() * 1000)
        new_filename = f"{timestamp}_{filename}"
        upload_path = os.path.join(app.root_path, 'uploads', new_filename)
        
        # uploads 디렉토리 생성
        os.makedirs(os.path.join(app.root_path, 'uploads'), exist_ok=True)
        
        file.save(upload_path)
        
        # URL 반환
        url = f"/uploads/{new_filename}"
        return jsonify({"success": True, "url": url})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

'''
    
    # manage_blog 함수 다음에 추가 (conn.close() 다음)
    content = content.replace(
        "        conn.close()\r\n\r\n# 아티팩트 이미지 서빙 (중요)",
        "        conn.close()\r\n" + routes_to_add + "\r\n# 아티팩트 이미지 서빙 (중요)"
    )
    
    # 백업 생성
    with open('web_app.py.backup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 파일 저장
    with open('web_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✔ web_app.py 패치 완료!")
    print("✔ 백업 파일: web_app.py.backup")

if __name__ == '__main__':
    try:
        patch_web_app()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
