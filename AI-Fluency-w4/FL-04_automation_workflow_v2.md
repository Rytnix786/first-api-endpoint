# FL-04: Ship an Automation Workflow v2

## ⚙️ 1. Pipeline Overview & Step Flow Diagram

**Selected Pipeline:** *Backend Microservice API Spec, Security Audit & README Documentation Pipeline*  
**Goal:** Automate the end-to-end transformation of raw backend code repos into security-audited, RESTful status-code compliant technical documentation.

```text
+-------------------+     Handoff JSON      +-------------------------+
| Step 1: Gather &  |  ===================> | Step 2: Synthesize &    |
| Extract Codebase  | (Endpoints & Schemas) | Security Audit          |
+-------------------+                       +-------------------------+
                                                         |
                                                         | Handoff Draft
                                                         v
+-------------------+     Handoff README    +-------------------------+
| Step 4: Format &  |  <=================== | Step 3: Critique &      |
| Deliver Final Doc |  (Voice Card Aligned) | Voice Refinement        |
+-------------------+                       +-------------------------+
```

---

## 📑 2. Step Prompts & Configuration

### Step 1: Gather & Extract (Input Source Grounding)
* **Goal:** Parse raw source files (`app.py`, `main.py`, `.env.example`, `requirements.txt`) into a structured technical inventory.
* **Prompt Configuration:**
  > `"Act as a Code Intelligence Parser. Analyze the provided repository source code. Extract and output a JSON schema containing: 1) API framework (FastAPI/Flask), 2) Database type & ORM/driver, 3) Complete list of HTTP endpoints with request body schemas, 4) Authentication mechanism (JWT Bearer, API key, or None), and 5) Environment variables required. Do not output prose explanations—output valid JSON only."`

### Step 2: Synthesize & Security Audit
* **Goal:** Audit endpoints against OWASP API security guidelines and generate a raw technical draft.
* **Prompt Configuration:**
  > `"Act as a Senior API Security Auditor. Take the JSON inventory from Step 1 and evaluate: 1) Are HTTP status codes RESTful (201 Created on signup, 204 No Content on logout, 400 Bad Request on empty payloads, 401 Unauthorized on missing tokens)? 2) Is JWT token extraction protected via try/except blocks? 3) Are parameterized SQL queries used to prevent SQL injection? Output a raw technical markdown draft outlining endpoint behavior, security controls, and error contract details."`

### Step 3: Critique & Voice Refinement
* **Goal:** Audit the technical draft against the developer's Voice Card and strip AI hype.
* **Prompt Configuration:**
  > `"Act as an Editor enforcing the Voice Card: 'Direct, plain, concise, technical, no corporate buzzwords, outcome-focused'. Review the raw technical draft from Step 2: 1) Eliminate buzzwords like 'seamless', 'cutting-edge', 'leveraged', and 'robust'. 2) Ensure all technical statements reference real metrics (e.g. EXPLAIN ANALYZE millisecond timings or unit test counts). 3) Verify that code snippets use copy-pasteable curl commands."`

### Step 4: Format & Finalize
* **Goal:** Format into a production-ready `README.md` document with installation steps, environment table, API reference, and Swagger `/docs` guide.
* **Prompt Configuration:**
  > `"Act as a Technical Documentation Specialist. Take the refined content from Step 3 and format it into a standardized GitHub README.md layout: 1) Project Title & Overview, 2) Installation & Setup commands, 3) API Reference Table, 4) Sample curl commands, 5) Security & Error Handling documentation. Ensure markdown formatting is clean with proper code fences."`

---

## 🧪 3. Documented Execution Across 5 Real Workspace Runs

### Run 1: Task1-w1 (Flask Microservice & ISO Status API)
* **Input Codebase:** `Task1-w1/app.py`
* **Step 1 Handoff JSON:** `{"framework": "Flask", "endpoints": ["/ [GET]", "/status [GET]"], "auth": "None"}`
* **Step 2 Security Audit:** Verified ISO 8601 UTC timestamp format with `Z` suffix. Flagged missing rate limiting on `/status`.
* **Step 3 Voice Critique:** Removed "lightweight microservice solution" fluff; focused on `unittest` 100% test coverage.
* **Step 4 Final Output Excerpt:**
  ```markdown
  ## API Endpoints
  - `GET /`: Returns welcome payload `{"message": "Hello, World!"}`.
  - `GET /status`: Returns UTC ISO 8601 server health timestamp `{"status": "ok", "timestamp": "2026-07-30T19:30:00Z"}`.
  ```

### Run 2: Task2-w2 (Docker Compose + PostgreSQL Indexing + Redis 7)
* **Input Codebase:** `Task2-w2/app.py`, `Task2-w2/docker-compose.yml`, `Task2-w2/init.sql`
* **Step 1 Handoff JSON:** `{"framework": "Flask", "db": "PostgreSQL 16 + B-tree Index", "cache": "Redis 7"}`
* **Step 2 Security Audit:** Verified B-tree index (`idx_visits_visited_at`) on 10,000 synthetic rows using `EXPLAIN ANALYZE`.
* **Step 3 Voice Critique:** Replaced generic "high performance database" text with exact timing numbers (**0.526 ms ➔ 0.054 ms** ~10x speedup).
* **Step 4 Final Output Excerpt:**
  ```markdown
  ## Performance Benchmarking (EXPLAIN ANALYZE)
  - Seq Scan (No Index): `0.526 ms`
  - Index Scan (B-tree): `0.054 ms` (⚡ ~10x Speedup)
  ```

### Run 3: Task3-w3-a1 (SQLite CRUD REST API)
* **Input Codebase:** `Task3-w3-a1/app.py`, `Task3-w3-a1/db.py`
* **Step 1 Handoff JSON:** `{"framework": "Flask", "db": "SQLite3 (tasks.db)", "crud": ["GET", "POST", "PUT", "DELETE"]}`
* **Step 2 Security Audit:** Verified parametrized SQL queries (`?`) preventing SQL injection; verified startup auto-seeding.
* **Step 3 Voice Critique:** Ensured error status codes (`400 Bad Request`, `404 Not Found`) were explicitly highlighted.
* **Step 4 Final Output Excerpt:**
  ```markdown
  ## Database Schema (tasks.db)
  `CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, done BOOLEAN DEFAULT 0);`
  ```

### Run 4: Task4-w4-a1 (FastAPI + Supabase Auth IdP + JWT Bearer Guard)
* **Input Codebase:** `Task4-w4-a1/app.py`, `Task4-w4-a1/test_app.py`, `Task4-w4-a1/.env`
* **Step 1 Handoff JSON:** `{"framework": "FastAPI", "auth_idp": "Supabase Auth", "middleware": "get_current_user"}`
* **Step 2 Security Audit:** Verified `HTTPBearer` security scheme in OpenAPI `/docs`; audited `401 Unauthorized` token handling.
* **Step 3 Voice Critique:** Structured Stage 7 AI vs. Me comparative security analysis.
* **Step 4 Final Output Excerpt:**
  ```markdown
  ## OpenAPI Swagger UI (/docs)
  Swagger UI automatically configures the green Authorize 🔓 padlock button for Bearer JWT token verification.
  ```

### Run 5: FlyRank-Backend-Core (Autonomous LLM Trading Agent & Rate Limiter)
* **Input Codebase:** `Task4-w4-a1/app.py` (Rate Limiting & Safety Guard Module)
* **Step 1 Handoff JSON:** `{"module": "Rate Limiter & Wallet Guard", "strategy": "Token Bucket + Circuit Breaker"}`
* **Step 2 Security Audit:** Evaluated sliding window log rate limiting and spend limits to prevent prompt injection wallet drains.
* **Step 3 Voice Critique:** Cut speculative claims; focused on p95 latency guarantees.
* **Step 4 Final Output Excerpt:**
  ```markdown
  ## Security Controls
  Sliding window rate limiting enforces max 100 req/min with immediate HTTP 429 Too Many Requests responses.
  ```

---

## ⏱️ 4. Honest Time Accounting & Cost Analysis

| Activity | Manual Execution Time | Automated Workflow Time | Time Saved |
| :--- | :--- | :--- | :--- |
| **Workflow Setup Cost (Prompts & Handoff Schemas)** | N/A | 45 minutes (One-time) | -45 minutes |
| **Run 1 (Task 1 Documentation & Audit)** | 60 minutes | 6 minutes | +54 minutes |
| **Run 2 (Task 2 Documentation & Audit)** | 60 minutes | 6 minutes | +54 minutes |
| **Run 3 (Task 3 Documentation & Audit)** | 60 minutes | 6 minutes | +54 minutes |
| **Run 4 (Task 4 Documentation & Audit)** | 60 minutes | 6 minutes | +54 minutes |
| **Run 5 (Backend Core Documentation & Audit)** | 60 minutes | 6 minutes | +54 minutes |
| **TOTAL (Across 5 Runs)** | **300 minutes (5.0 hrs)** | **75 minutes (1.25 hrs)** | **225 minutes (~3.75 hrs saved)** |

---

## ⚠️ 5. Known Failure Points & Required Human Review Gates

1. **Secret Leak Inspection (Critical Gate):**  
   *Failure Mode:* The automated workflow might accidentally include live `.env` credentials in example Markdown code blocks if the source code contains hardcoded strings.  
   *Required Human Review:* Human must inspect `README.md` before publishing to confirm zero secret keys are exposed.

2. **Benchmark Number Verification:**  
   *Failure Mode:* The AI might estimate or hallucinate execution timings if terminal outputs are truncated.  
   *Required Human Review:* Human must cross-reference `EXPLAIN ANALYZE` timings against real `psql` terminal logs.

3. **SDK Deprecation Updates:**  
   *Failure Mode:* Supabase SDK or FastAPI version updates can alter default exception classes (e.g. Pydantic v1 vs v2 annotations).  
   *Required Human Review:* Human must verify that error handling models match the exact installed package versions.
