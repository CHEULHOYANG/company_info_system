#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
web_app.py에 LYS Admin API 추가
"""

# 읽기
with open('web_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 삽입 위치 찾기 (# 아티팩트 이미지 서빙 직전)
insert_idx = None
for i, line in enumerate(lines):
    if '# 아티팩트 이미지 서빙 (중요)' in line:
        insert_idx = i
        break

if not insert_idx:
    print("ERROR: 삽입 위치를 찾을 수 없습니다")
    exit(1)

# 추가할 코드
new_code = '''
# ============================================
# LYS Admin Additional API Routes
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
        data = request.get_json(force=True)
        if not data:
            return jsonify({"success": False, "message": "No data"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 팀원 데이터 업데이트/삽입
        if 'team' in data:
            for idx, member in enumerate(data['team']):
                if member.get('id') and member['id'] != '':
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
                if news_item.get('id') and news_item['id'] != '':
                    # 기존 뉴스 업데이트
                    cursor.execute("""
                        UPDATE BlogPosts
                        SET title=?, category=?, summary=?, link_url=?, publish_date=?
                        WHERE id=?
                    """, (news_item.get('title'), news_item.get('category'), news_item.get('summary'),
                          news_item.get('link_url'), news_item.get('publish_date'), news_item['id']))
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
                if question.get('id') and question['id'] != '':
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
        
        print("✅ LYS 데이터 저장 완료")
        return jsonify({"success": True, "message": "저장되었습니다."})
    except Exception as e:
        print(f"❌ save-all 오류: {e}")
        import traceback
        traceback.print_exc()
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
        print(f"✅ 질문 #{id} 삭제 완료")
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ 질문 삭제 오류: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/lys/question/<int:id>/move', methods=['POST'])
def api_lys_move_question(id):
    """질문 순서 이동"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        data = request.get_json(force=True)
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

'''

# 삽입
lines.insert(insert_idx, new_code)

# 저장
with open('web_app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ API 라우트 추가 완료!")
print("   - /lys/admin (GET)")
print("   - /api/lys/save-all (POST)")
print("   - /api/lys/news/<id> (DELETE)")
print("   - /api/lys/question/<id> (DELETE)")
print("   - /api/lys/question/<id>/move (POST)")
print("   - /api/lys/inquiry/<id> (DELETE)")
print("\n🔄 서버를 재시작해주세요!")
