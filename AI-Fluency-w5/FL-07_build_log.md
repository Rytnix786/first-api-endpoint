# Assignment FL-07 — Build the Agent: Build Log & Execution Proof

**Agent Name:** `BackendEngineerAgent`  
**Author / Developer:** Mehedi Hasan (@Rytnix786)  
**Track:** General AI Fluency — Week 5 (Phase: Build)  
**Deliverable File:** `AI-Fluency-w5/FL-07_build_log.md`  
**Agent Source Code:** [`AI-Fluency-capstone/personal_agent.py`](file:///h:/FlyRank-Works-Backend/AI-Fluency-capstone/personal_agent.py)  

---

## 🛠️ 1. Build Narrative & Spec Matching

I implemented `BackendEngineerAgent` as an autonomous Python CLI script adhering to the design established in **FL-06**:
* Built dynamic tool registration utilizing **Pydantic v2** (`AgentToolResult`) with typed output contracts.
* Connected 4 real, live tools:
  1. `inspect_codebase`: Reads and parses local Python files, counting lines, routes (`@app`), and imports.
  2. `audit_security`: Audits AST patterns for `HTTPBearer` JWT guards, try/except error safety, and `os.getenv` environment secret isolation.
  3. `run_unit_tests`: Invokes local `subprocess` test runner for automated regression detection.
  4. `check_api_endpoint`: Issues HTTP requests via `httpx` to probe live endpoint health.

---

## 💥 2. What Broke & What Was Changed (Real Iterations)

### Issue 1: `unittest` Test Discovery Across Sibling Directories
* **What Broke:** When running tests located in `../Task4-w4-a1/test_app.py`, `python -m unittest` failed because the working directory defaulted to the agent's root directory, resulting in `ModuleNotFoundError: No module named 'app'`.
* **Fix:** Updated `tool_run_unit_tests` to split the path, setting `cwd = os.path.dirname(test_file)` dynamically before triggering `subprocess.run()`.

### Issue 2: Standard Error (`stderr`) Stream in Python `unittest`
* **What Broke:** Python's built-in `unittest` runner writes test execution progress dots (`.........`) and the final `OK` summary to `sys.stderr` rather than `sys.stdout`. The agent initially marked runs as failed because `stderr` was not empty.
* **Fix:** Updated the status determination logic to check `result.returncode == 0` or `"OK" in result.stderr`.

---

## ✂️ 3. What Was Cut from the FL-06 Spec & Why

* **Cut Cloud Database Migration Runner:** In the initial FL-06 brainstorm, I considered adding a live database migration tool. I intentionally cut this from the MVP because pre-commit validation must run in < 2 seconds offline without requiring remote database credentials or risk of corrupting production data.

---

## 📺 4. Raw, Unedited End-to-End Run Capture Transcript

```text
$ python personal_agent.py --target "../Task4-w4-a1/app.py" --test "../Task4-w4-a1/test_app.py"

2026-08-19 23:16:27,826 [INFO] [AGENT] [Rytnix-Backend-Agent] Starting Autonomous Agent Turn for Goal: 'Audit Task 4 FastAPI Auth Microservice'
2026-08-19 23:16:27,826 [INFO] [TOOL] inspect_codebase('../Task4-w4-a1/app.py')
2026-08-19 23:16:27,831 [INFO] [TOOL] audit_security('../Task4-w4-a1/app.py')
2026-08-19 23:16:27,831 [INFO] [TOOL] run_unit_tests('../Task4-w4-a1/test_app.py')

============================================================
PERSONAL AGENT EXECUTION COMPLETED
============================================================
# Agent Audit Report: app.py

**Agent:** Rytnix-Backend-Agent  
**Goal:** Audit Task 4 FastAPI Auth Microservice  
**Timestamp:** 2026-08-19T17:16:29.695052+00:00  

## Executed Agent Tools & Observations

### Tool Invoked: `inspect_codebase` (Status: `success`)
```json
{
  "file_path": "../Task4-w4-a1/app.py",
  "lines_count": 269,
  "endpoints_found": 16,
  "sample_definitions": [
    "@app.exception_handler(HTTPException)",
    "async def custom_http_exception_handler(request: Request, exc: HTTPException):",
    "def get_supabase_headers(token: Optional[str] = None) -> Dict[str, str]:",
    "async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:",
    "@app.get(\"/public/info\", tags=[\"Public\"])",
    "async def public_info():",
    "@app.post(\"/auth/signup\", status_code=status.HTTP_201_CREATED, tags=[\"Auth\"])",
    "async def signup(payload: SignupRequest):"
  ],
  "imports": [
    "import os",
    "from typing import Optional, Dict, Any",
    "from dotenv import load_dotenv",
    "from fastapi import FastAPI, Depends, HTTPException, status, Request, Response",
    "from fastapi.responses import JSONResponse",
    "from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials"
  ]
}
```

### Tool Invoked: `audit_security` (Status: `success`)
```json
{
  "file_path": "../Task4-w4-a1/app.py",
  "audit_checks_passed": 3,
  "security_findings": [
    "[PASS] Uses Bearer JWT authentication mechanism.",
    "[PASS] Exception handling blocks present for runtime safety.",
    "[PASS] Environment secrets loaded securely via os.getenv."
  ]
}
```

### Tool Invoked: `run_unit_tests` (Status: `success`)
```json
{
  "returncode": 0,
  "passed": true,
  "stdout": "Server running and connected to Supabase",
  "stderr": ".........\n----------------------------------------------------------------------\nRan 9 tests in 1.175s\n\nOK"
}
```

## Autonomous Agent Verdict
All code structure, security checks, and automated test loops executed successfully without critical vulnerabilities.

[SUCCESS] Agent report saved to: agent_audit_report.md
```
