# General AI Fluency - Week 2: Frame It As Cases

## 🎯 Voice Card
`Direct, plain, concise, technical, no corporate buzzwords, outcome-focused`

---

## 🛠️ Case Studies

### Piece 1: Minimal Flask API Endpoint & Health Monitoring
*(Project: Task 1 - First API Endpoint)*

* **The Problem:** 
  Microservice architectures require lightweight entry points and standardized health checks so monitoring tools know instantly if an application server is live or experiencing outages.

* **What I Did & Decided:**
  I built a Flask backend service with two core HTTP routes: `/` for primary endpoint connectivity and `/status` for server health. I decided to standardize the status response format using Python’s native `datetime` module formatted as a UTC ISO 8601 string (`Z` suffix), ensuring timestamp consistency across distributed systems without adding heavy third-party dependencies.

* **What Came of It:**
  A lightweight, fully tested API service (`100% test coverage via unittest`) ready for integration into larger backend microservices with predictable status payloads.

---

### Piece 2: Containerized Flask Backend with PostgreSQL & Redis Caching
*(Project: Task 2 - Database Integration & Performance Benchmarking)*

* **The Problem:**
  In-memory backend state resets whenever a server restarts. Furthermore, unindexed database queries degrade rapidly in response time as database tables scale to tens of thousands of rows.

* **What I Did & Decided:**
  I containerized the Flask API alongside PostgreSQL 16 and Redis 7 using Docker Compose with dedicated named volumes (`pgdata`) to persist state across container teardowns. To improve query efficiency, I added a B-tree index (`idx_visits_visited_at`) on timestamp-filtered columns and benchmarked query execution using PostgreSQL’s `EXPLAIN ANALYZE` on 10,000 synthetic rows.

* **What Came of It:**
  Execution time for timestamp queries dropped from **0.526 ms** (Sequential Scan) to **0.054 ms** (Index Scan)—delivering a **~10x speedup**—while ensuring zero data loss during simulated system reboots.

---

### Piece 3: Task CRUD RESTful Service with SQLite Persistence
*(Project: Task 3 - Connecting CRUD to Database)*

* **The Problem:**
  Building a reliable task management backend requires persistence and strict API contracts without relying on heavy database server installations during early development or edge deployment.

* **What I Did & Decided:**
  I refactored the task management REST API to replace array-based mock storage with SQLite persistence (`tasks.db`). I implemented raw SQL parametrized queries (`INSERT`, `SELECT`, `UPDATE`, `DELETE`) with strict validation (returning `400 Bad Request` for invalid payloads and `404 Not Found` for missing resources) and added automated startup seeding for initial baseline records.

* **What Came of It:**
  A zero-config, production-contract compliant CRUD API supporting complete task lifecycles with raw SQL validation and verified persistence across server restarts.

---

## 👤 Bio & Contact / Call to Action (CTA)

* **Bio:** 
  Backend engineer building clean, containerized Python APIs, database models, and high-performance server architectures.

* **Contact / CTA:**
  Looking to build fast, well-tested backend services? Explore my code on [GitHub](https://github.com/Rytnix786/first-api-endpoint) or get in touch via email.

---

## 🔄 Before vs. After (Generic AI vs. Voice-Edited)

* **Generic AI Version:**
  > *"Leveraged cutting-edge containerized microservices and robust database optimization strategies to seamlessly maximize server throughput and deliver next-generation backend efficiency."*

* **My Edited Version (Voice-Driven):**
  > *"Containerized a Flask API with Docker, integrated Redis caching, and indexed PostgreSQL timestamps to cut query execution time from 0.526 ms down to 0.054 ms."*
