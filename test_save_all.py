import requests
import json

# Adjust port if necessary, assuming 5000 based on standard Flask
BASE_URL = 'http://127.0.0.1:5000'
LOGIN_URL = f'{BASE_URL}/lys/admin'
SAVE_URL = f'{BASE_URL}/api/lys/save-all'

def test_save_all():
    session = requests.Session()
    
    # 1. Login
    print("Attempting login...")
    login_payload = {'password': 'admin1234!'}
    try:
        response = session.post(LOGIN_URL, data=login_payload)
        if response.status_code == 200 and '관리자 페이지' in response.text:
            print("Login successful.")
        else:
            # It might perform a redirect or render the template directly. 
            # If render template, status is 200.
            print(f"Login response status: {response.status_code}")
            # Verify auth cookie is set
            if 'session' in session.cookies:
                print("Session cookie found.")
            else:
                print("Login failed (no session cookie).")
                return
    except Exception as e:
        print(f"Could not connect to server: {e}")
        return

    # 2. Prepare Data (Minimal Payload)
    # We will try to update just one field to verification
    payload = {
        "team": [
            {
                "id": 1, 
                "name": "양철호", 
                "position": "(수석팀장) Senior Team Leader", 
                "phone": "010-0000-0000",
                "bio": "Test Save Update", 
                "photo_url": ""
            }
        ],
        "news": [],
        "seminars": []
    }

    # 3. Send Save Request
    print("Sending save-all request...")
    try:
        response = session.post(SAVE_URL, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("Save-all endpoint verified successfully.")
        else:
            print("Save-all endpoint failed.")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_save_all()
