import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    """Returns a connection to the PostgreSQL database."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(DATABASE_URL)

def log_visit():
    """Inserts a new visit entry into the visits table."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO visits (visited_at) VALUES (DEFAULT);")
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def get_status():
    """Checks the health of the database connection.
    
    Returns:
        "ok" if database is healthy, "error" otherwise.
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        return "ok"
    except Exception:
        return "error"
    finally:
        if conn:
            conn.close()
