import sys
from unittest.mock import MagicMock
# Mock psycopg2 module to prevent ImportError when psycopg2 is not installed on the host
sys.modules['psycopg2'] = MagicMock()

import unittest
from unittest.mock import patch
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @patch('db.log_visit')
    def test_hello(self, mock_log_visit):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"message": "Hello, World!"})
        mock_log_visit.assert_called_once()

    @patch('db.get_status')
    def test_status(self, mock_get_status):
        mock_get_status.return_value = "ok"
        response = self.app.get('/status')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.assertIn("timestamp", response.json)
        mock_get_status.assert_called_once()

    @patch('db.get_status')
    def test_status_db_error(self, mock_get_status):
        mock_get_status.return_value = "error"
        response = self.app.get('/status')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "error")
        self.assertIn("timestamp", response.json)
        mock_get_status.assert_called_once()

if __name__ == '__main__':
    unittest.main()
