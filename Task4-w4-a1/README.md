# Assignment W4 — Auth: Login & Protect (FastAPI + Supabase)

A secure, production-grade RESTful API built with **Python 3.10+**, **FastAPI**, and **Supabase Auth** as the Identity Provider (IdP). This service implements complete user authentication workflows (Sign Up, Log In, Log Out) and enforces Bearer JWT token verification on protected API routes.

---

## 🔒 Purpose & Security Architecture

Traditional open APIs permit unrestricted read/write access. This microservice secures endpoints using a **Trust Triangle**:

1. **The Client**: Requests tokens via credentials and presents JWTs in the HTTP `Authorization: Bearer <token>` header.
2. **Identity Provider (Supabase Auth)**: Manages user accounts, password hashes, and issues cryptographically signed JWT Access Tokens.
3. **Backend API Server (FastAPI)**: Extracts and verifies JWT tokens using reusable dependency middleware (`get_current_user`) before opening protected routes.

---

## 📁 Repository Structure

```text
Task4-w4-a1/
├── .env                       # Local secrets (Git-ignored)
├── .env.example               # Public environment template with placeholders
├── .gitignore                 # Excludes .env, __pycache__, .venv, .pytest_cache
├── app.py                     # Main FastAPI application, routes, & middleware
├── test_app.py                # Automated Pytest / Unittest test suite (9 passing tests)
├── requirements.txt           # Project dependencies
└── README.md                  # Comprehensive documentation & AI vs Me audit
```

---

## 🛠️ How to Install & Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your Supabase project credentials in `.env`:
```ini
SUPABASE_URL=https://mtkgstzagbhcxhswmiqq.supabase.co
SUPABASE_KEY=your_anon_public_key_here
PORT=8000
```

### 3. Run the Server (Single Terminal Command)
```bash
python app.py
```
*The server starts on `http://127.0.0.1:8000` and logs:*
`Server running and connected to Supabase`

### 4. Run Automated Test Suite
```bash
python -m unittest test_app.py
```

---

## 📊 API Reference Table

| Method | Endpoint | Description | Auth Required | Expected Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/public/info` | Public welcome information | `None` | `200 OK` |
| `POST` | `/auth/signup` | Register a new user account | `None` | `201 Created`, `400 Bad Request` |
| `POST` | `/auth/login` | Authenticate & issue JWT access token | `None` | `200 OK`, `400 Bad Request`, `401 Unauthorized` |
| `POST` | `/auth/logout` | Terminate user session | `Bearer Token` | `204 No Content`, `401 Unauthorized` |
| `GET` | `/protected/profile` | Read private user profile metadata | `Bearer Token` | `200 OK`, `401 Unauthorized` |
| `GET` | `/protected/dashboard` | Read protected dashboard data | `Bearer Token` | `200 OK`, `401 Unauthorized` |

---

## 🧪 Sample `curl` Commands

```bash
# 1. Register a new user
curl -i -X POST http://127.0.0.1:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com", "password": "Password123!"}'

# 2. Log in and acquire JWT Token
curl -i -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com", "password": "Password123!"}'

# 3. Access protected profile using Access Token
curl -i http://127.0.0.1:8000/protected/profile \
  -H "Authorization: Bearer <PASTE_YOUR_ACCESS_TOKEN_HERE>"

# 4. Log out
curl -i -X POST http://127.0.0.1:8000/auth/logout \
  -H "Authorization: Bearer <PASTE_YOUR_ACCESS_TOKEN_HERE>"
```

---

## 🔓 Swagger UI & Authorize Padlock Button (`/docs`)

FastAPI generates interactive Swagger documentation automatically at `http://127.0.0.1:8000/docs`.

### How to Authorize in Swagger UI:
1. Open `http://127.0.0.1:8000/docs` in your browser.
2. Execute `POST /auth/login` with your credentials and copy the `access_token` string from the JSON response.
3. Click the green **Authorize** 🔓 padlock button at the top right.
4. Paste your `access_token` into the Value field and click **Authorize**.
5. The lock icons next to `/protected/profile`, `/protected/dashboard`, and `/auth/logout` will lock 🔒, enabling authenticated **"Try it out"** requests directly in your browser!

---

## ⚔️ Stage 7 — The AI Rematch: AI vs. Me Analysis

We evaluated an AI-generated authentication boilerplate against our production implementation across four core security dimensions:

| Dimension | Manual Implementation (Me) | AI-Generated Boilerplate |
| :--- | :--- | :--- |
| **Bearer Prefix Parsing** | Used FastAPI `HTTPBearer(auto_error=False)` which natively strips the `Bearer ` string cleanly and safely returns `401 {"error": "Access token required"}` when missing. | Used raw string manipulation (`req.headers["Authorization"].split(" ")[1]`), which threw unhandled `IndexError` 500 server crashes when `Bearer` was omitted. |
| **Status Code Accuracy** | Strictly enforced `201 Created` for signup, `204 No Content` for logout, `400 Bad Request` for empty payloads, and `401 Unauthorized` for failed auth. | Lazily returned `200 OK` for all endpoints (including signup and failed logins), violating RESTful status code specifications. |
| **Token Verification Safety** | Wrapped Supabase verification in try/except blocks, returning clean `401 {"error": "Invalid or expired token"}` payloads without leaking internal stack traces. | Exposed internal database error messages (`jwt claim error: token is expired`) directly in JSON response bodies, creating security information leaks. |
| **Session Invalidation** | Implemented `POST /auth/logout` with Bearer token invalidation and `204 No Content` status. | Completely omitted the `/auth/logout` endpoint, assuming client-side token deletion was sufficient. |

### Summary Verdict:
While AI can rapidly generate basic syntax, manual engineering ensures defensive error handling, precise HTTP status code compliance, and zero security information leaks.
