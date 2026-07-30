# General AI Fluency - Prompt Ladder Deliverable

## 🎯 Final Reusable Prompt (Cleaned Up for Anyone to Use)

```text
Act as a Senior Python Backend Engineer. Your task is to write a single-file Flask RESTful API server for task management connected to a SQLite database.

Requirements:
1. Database Schema: SQLite database `tasks.db` with table `tasks` containing columns: `id` (INTEGER PRIMARY KEY AUTOINCREMENT), `title` (TEXT NOT NULL), and `done` (BOOLEAN NOT NULL DEFAULT 0).
2. Endpoints:
   - GET /tasks -> List all tasks (200 OK)
   - GET /tasks/<id> -> Fetch single task (200 OK, 404 Not Found)
   - POST /tasks -> Create task with body `{"title": str, "done": bool}` (201 Created, 400 Bad Request if missing title)
   - PUT /tasks/<id> -> Update task by ID (200 OK, 404 Not Found, 400 Bad Request)
   - DELETE /tasks/<id> -> Delete task by ID (200 OK, 404 Not Found)
3. Technical Constraints:
   - Use standard `sqlite3` library with parameterized SQL queries (`?`) to prevent SQL injection.
   - Do NOT use ORMs like SQLAlchemy.
   - Return clean JSON payloads and proper HTTP status codes.
4. Output Requirements:
   - Output clean, complete, runnable Python code (`app.py`).
   - Include a `unittest` test suite at the bottom of the file covering all endpoints.
```

---

## 🪜 The Prompt Ladder (Baseline + 5 Iterative Layers)

### Run 0: Weak Baseline Prompt
* **Prompt:**
  > `"Write backend code for a task manager"`

* **Output Excerpt:**
  ```python
  class TaskManager:
      def __init__(self):
          self.tasks = []
      def add_task(self, task):
          self.tasks.append(task)
  ```

---

### Run 1: Layer 1 — Clearer Goal
* **Layer Added:** `Clearer Goal` (Switching from generic code to a web HTTP API service).
* **Prompt:**
  > `"Write a Flask REST API for a task manager that returns JSON responses for task CRUD operations."`

* **Output Excerpt:**
  ```python
  from flask import Flask, jsonify, request
  app = Flask(__name__)
  tasks = []

  @app.route('/tasks', methods=['GET'])
  def get_tasks():
      return jsonify(tasks)
  ```

* **Four Notes:**
  1. **What changed in prompt:** Specified Flask REST API and JSON endpoints instead of generic Python functions.
  2. **What actually improved in output:** The output shifted from a simple local array class to an HTTP server with routing decorator functions (`@app.route`).
  3. **What still failed:** The data is stored in a temporary Python list in memory; restarting the server wipes all tasks.
  4. **What I would try next:** Pass real database context so it uses persistent storage.

---

### Run 2: Layer 2 — Real Context
* **Layer Added:** `Real Context` (Providing exact SQLite database file and schema details).
* **Prompt:**
  > `"Write a Flask REST API for a task manager using SQLite database 'tasks.db' with table 'tasks(id INTEGER PRIMARY KEY, title TEXT, done BOOLEAN)'."`

* **Output Excerpt:**
  ```python
  import sqlite3
  from flask import Flask, jsonify, request

  @app.route('/tasks', methods=['GET'])
  def get_tasks():
      conn = sqlite3.connect('tasks.db')
      c = conn.cursor()
      c.execute("SELECT * FROM tasks")
      rows = c.fetchall()
      return jsonify(rows)
  ```

* **Four Notes:**
  1. **What changed in prompt:** Provided exact database name, database type (SQLite), and table column definitions.
  2. **What actually improved in output:** The code replaced in-memory lists with `sqlite3` connection calls and `SELECT` SQL queries.
  3. **What still failed:** Returns tuple rows like `[1, "Buy milk", 0]` instead of formatted JSON dictionaries like `{"id": 1, "title": "Buy milk", "done": false}`.
  4. **What I would try next:** Add explicit formatting and error constraint rules.

---

### Run 3: Layer 3 — Constraints & Error Contracts
* **Layer Added:** `Constraints` (Enforcing parametrized queries, JSON dictionary structure, and HTTP status codes).
* **Prompt:**
  > `"Write a Flask REST API for SQLite table tasks(id INTEGER PRIMARY KEY, title TEXT, done BOOLEAN). Use parameterized SQL queries only. Return JSON dictionaries like {"id": 1, "title": "...", "done": false}. Return HTTP 400 for missing input fields and HTTP 404 when an ID is not found."`

* **Output Excerpt:**
  ```python
  @app.route('/tasks/<int:task_id>', methods=['GET'])
  def get_task(task_id):
      conn = sqlite3.connect('tasks.db')
      conn.row_factory = sqlite3.Row
      c = conn.cursor()
      c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
      row = c.fetchone()
      if not row:
          return jsonify({"error": "Task not found"}), 404
      return jsonify(dict(row)), 200
  ```

* **Four Notes:**
  1. **What changed in prompt:** Enforced parametrized SQL queries (`?`), dictionary mapping via `row_factory`, and HTTP status codes (`400`, `404`, `200`).
  2. **What actually improved in output:** API outputs are now key-value JSON objects and clients get proper 404 status codes on invalid IDs.
  3. **What still failed:** The generated output included lengthy markdown paragraphs explaining SQL basics that I didn't need.
  4. **What I would try next:** Add a Quality Criteria / Style Constraint layer to clean up formatting.

---

### Run 4: Layer 4 — Quality Criteria & Formatting Constraints ⚠️ *(Honest "Made It Worse" Moment)*
* **Layer Added:** `Quality Criteria / Extreme Constraints` (Attempting to enforce line-by-line inline comments for readability).
* **Prompt:**
  > `"Write a Flask REST API for SQLite tasks table with parameterized queries, 400/404 status codes, and dictionary JSON payloads. Add detailed inline comments explaining every single line of Python and SQL code for maximum code quality."`

* **Output Excerpt:**
  ```python
  # Import the jsonify function from flask to convert dict to json
  from flask import jsonify 
  # Execute a SQL query to select all tasks from the table
  c.execute("SELECT * FROM tasks") # SQL query execution
  # Fetch all results from the cursor object
  rows = c.fetchall() # Fetching rows
  ```

* **Four Notes:**
  1. **What changed in prompt:** Added a constraint requesting inline comments on every single line of code.
  2. **What actually improved in output:** None.
  3. **What still failed (THIS MADE IT WORSE):** The code output became extremely cluttered, repetitive, and unreadable. Trivial lines like `import jsonify` had redundant commentary that slowed down code scanning.
  4. **What I would try next:** Remove the inline comment constraint and instead add automated verification tests (unit tests).

---

### Run 5: Layer 5 — Verification Requirements
* **Layer Added:** `Verification Requirements` (Requiring an executable `unittest` suite at the bottom of the file).
* **Prompt:**
  > `"Write a single-file Flask REST API for SQLite tasks(id, title, done) with parameterized queries, clean JSON payloads, 400/404 handling. Remove excessive comments. Include a runnable unittest test suite at the bottom of the file verifying GET, POST, PUT, and DELETE endpoints."`

* **Output Excerpt:**
  ```python
  import unittest

  class TaskApiTestCase(unittest.TestCase):
      def setUp(self):
          self.app = app.test_client()
          # setup in-memory test db...

      def test_get_tasks(self):
          res = self.app.get('/tasks')
          self.assertEqual(res.status_code, 200)

  if __name__ == '__main__':
      unittest.main()
  ```

* **Four Notes:**
  1. **What changed in prompt:** Demanded removal of excessive comments and added a requirement for a runnable `unittest` test suite.
  2. **What actually improved in output:** The script became self-verifying. Running `python app.py` executes unit tests against all REST endpoints automatically to confirm functionality.
  3. **What still failed:** Nothing—the output is a production-ready, fully tested single-file Flask API.
  4. **What I would try next:** Clean up into a final reusable template prompt.
