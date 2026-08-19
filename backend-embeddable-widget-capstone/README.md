# Embeddable Widget & Lead-Capture Platform (`flyrank-capstone-widget-platform`)

> **FlyRank Internship · Backend AI Engineering Track · Capstone**  
> An embeddable lead-capture widget platform featuring hardened cross-origin submission pipelines, honeypot spam protection, sliding-window rate limiting, two-tier geo-enrichment fallback chains, and resilient side effects.

---

## 🏛️ 1. Architecture Overview

The system strictly isolates three operational request pathways:

```text
1. WIDGET OWNER (Authenticated Admin Path)
   └─► POST /api/v1/widgets ─► Tenant-Isolated Widget DB ─► Returns <script> embed snippet

2. CUSTOMER WEBSITE (Public Cached Delivery Path — Any Origin)
   └─► <script src="http://localhost:8000/widget.js?id=w_123"></script>
         ├─► GET /widget.js (Cache-Control: public, max-age=31536000, immutable)
         └─► GET /api/v1/widgets/w_123/config (CORS *, Cache-Control: public, max-age=60)
               └─► Dynamic DOM Rendering (Lead-Capture Form)

3. WEBSITE VISITOR (Hardened Public Submission Path — Cross-Origin)
   └─► POST /api/v1/submissions (Public · CORS *)
         ├─► [1] CORS & Preflight Verification (OPTIONS handled)
         ├─► [2] Boundary Payload Validation (Name, Email, Length) ➔ Bad input? HTTP 400
         ├─► [3] Honeypot Spam Check (_website_url_hp) ➔ Bot detected? Flagged / Quietly dropped
         ├─► [4] IP & Widget Rate Limiting (Sliding Window) ➔ Burst flood? HTTP 429 + Retry-After
         ├─► [5] Geo Enrichment Fallback Chain:
         │       Provider A (ip-api) ─(fails)─► Provider B (ipapi.co) ─(fails)─► Store without Geo
         ├─► [6] Atomic DB Storage (Linked to tenant_id & widget_id)
         └─► [7] Safe Email Side Effect ➔ If email fails, submission STILL returns HTTP 201 Created!
```

---

## 🗄️ 2. Multi-Tenant Data Model

```text
+-------------------+           +-------------------+           +-----------------------+
|     tenants       |           |      widgets      |           |      submissions      |
+-------------------+           +-------------------+           +-----------------------+
| id (PK)           | 1       * | id (PK)           | 1       * | id (PK)               |
| name              | <-------- | tenant_id (FK)    | <-------- | tenant_id (FK)        |
| api_key           |           | title             |           | widget_id (FK)        |
| created_at        |           | description       |           | name                  |
+-------------------+           | button_text       |           | email                 |
                                | allowed_origins   |           | message               |
                                | fields_config     |           | ip_address            |
                                | created_at        |           | country, city         |
                                +-------------------+           | geo_provider          |
                                                                | is_spam               |
                                                                | created_at            |
                                                                +-----------------------+
```

---

## 🔌 3. API Contracts

### 1. Public Submission: `POST /api/v1/submissions`
- **CORS:** Allowed from any origin (`Access-Control-Allow-Origin: *`).
- **Payload:**
  ```json
  {
    "widget_id": "w_demo_123",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "message": "Interested in your service!",
    "_website_url_hp": ""
  }
  ```
- **Responses:**
  - `201 Created`: Submission validated, enriched, and stored.
  - `400 Bad Request`: Validation failure (malformed email, missing required fields).
  - `429 Too Many Requests`: Rate limit exceeded (includes `Retry-After` header).

### 2. Widget Config: `GET /api/v1/widgets/{widget_id}/config`
- **CORS:** Allowed from any origin.
- **Cache:** `Cache-Control: public, max-age=60`.

### 3. Embed Script: `GET /widget.js`
- **Cache:** `Cache-Control: public, max-age=31536000, immutable`.

### 4. Owner Analytics: `GET /api/v1/analytics/stats`
- **Headers:** `X-API-Key: <tenant_api_key>`
- **Response:** Total submission count, daily distribution, and top widgets.

---

## 🛠️ 4. Setup & Running Instructions

### 1. Environment Configuration
```bash
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Backend API
```bash
python app.py
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

### 4. Run Automated Tests
```bash
python -m pytest test_widget_platform.py -v
```

---

## 🚫 5. Non-Goals Definition (§ 7)
- **No Complex Form Builder UI:** Focuses strictly on backend hardening, resilience, CORS, geo fallback, and embed delivery.
- **No Real SMTP Infrastructure Required:** Email side effects log to console or mock handlers; failure resilience is what is strictly tested and verified.
