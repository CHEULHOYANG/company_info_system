import requests

session = requests.Session()
login_url = 'http://localhost:5000/lys/admin'
password = 'admin1234!'

try:
    # Login
    response = session.post(login_url, data={'password': password})
    
    print(f"Status Code: {response.status_code}")

    if '세미나 관리' in response.text:
        print("Login Successful. Found '세미나 관리'.")
    else:
        print("Login Failed or '세미나 관리' not found.")
        # print(response.text[:500])

    # Check for specific tabs content
    if 'id="seminars"' in response.text or 'seminar-management' in response.text:
        print("Found Seminars Tab Content.")
    else:
        print("Seminars Tab Content NOT found.")

    if 'id="applicants"' in response.text or 'seminar-applicants' in response.text:
        print("Found Applicants Tab Content.")
    else:
        print("Applicants Tab Content NOT found.")
        
except Exception as e:
    print(f"Error: {e}")
