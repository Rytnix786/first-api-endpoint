# FL-02: Prompt Engineering Iteration Log & Cross-Model Comparison

## 📋 Task Overview
- **Task Selected from Repo:** Building a containerized Flask REST API with PostgreSQL database integration and Redis caching for health status and visit tracking (`Task2-w2`).
- **Goal:** Generate a production-grade Python backend script (`app.py`) with database connections, Redis ping status, error handling, and parameterized query execution.

---

## 🪜 Prompt Iterations (Naive Baseline + 5 Named Technique Versions)

### Version 0: Naive One-Line Baseline Prompt
* **Technique:** None (Naive Baseline)
* **Prompt:**
  > `"Write a Flask app with Postgres and Redis"`

* **Output Excerpt:**
  ```python
  from flask import Flask
  import psycopg2
  import redis

  app = Flask(__name__)
  db = psycopg2.connect("dbname=test user=postgres")
  r = redis.Redis()

  @app.route('/')
  def index():
      return "Hello"
  ```

* **Iteration Note (What Changed & Why):**
  - *Observed Output Difference:* The naive output is overly simplistic, hardcodes database credentials, creates unhandled connection drops, and has no REST endpoints, health checks, or JSON responses.

---

### Version 1: Role Assignment
* **Named Technique Applied:** `Role Assignment`
* **Prompt:**
  > `"Act as a Senior Python Backend Architect specializing in containerized cloud services. Write a Flask app with Postgres and Redis."`

* **Output Excerpt:**
  ```python
  import os
  import psycopg2
  import redis
  from flask import Flask, jsonify

  app = Flask(__name__)

  def get_db():
      return psycopg2.connect(
          host=os.environ.get("DB_HOST", "localhost"),
          database=os.environ.get("DB_NAME", "app_db"),
          user=os.environ.get("DB_USER", "postgres"),
          password=os.environ.get("DB_PASSWORD", "secret")
      )
  ```

* **Iteration Note (What Changed & Why):**
  - *Observed Output Difference:* Assigning the Senior Backend Architect role caused the model to structure environment variable configurations (`os.environ.get`) instead of hardcoding localhost strings, and added structured database helper methods.

---

### Version 2: Context and Motivation
* **Named Technique Applied:** `Context and Motivation`
* **Prompt:**
  > `"Act as a Senior Python Backend Architect. We are deploying a production microservice that tracks visitor counts in PostgreSQL and caches health statuses in Redis. The service must handle high traffic without crashing when a database connection fluctuates. Write a Flask app with Postgres and Redis."`

* **Output Excerpt:**
  ```python
  @app.route('/status', methods=['GET'])
  def status_check():
      health = {"status": "ok", "db": "ok", "redis": "ok"}
      try:
          r.ping()
      except redis.ConnectionError:
          health["redis"] = "error"
          health["status"] = "degraded"
      
      try:
          conn = get_db_connection()
          conn.close()
      except Exception:
          health["db"] = "error"
          health["status"] = "error"
          
      status_code = 200 if health["status"] == "ok" else 503
      return jsonify(health), status_code
  ```

* **Iteration Note (What Changed & Why):**
  - *Observed Output Difference:* Adding high-traffic motivation and uptime context forced the model to generate robust try/except error handling around database and Redis calls, returning HTTP 503 Service Unavailable when dependencies fail.

---

### Version 3: Few-Shot Examples
* **Named Technique Applied:** `Few-Shot Examples`
* **Prompt:**
  > `"Act as a Senior Backend Architect building a production microservice.
  > Here is an example of the expected JSON response for /status:
  > Input: GET /status (Redis connected, DB disconnected)
  > Output JSON: {"status": "error", "redis_status": "ok", "timestamp": "2026-07-30T19:30:00Z"}
  >
  > Input: GET / (Successful visit)
  > Output JSON: {"message": "Hello, World!"}
  > 
  > Write the Flask app implementing Postgres visit logging and Redis health checks matching these exact examples."`

* **Output Excerpt:**
  ```python
  from datetime import datetime, timezone

  @app.route('/status', methods=['GET'])
  def status():
      res = {"status": "ok", "redis_status": "ok"}
      # Redis check
      try:
          redis_client.ping()
      except Exception:
          res["redis_status"] = "error"
      # Postgres check
      try:
          conn = get_db_connection()
          conn.close()
      except Exception:
          res["status"] = "error"
          
      res["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
      return jsonify(res), (200 if res["status"] == "ok" else 500)
  ```

* **Iteration Note (What Changed & Why):**
  - *Observed Output Difference:* Providing few-shot input/output examples aligned key naming (`redis_status`, `timestamp`) and UTC ISO 8601 formatting to exact specification without guessing payload keys.

---

### Version 4: Output Structure
* **Named Technique Applied:** `Output Structure`
* **Prompt:**
  > `"Act as a Senior Backend Architect building a production Flask API. Follow the few-shot examples provided earlier.
  > Enforce the following Output Structure:
  > 1. Single-file Python script named app.py.
  > 2. Imports and Environment Config at top.
  > 3. Database connection pooling function get_db_connection().
  > 4. Flask endpoints @app.route('/') and @app.route('/status').
  > 5. Main block starting server on port 5000.
  > Do not include any conversational markdown introductions or summaries outside the code block."`

* **Output Excerpt:**
  ```python
  # app.py
  import os
  from datetime import datetime, timezone
  from flask import Flask, jsonify
  import psycopg2
  import redis

  app = Flask(__name__)
  # ... cleanly structured top-to-bottom implementation ...
  ```

* **Iteration Note (What Changed & Why):**
  - *Observed Output Difference:* Specifying strict structural layout eliminated conversational chatter, forced imports to the top, and outputted clean, directly copy-pasteable backend code.

---

### Version 5: Step Decomposition
* **Named Technique Applied:** `Step Decomposition`
* **Prompt:**
  > `"Act as a Senior Backend Architect. Build the Flask API with Postgres and Redis by following these steps in order:
  > Step 1: Read DB credentials (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT) and REDIS_HOST from environment variables with sensible defaults.
  > Step 2: Implement get_db_connection() returning a psycopg2 connection object.
  > Step 3: Implement GET / route that inserts a row into 'visits(visited_at)' table and returns {"message": "Hello, World!"}.
  > Step 4: Implement GET /status route checking DB and Redis health, appending UTC timestamp ('Z' suffix), and returning appropriate status code.
  > Step 5: Wrap database calls in parameterized queries to prevent SQL injection."`

* **Output Excerpt:**
  ```python
  @app.route('/', methods=['GET'])
  def hello():
      try:
          conn = get_db_connection()
          cur = conn.cursor()
          cur.execute("INSERT INTO visits (visited_at) VALUES (NOW());")
          conn.commit()
          cur.close()
          conn.close()
      except Exception as e:
          app.logger.error(f"Failed to record visit: {e}")
      return jsonify({"message": "Hello, World!"})
  ```

* **Iteration Note (What Changed & Why):**
  - *Observed Output Difference:* Step decomposition ensured that optional edge features (such as visit recording during GET `/` and exception logging) were fully realized rather than omitted or stubbed with `# TODO`.

---

## ⚖️ Cross-Model Comparison: Claude vs. ChatGPT

We ran the final decomposed prompt through both **Claude 3.5 Sonnet** and **ChatGPT (GPT-4o)**:

| Evaluation Dimension | Claude 3.5 Sonnet | ChatGPT (GPT-4o) |
| :--- | :--- | :--- |
| **Tone & Style** | Extremely concise, modular code structure, defensive error handling, no filler explanations. | Instructional and verbose; added detailed docstrings and explanatory markdown after code block. |
| **Accuracy & Security** | Used parameterized SQL queries and explicitly closed cursors in `finally` blocks to prevent leakages. | Used parameterized queries, but omitted explicit `cur.close()` calls before connection closing. |
| **Structure & Flow** | Followed environment variable defaults and ISO 8601 formatting (`Z` suffix) cleanly on first try. | Used standard `isoformat()` which appended `+00:00` offset instead of the specified `Z` string format. |
| **Failure Points** | Required explicit mention to include `conn.commit()` after `INSERT` operations. | Over-complicated error responses by returning nested error traces in production JSON payloads. |

---

## 🧩 Final Reusable Prompt Template (Generic & Context-Free)

```text
Act as a Senior Backend Engineer. Your task is to build a containerized Python web API service using Flask, PostgreSQL, and Redis.

Requirements:
1. Environment Setup:
   - Read DB connection parameters (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT) and REDIS_HOST/REDIS_PORT from environment variables with defaults.

2. Database & Cache Operations:
   - Create a connection helper `get_db_connection()` using psycopg2.
   - Use parameterized SQL queries for all database interactions.
   - Ensure cursors and connections are properly closed after usage.

3. API Endpoints:
   - GET / : Record event timestamp in PostgreSQL table `visits` and return JSON `{"message": "Hello, World!"}`.
   - GET /status : Check PostgreSQL and Redis ping connectivity. Return JSON payload containing `status` ("ok" or "error"), `redis_status` ("ok" or "error"), and `timestamp` (UTC ISO 8601 string ending with 'Z'). Return HTTP 200 if healthy, or HTTP 500/503 if primary DB connection fails.

4. Output Format:
   - Return clean, runnable single-file Python code (`app.py`).
```
