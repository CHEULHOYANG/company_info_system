from web_app import app
import unittest

class TestSeminarRegistration(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess['lys_admin_auth'] = True

    def test_register_seminar(self):
        data = {
            'title': 'Test Seminar',
            'date': '2024-12-31',
            'time': '10:00',
            'location': 'Test Location',
            'max_attendees': '30',
            'description': 'Test Description',
            'session_title[]': ['Session 1', 'Session 2'],
            'session_time[]': ['10:00-11:00', '11:00-12:00'],
            'session_instructor[]': ['Instructor 1', 'Instructor 2']
        }
        response = self.client.post('/lys/admin/seminars', data=data, follow_redirects=True)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Response Data: {response.data.decode('utf-8')}")

if __name__ == '__main__':
    unittest.main()
