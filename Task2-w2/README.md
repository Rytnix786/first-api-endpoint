# first-api-endpoint

A minimal Flask backend server with two API endpoints, containerized and backed by a PostgreSQL database.

## Running with Docker Compose

1. Make sure you have Docker running in the background.
2. In the `Task1-w1` directory, copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Start the application and database services:
   ```bash
   docker compose up --build
   ```
   This will spin up:
   - A PostgreSQL 16 database container (`postgres_db`).
   - The Flask app container (`flask_app`) which will run once the database is healthy.
   - The DB schema will be automatically created on the first run via `init.sql`.

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
Returns the current server and database health status along with a UTC ISO timestamp.
```bash
curl http://127.0.0.1:5000/status
```
Expected output (if DB is healthy):
```json
{"status": "ok", "timestamp": "2026-07-13T09:15:00Z"}
```
If the database connection fails, `status` will be `"error"`.

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

## Local Development (Without Docker)

Install dependencies:
```bash
pip install -r requirements.txt
```

Run tests:
```bash
python -m unittest test_app.py
```
*(Note: Tests use mocked database queries and do not require a running PostgreSQL instance).*

