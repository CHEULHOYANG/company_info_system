import os

file_path = 'web_app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the split points
start_marker = "                data['biz_no']"
end_marker = "    start_date = request.args.get('start_date', '').strip()"

start_index = -1
end_index = -1

for i, line in enumerate(lines):
    if start_marker in line:
        start_index = i
    if end_marker in line:
        end_index = i

if start_index == -1 or end_index == -1:
    print(f"Error: Markers not found. Start: {start_index}, End: {end_index}")
    exit(1)

print(f"Found markers at {start_index} and {end_index}")

# Construct the new content
new_content = """            ))
            conn.commit()
            return jsonify({"success": True, "message": "세미나 참가 신청이 완료되었습니다."})
        except Exception as e:
            conn.rollback()
            return jsonify({"success": False, "message": f"데이터베이스 오류: {str(e)}"}), 500
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# --- LYS ADMIN ROUTES START ---
@app.route('/lys/admin/seminars', methods=['GET', 'POST'])
def lys_admin_seminars():
    \"\"\"세미나 관리 페이지\"\"\"
    if not session.get('lys_admin_auth'):
        return redirect('/lys/admin')
        
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            # JSON 요청 처리 (lys_admin.html에서 오는 경우)
            if request.is_json:
                data = request.json
                title = data.get('title')
                date = data.get('date')
                time = data.get('time')
                location = data.get('location')
                max_attendees = data.get('max_attendees', '')
                description = data.get('description', '')
                instructor = data.get('instructor', '')
                link_url = data.get('link_url', '')
                
                # 날짜 포맷 변환 (YYYY.MM.DD -> YYYY-MM-DD)
                if date and '.' in date:
                    date = date.replace('.', '-')

                cursor = conn.execute('''
                    INSERT INTO Seminars (title, date, time, location, description, max_attendees, instructor, link_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title, date, time, location, description, max_attendees, instructor, link_url))
                seminar_id = cursor.lastrowid
                
                # 세션 처리 (JSON에 세션 정보가 있다면)
                if 'sessions' in data:
                    for sem_session in data['sessions']:
                        conn.execute('''
                            INSERT INTO SeminarSessions (seminar_id, session_time, title, instructor)
                            VALUES (?, ?, ?, ?)
                        ''', (seminar_id, sem_session.get('time'), sem_session.get('title'), sem_session.get('instructor')))
                
                conn.commit()
                return jsonify({'success': True})

            # Form 요청 처리 (lys_admin_seminars.html에서 오는 경우)
            else:
                title = request.form.get('title')
                date = request.form.get('date')
                time = request.form.get('time')
                location = request.form.get('location')
                max_attendees = request.form.get('max_attendees', '')
                description = request.form.get('description', '')
                instructor = request.form.get('instructor', '')
                
                # 이미지 업로드 처리
                image_url = None
                if 'image_file' in request.files:
                    file = request.files['image_file']
                    if file and file.filename != '':
                        import uuid
                        filename = f"seminar_{int(time.time())}_{file.filename}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        image_url = f"/uploads/{filename}"

                cursor = conn.execute('''
                    INSERT INTO Seminars (title, date, time, location, description, max_attendees, instructor, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title, date, time, location, description, max_attendees, instructor, image_url))
                seminar_id = cursor.lastrowid
                
                # 세션 추가
                sessions = request.form.getlist('session_title[]')
                session_times = request.form.getlist('session_time[]')
                instructors = request.form.getlist('session_instructor[]')
                
                for i in range(len(sessions)):
                    if sessions[i]:
                        conn.execute('''
                            INSERT INTO SeminarSessions (seminar_id, session_time, title, instructor)
                            VALUES (?, ?, ?, ?)
                        ''', (seminar_id, session_times[i], sessions[i], instructors[i]))
                
                conn.commit()
                return redirect('/lys/admin/seminars')
            
        seminars = conn.execute('SELECT * FROM Seminars ORDER BY date DESC').fetchall()
        return render_template('lys_admin_seminars.html', seminars=[dict(row) for row in seminars])
    except Exception as e:
        print(f"세미나 관리 오류: {e}")
        return f"오류가 발생했습니다: {str(e)}", 500
    finally:
        conn.close()

@app.route('/lys/admin/registrations')
def lys_admin_registrations():
    \"\"\"세미나 신청자 관리 페이지\"\"\"
    if not session.get('lys_admin_auth'):
        return redirect('/lys/admin')
        
    conn = get_db_connection()
    try:
        registrations = conn.execute('''
            SELECT * FROM SeminarRegistrations ORDER BY created_at DESC
        ''').fetchall()
        return render_template('lys_admin_registrations.html', registrations=[dict(row) for row in registrations])
    finally:
        conn.close()

@app.route('/lys/admin/registrations/<int:id>/delete', methods=['POST'])
def lys_admin_delete_registration(id):
    if not session.get('lys_admin_auth'): return redirect('/lys/admin')
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM SeminarRegistrations WHERE id = ?', (id,))
        conn.commit()
    finally:
        conn.close()
    return redirect('/lys/admin/registrations')

@app.route('/lys/admin/questions', methods=['GET', 'POST'])
def lys_admin_questions():
    \"\"\"진단 질문 관리 페이지\"\"\"
    if not session.get('lys_admin_auth'):
        return redirect('/lys/admin')
        
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            question_text = request.form['question']
            q_type = request.form['type']
            # Get next display order
            max_order = conn.execute('SELECT MAX(display_order) FROM ys_questions').fetchone()[0] or 0
            
            conn.execute('''
                INSERT INTO ys_questions (question_text, type, display_order, is_active)
                VALUES (?, ?, ?, 1)
            ''', (question_text, q_type, max_order + 1))
            conn.commit()
            return redirect('/lys/admin/questions')
            
        questions = conn.execute('SELECT * FROM ys_questions ORDER BY display_order ASC').fetchall()
        return render_template('lys_admin_questions.html', questions=[dict(row) for row in questions])
    finally:
        conn.close()

@app.route('/lys/admin/questions/reorder', methods=['POST'])
def lys_admin_reorder_questions():
    if not session.get('lys_admin_auth'): return jsonify({'success': False}), 403
    try:
        order_data = request.json['order'] # List of IDs in new order
        conn = get_db_connection()
        for index, q_id in enumerate(order_data):
            conn.execute('UPDATE ys_questions SET display_order = ? WHERE id = ?', (index + 1, q_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/lys/admin/questions/<int:id>/delete', methods=['POST'])
def lys_admin_delete_question(id):
    if not session.get('lys_admin_auth'): return redirect('/lys/admin')
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM ys_questions WHERE id = ?', (id,))
        conn.commit()
    finally:
        conn.close()
    return redirect('/lys/admin/questions')
# --- LYS ADMIN ROUTES END ---

@app.route('/lys/inquiry')
def lys_inquiry():
    \"\"\"YS Honers 상담신청 페이지\"\"\"
    conn = get_db_connection()
    try:
        questions = conn.execute('''
            SELECT * FROM ys_questions WHERE is_active = 1 ORDER BY display_order
        ''').fetchall()
        return render_template('lys_inquiry.html', questions=[dict(q) for q in questions])
    except Exception as e:
        print(f"질문 조회 오류: {e}")
        return render_template('lys_inquiry.html', questions=[])
    finally:
        conn.close()

@app.route('/lys/admin', methods=['GET', 'POST'])
def lys_admin():
    \"\"\"YS Honers 관리자 페이지\"\"\"
    # 비밀번호 인증
    ADMIN_PASSWORD = 'admin1234!'
    
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['lys_admin_auth'] = True
        else:
            return render_template('lys_admin_login.html', error='비밀번호가 올바르지 않습니다.')
    
    if not session.get('lys_admin_auth'):
        return render_template('lys_admin_login.html')

    conn = get_db_connection()
    try:
        # 팀원 목록 조회
        team_members = conn.execute('SELECT * FROM ys_team_members ORDER BY id').fetchall()
        
        # 뉴스 목록 조회
        news_items = conn.execute('SELECT * FROM ys_news ORDER BY publish_date DESC').fetchall()
        
        # 상담 문의 목록 조회
        inquiries = conn.execute('SELECT * FROM ys_inquiries ORDER BY created_at DESC').fetchall()
        
        # 퀴즈 질문 조회
        quiz_questions = conn.execute('SELECT * FROM ys_questions ORDER BY id').fetchall()
        
        # 세미나 목록 조회
        seminars = conn.execute('SELECT * FROM Seminars ORDER BY date DESC').fetchall()
        
        # 세미나 신청자 목록 조회
        seminar_registrations = conn.execute('SELECT * FROM SeminarRegistrations ORDER BY created_at DESC').fetchall()
        
        # 상담 문의 데이터 가공 (체크리스트 파싱)
        inquiries_data = []
        import json
        for row in inquiries:
            item = dict(row)
            if item.get('checklist'):
                try:
                    item['checklist'] = json.loads(item['checklist'])
                except:
                    item['checklist'] = []
            inquiries_data.append(item)
            
        return render_template('lys_admin.html', 
                             team_members=[dict(row) for row in team_members],
                             news_items=[dict(row) for row in news_items],
                             inquiries=inquiries_data,
                             quiz_questions=[dict(row) for row in quiz_questions],
                             seminars=[dict(row) for row in seminars],
                             seminar_registrations=[dict(row) for row in seminar_registrations])
    finally:
        conn.close()

@app.route('/api/lys/news/<int:news_id>', methods=['DELETE'])
def api_lys_news_delete(news_id):
    \"\"\"뉴스 삭제 API\"\"\"
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM ys_news WHERE id=?', (news_id,))
        conn.commit()
        return jsonify({'success': True, 'message': '뉴스가 삭제되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/lys/inquiry', methods=['GET', 'POST'])
def api_lys_inquiry():
    \"\"\"상담 문의 API\"\"\"
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            inquiries = conn.execute('''
                SELECT * FROM ys_inquiries ORDER BY created_at DESC
            ''').fetchall()
            return jsonify({'success': True, 'data': [dict(row) for row in inquiries]})
        
        elif request.method == 'POST':
            data = request.get_json()
            import json
            checklist = json.dumps(data.get('checklist', []), ensure_ascii=False) if data.get('checklist') else None
            
            conn.execute('''
                INSERT INTO ys_inquiries (name, company, phone, checklist, content, status)
                VALUES (?, ?, ?, ?, ?, 'new')
            ''', (data.get('name'), data.get('company'), data.get('phone'),
                  checklist, data.get('content')))
            conn.commit()
            return jsonify({'success': True, 'message': '상담 문의가 등록되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/lys/inquiry/<int:inquiry_id>', methods=['DELETE'])
def api_lys_inquiry_delete(inquiry_id):
    \"\"\"상담 문의 삭제 API\"\"\"
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM ys_inquiries WHERE id=?', (inquiry_id,))
        conn.commit()
        return jsonify({'success': True, 'message': '문의가 삭제되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/lys/upload', methods=['POST'])
def api_lys_upload():
    \"\"\"이미지 업로드 API\"\"\"
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '파일이 선택되지 않았습니다.'}), 400
        
        # 파일 저장
        import uuid
        filename = f"{int(time.time() * 1000)}-{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True, 
            'message': '파일이 업로드되었습니다.',
            'url': f'/uploads/{filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    \"\"\"업로드된 파일 제공\"\"\"
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/lys/save-all', methods=['POST'])
def api_lys_save_all():
    \"\"\"전체 데이터 저장 API (팀원+뉴스)\"\"\"
    conn = get_db_connection()
    try:
        data = request.get_json()
        
        # 팀원 정보 업데이트
        if 'team' in data:
            for member in data['team']:
                if member.get('id'):
                    conn.execute('''
                        UPDATE ys_team_members 
                        SET name=?, position=?, phone=?, bio=?, photo_url=?, updated_at=CURRENT_TIMESTAMP
                        WHERE id=?
                    ''', (member.get('name'), member.get('position'), member.get('phone'),
                          member.get('bio'), member.get('photo_url'), member.get('id')))
            conn.commit()
            return jsonify({'success': True})
    finally:
        conn.close()

@app.route('/api/lys/inquiry/mark-read', methods=['POST'])
def api_lys_inquiry_mark_read():
    \"\"\"모든 상담 문의를 확인함으로 표시\"\"\"
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE ys_inquiries SET status = 'read' WHERE status = 'new' OR status IS NULL
        ''')
        conn.commit()
        return jsonify({'success': True, 'message': '모든 문의가 확인 처리되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# --- 개인사업자(전단계) 관리 라우트 ---

@app.route('/individual_businesses')
def individual_business_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 검색 파라미터 가져오기
    company_name = request.args.get('company_name', '').strip()
    business_number = request.args.get('business_number', '').strip()
    address = request.args.get('address', '').strip()
    industry_type = request.args.get('industry_type', '').strip()
"""

# Reconstruct the file
final_lines = lines[:start_index+1] + [new_content + "\n"] + lines[end_index:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print("File patched successfully.")
