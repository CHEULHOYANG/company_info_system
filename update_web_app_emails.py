
import sys
import os

target_file = 'g:/company_project_system/web_app.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

smtp_code = """
@app.route('/api/smtp-configs', methods=['GET', 'POST'])
def api_smtp_configs():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session['user_id']
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM smtp_configs WHERE user_id = ?', (user_id,))
        configs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'configs': configs})
    
    else: # POST
        data = request.json
        config_id = data.get('config_id')
        
        if config_id:
            cursor.execute('''
                UPDATE smtp_configs 
                SET config_name = ?, smtp_server = ?, smtp_port = ?, sender_email = ?, sender_password = ?
                WHERE config_id = ? AND user_id = ?
            ''', (data['config_name'], data['smtp_server'], data['smtp_port'], data['sender_email'], data['sender_password'], config_id, user_id))
            message = 'SMTP 설정이 수정되었습니다.'
        else:
            cursor.execute('''
                INSERT INTO smtp_configs (user_id, config_name, smtp_server, smtp_port, sender_email, sender_password)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, data['config_name'], data['smtp_server'], data['smtp_port'], data['sender_email'], data['sender_password']))
            message = 'SMTP 설정이 저장되었습니다.'
            
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': message})

@app.route('/api/send-emails', methods=['POST'])
def api_send_emails():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
        
    data = request.json
    biz_nos = data.get('biz_nos', [])
    subject = data.get('subject', '')
    body = data.get('body', '')
    smtp_config_id = data.get('smtp_config_id')
    group_name = data.get('group_name')
    user_id = session['user_id']
    
    if not biz_nos:
        return jsonify({'success': False, 'message': '발송할 기업을 선택해주세요'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM smtp_configs WHERE config_id = ? AND user_id = ?', (smtp_config_id, user_id))
    config = cursor.fetchone()
    if not config:
        conn.close()
        return jsonify({'success': False, 'message': 'SMTP 설정을 찾을 수 없습니다.'}), 404
        
    placeholders = ','.join(['?'] * len(biz_nos))
    cursor.execute(f'SELECT biz_no, company_name, representative_name, email, phone_number as phone, address FROM Company_Basic WHERE biz_no IN ({placeholders})', biz_nos)
    companies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    sender = EmailSender(
        smtp_server=config['smtp_server'],
        smtp_port=config['smtp_port'],
        sender_email=config['sender_email'],
        sender_password=config['sender_password']
    )
    
    # Run in background
    sender.send_batch_emails(user_id, companies, subject, body, smtp_config_id=smtp_config_id, group_name=group_name)
    return jsonify({'success': True, 'message': '발송이 시작되었습니다.'})

@app.route('/api/batch-status/<batch_id>', methods=['GET'])
def api_batch_status(batch_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM send_batches WHERE batch_id = ? AND user_id = ?', (batch_id, session['user_id']))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({'success': True, 'batch': dict(row)})
    return jsonify({'success': False, 'message': '배치를 찾을 수 없습니다.'}), 404

@app.route('/email_system')
def email_system():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('email_system.html', user_name=session.get('name', '사용자'))
"""

if "if __name__ == '__main__':" in content:
    parts = content.split("if __name__ == '__main__':")
    new_content = parts[0] + smtp_code + "\nif __name__ == '__main__':" + parts[1]
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Successfully added email API routes.')
else:
    print('Could not find injection point.')
