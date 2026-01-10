# This file reconstructs the missing LYS routes section
# Lines to replace in web_app.py from approximately line 6652 onwards

FIXED_CODE = '''
@app.route('/api/seminar/register', methods=['POST'])
def register_seminar_api():
    """세미나 참가 신청 API"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "데이터가 없습니다."}), 400
            
        required_fields = ['seminar_title', 'name', 'phone', 'biz_no']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "message": f"필수 항목이 누락되었습니다: {field}"}), 400
        
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO SeminarRegistrations 
                (seminar_title, name, phone, company_name, position, biz_no)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data['seminar_title'],
                data['name'],
                data['phone'],
                data.get('company_name', ''),
                data.get('position', ''),
                data['biz_no']
            ))
            conn.commit()
            return jsonify({"success": True, "message": "세미나 참가 신청이 완료되었습니다."})
        except Exception as e:
            conn.rollback()
            return jsonify({"success": False, "message": f"데이터베이스 오류: {str(e)}"}), 500
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
'''

print(FIXED_CODE)
