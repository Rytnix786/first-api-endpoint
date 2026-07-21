import unittest
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_hello(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"message": "Hello, World!"})

    def test_status(self):
        response = self.app.get('/status')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.assertIn("timestamp", response.json)

    def test_db_initialization_and_seeding(self):
        import db
        db.init_db()
        tasks = db.get_all_tasks()
        self.assertGreaterEqual(len(tasks), 3)

    def test_get_all_tasks(self):
        response = self.app.get('/tasks')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        self.assertGreaterEqual(len(response.json), 3)

    def test_get_single_task_success(self):
        response = self.app.get('/tasks/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['id'], 1)
        self.assertIn('title', response.json)
        self.assertIn('done', response.json)

    def test_get_single_task_not_found(self):
        response = self.app.get('/tasks/9999')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {"error": "Task not found"})

    def test_create_task_success(self):
        payload = {"title": "Test persistent creation", "done": False}
        response = self.app.post('/tasks', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['title'], "Test persistent creation")
        self.assertFalse(response.json['done'])
        self.assertIn('id', response.json)

    def test_create_task_missing_title(self):
        payload = {"title": "  "}
        response = self.app.post('/tasks', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "Title is required"})

    def test_update_task_success(self):
        payload = {"title": "Updated Task Title", "done": True}
        response = self.app.put('/tasks/1', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['title'], "Updated Task Title")
        self.assertTrue(response.json['done'])

    def test_update_task_not_found(self):
        payload = {"title": "Non existent"}
        response = self.app.put('/tasks/9999', json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {"error": "Task not found"})

    def test_delete_task_success(self):
        # Create a task to delete
        create_res = self.app.post('/tasks', json={"title": "To be deleted"})
        task_id = create_res.json['id']

        delete_res = self.app.delete(f'/tasks/{task_id}')
        self.assertEqual(delete_res.status_code, 200)
        self.assertEqual(delete_res.json, {"message": "Task deleted successfully"})

        # Confirm 404 on GET
        get_res = self.app.get(f'/tasks/{task_id}')
        self.assertEqual(get_res.status_code, 404)

    def test_delete_task_not_found(self):
        response = self.app.delete('/tasks/9999')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {"error": "Task not found"})

if __name__ == '__main__':
    unittest.main()
