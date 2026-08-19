# Assignment FL-06 — Personal Agent Design Specification

**Agent Name:** `BackendEngineerAgent`  
**Author / User:** Mehedi Hasan (@Rytnix786)  
**Track:** General AI Fluency — Week 5 (Phase: Build)  
**Deliverable File:** `AI-Fluency-w5/FL-06_personal_agent_design_spec.md`  
**Live Companion Code:** [`AI-Fluency-capstone/personal_agent.py`](file:///h:/FlyRank-Works-Backend/AI-Fluency-capstone/personal_agent.py)  

---

## 1. 🎯 Job To Be Done (JTBD) & Scope

### Primary Job:
An autonomous **Backend Codebase Auditor & Security Verification Agent** that inspects newly built Python backend APIs, executes automated unit test suites, audits endpoints for JWT authentication and secrets leakage, and compiles an evidence-backed markdown audit report before code is committed to production.

### Scope Boundary (Target: ~10 Build Hours):
* **In-Scope:** Parsing Python AST and routes (`FastAPI` / `Flask`), running local `pytest` / `unittest` subprocess loops, checking live HTTP status contracts, scanning for hardcoded secrets, and formatting structured markdown reports.
* **Out-of-Scope:** Automated code refactoring or destructive file mutations without human approval.

---

## 2. 👤 The User & Usage Frequency

* **Primary User:** Mehedi Hasan (Python Backend & AI Engineer).
* **Usage Frequency:** Daily (pre-commit hook or on-demand via CLI before opening Pull Requests).
* **Expected Runtime:** < 30 seconds per execution turn.

---

## 3. 🛠️ Tools, Data Sources & Access Plan

| Tool Name | Action & Purpose | Data Source / Access Plan |
| :--- | :--- | :--- |
| **`inspect_codebase(path)`** | Parses file lines, route definitions, and function signatures. | Local file system read access via standard Python `os` / `ast`. |
| **`run_unit_tests(test_path)`** | Executes unit test runner and captures stdout/stderr and exit codes. | Local subprocess execution (`python -m unittest` / `pytest`). |
| **`check_api_endpoint(url)`** | Dispatches HTTP GET/POST requests and checks status code contracts. | Network HTTP client (`requests` / `urllib`). |
| **`audit_security(path)`** | Scans source code for Bearer JWT guards, exception handling, and `.env` loading. | Local AST and regex string analysis. |

---

## 4. 📋 Draft Agent System Instructions

```text
You are 'BackendEngineerAgent', an autonomous AI engineering auditor.
Your goal is to verify that a target backend microservice is secure, functional, and ready for production.

Execution Flow:
1. Call `inspect_codebase` to understand the endpoints, lines of code, and structure.
2. Call `audit_security` to verify JWT protection, secret loading via os.getenv, and try/except blocks.
3. Call `run_unit_tests` to execute the automated test suite.
4. If a live URL is provided, call `check_api_endpoint` to probe the /health status.
5. Compile all tool outputs into a structured Markdown report with clear PASS / FAIL verdicts.
```

---

## 5. 🧪 Five Concrete Evaluation Cases (Defined Pre-Build)

1. **Eval 1 (Clean FastAPI Microservice):** Target `Task4-w4-a1` with all 9 unit tests passing and JWT auth in place.  
   *Expected Outcome:* Full PASS report generated with 0 security warnings.
2. **Eval 2 (Failing Test Suite Detection):** Introduce an assertion error in a test file.  
   *Expected Outcome:* Agent captures exact traceback, pinpoints failing assertion, and refuses a PASS verdict.
3. **Eval 3 (Missing Auth Security Alert):** Target an unprotected route handling sensitive user data.  
   *Expected Outcome:* Agent flags `[SECURITY WARNING] Missing JWT Bearer protection on sensitive endpoint`.
4. **Eval 4 (Hardcoded Secret Leakage):** Insert a plain-text API key (`sk-or-v1-...`) directly in source code.  
   *Expected Outcome:* Agent detects raw secret pattern, redacts token from log output, and triggers a HIGH risk alert.
5. **Eval 5 (Offline Endpoint Handling):** Probe an unreachable localhost port (e.g. `http://localhost:9999`).  
   *Expected Outcome:* Agent catches `ConnectionRefusedError` gracefully without crashing and notes service is offline.

---

## 6. 🛡️ Risks, Guardrails & Failure Modes

* **Must Confirm Before Executing:** Any action that writes, alters, or deletes files on disk.
* **Strictly Prohibited Actions:**
  - Never print unredacted `.env` API keys or passwords to console or markdown reports.
  - Never run destructive shell commands (`rm -rf`, `DROP TABLE`, `git push --force`).
  - Never hallucinate test passing status when subprocess exit code is non-zero (`exit != 0`).

---

## 7. ⚖️ Platform Choice & Justification

### Chosen Platform:
**Scripted Python Autonomous Agent (`personal_agent.py`)** with native tool calling loop.

### Alternatives Evaluated:
1. **Custom GPT (OpenAI Plus):** Cloud-only; cannot access local development files or run local `pytest` terminal commands without cumbersome tunnel setups.
2. **n8n Workflow Automation:** Good for webhooks, but introduces external server overhead for simple pre-commit developer tasks.

### Why Scripted Python Wins:
- **Zero Subscriptions / Free Execution:** Runs directly in local terminal or CI/CD pipelines.
- **Direct Local Access:** Reads local code and runs local test suites with zero latency.
- **Full Determinism:** Tool arguments, error handling, and output reporting are 100% reproducible and inspectable.
