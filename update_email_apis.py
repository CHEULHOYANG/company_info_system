
import os
import sys

target_file = 'g:/company_project_system/web_app.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

email_api_code = """
# --- EMAIL SYSTEM ENHANCED APIs ---

@app.route('/api/email_groups', methods=['GET'])
def api_email_groups():
    if 'user_id' not in session: return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    from email_service import get_email_groups
    groups = get_email_groups()
    return jsonify({'success': True, 'groups': groups})

@app.route('/api/email_batch_send', methods=['POST'])
def api_email_batch_send():
    if 'user_id' not in session: return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.json
    group_id = data.get('group_id')
    smtp_config_id = data.get('smtp_config_id')
    subject = data.get('subject')
    body = data.get('body')
    user_id = session['user_id']
    
    from email_service import EmailSender, get_group_members
    
    # 1. SMTP Config 가져오기 (이미 구현된 smtp_configs 테이블 활용)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM smtp_configs WHERE config_id = ? AND user_id = ?', (smtp_config_id, user_id))
    config = cursor.fetchone()
    
    if not config:
        conn.close()
        return jsonify({'success': False, 'message': 'SMTP 설정을 찾을 수 없습니다.'})

    # 2. 그룹 멤버 가져오기
    companies = get_group_members(group_id)
    if not companies:
        conn.close()
        return jsonify({'success': False, 'message': '그룹에 발송 가능한 기업이 없습니다.'})
        
    cursor.execute('SELECT name FROM email_groups WHERE id = ?', (group_id,))
    group_name = cursor.fetchone()['name']
    conn.close()

    sender = EmailSender(
        smtp_server=config['smtp_server'],
        smtp_port=config['smtp_port'],
        sender_email=config['sender_email'],
        sender_password=config['sender_password']
    )
    
    res = sender.send_batch_emails(user_id, companies, subject, body, smtp_config_id=smtp_config_id, group_name=group_name)
    return jsonify({'success': True, 'batch_id': res['batch_id'], 'total': res['total']})

@app.route('/api/batch_status/<batch_id>', methods=['GET'])
def api_batch_status_enhanced(batch_id):
    if 'user_id' not in session: return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM send_batches WHERE batch_id = ?', (batch_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({'success': True, 'batch': dict(row)})
    return jsonify({'success': False, 'message': 'Batch not found'})

@app.route('/email_system')
def email_system_page():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('email_system.html', user_name=session.get('name', '사용자'))
"""

# Injection logic: Add before app.run or at the end
if "if __name__ == '__main__':" in content:
    parts = content.split("if __name__ == '__main__':")
    # Replace old routes if they exist to prevent duplication
    new_content = parts[0] + email_api_code + "\\n\\nif __name__ == '__main__':" + parts[1]
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Web App API updated.')
else:
    print('Could not find injection point in web_app.py')
