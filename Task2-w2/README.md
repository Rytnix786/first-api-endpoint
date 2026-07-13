# first-api-endpoint

A minimal Flask backend server with two API endpoints, containerized and backed by a PostgreSQL database and Redis cache.

## Running with Docker Compose

1. Make sure you have Docker running in the background.
2. In the `Task2-w2` directory, copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Start the application, database, and Redis cache services:
   ```bash
   docker compose up --build
   ```
   This will spin up:
   - A PostgreSQL 16 database container (`postgres_db`).
   - A Redis cache container (`redis_cache`).
   - The Flask app container (`flask_app`) which will run once the database is healthy.
   - The DB schema and indexes will be automatically created on the first run via `init.sql`.

## API Endpoints

The API routes behave identically to the original in-memory version:

### 1. Hello World
Returns a simple welcome message and logs a database entry in the `visits` table.
```bash
curl http://127.0.0.1:5000/
```
Expected output:
```json
{"message": "Hello, World!"}
```

### 2. Status Check
Returns the health status of the Flask application, PostgreSQL database, and Redis cache, along with a UTC ISO timestamp.
```bash
curl http://127.0.0.1:5000/status
```
Expected output (if healthy):
```json
{
  "redis_status": "ok",
  "status": "ok",
  "timestamp": "2026-07-13T09:39:06.531995Z"
}
```
If PostgreSQL is down, `status` will be `"error"`. If Redis is down, `redis_status` will be `"error"`.

## Verification of Persistence

We verified that data persists across database container restarts using a named Docker volume (`pgdata`):

1. **Start the containers** using `docker compose up`.
2. **Generate data** by calling the hello endpoint (`curl http://127.0.0.1:5000/`) a few times.
3. **Verify entries exist** in the Postgres database:
   ```bash
   docker compose exec db psql -U postgres -d postgres_db -c "SELECT * FROM visits;"
   ```
4. **Restart the containers** to simulate a system shutdown:
   ```bash
   docker compose down
   docker compose up -d
   ```
5. **Verify data is still present** after the reboot:
   ```bash
   docker compose exec db psql -U postgres -d postgres_db -c "SELECT * FROM visits;"
   ```
   The previously logged visits will be displayed, proving that the volume storage persists.

## Stretch Goals (Optional)

### 1. Redis Integration
We added a Redis container (`redis_cache`) using the `redis:7-alpine` image and integrated health check verification into the Flask app. A connection ping is sent whenever GET `/status` is called, returning `"redis_status": "ok"` in the JSON payload when Redis is fully functional.

### 2. PostgreSQL Indexing (EXPLAIN ANALYZE)
We added a B-tree index on the `visited_at` column of the `visits` table to optimize queries filtering by timestamp:
```sql
CREATE INDEX idx_visits_visited_at ON visits (visited_at);
```

#### Performance Comparison (Benchmarking on 10,000 seeded rows)
To test performance, we seeded the table with 10,000 random entries:
```sql
INSERT INTO visits (visited_at)
SELECT NOW() - (random() * interval '30 days')
FROM generate_series(1, 10000);
```

We then ran a timestamp-filtered query plan before and after dropping the index:

* **With Index (Index Scan)**:
  ```sql
  EXPLAIN ANALYZE SELECT * FROM visits WHERE visited_at > NOW() - interval '1 minute';
  ```
  **Output Plan**:
  ```
  Index Scan using idx_visits_visited_at on visits  (cost=0.29..8.30 rows=1 width=12) (actual time=0.009..0.009 rows=0 loops=1)
    Index Cond: (visited_at > (now() - '00:01:00'::interval))
  Planning Time: 0.854 ms
  Execution Time: 0.054 ms
  ```

* **Without Index (Sequential Scan)**:
  ```sql
  DROP INDEX idx_visits_visited_at;
  EXPLAIN ANALYZE SELECT * FROM visits WHERE visited_at > NOW() - interval '1 minute';
  ```
  **Output Plan**:
  ```
  Seq Scan on visits  (cost=0.00..230.00 rows=1 width=12) (actual time=0.499..0.499 rows=0 loops=1)
    Filter: (visited_at > (now() - '00:01:00'::interval))
    Rows Removed by Filter: 10000
  Planning Time: 0.455 ms
  Execution Time: 0.526 ms
  ```

**Verdict**: The query execution time dropped from **0.526 ms** (Sequential Scan) to **0.054 ms** (Index Scan), providing a **~10x speedup** on a dataset of 10,000 rows.

## Local Development (Without Docker)

Install dependencies:
```bash
pip install -r requirements.txt
```

Run tests:
```bash
python -m unittest test_app.py
```
*(Note: Tests use mocked database and Redis modules and do not require running instances).*


