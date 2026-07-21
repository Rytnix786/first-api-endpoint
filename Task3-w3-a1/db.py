import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()

    # Seed 3 example tasks if the table is empty
    cursor.execute('SELECT COUNT(*) AS count FROM tasks')
    row = cursor.fetchone()
    if row['count'] == 0:
        seed_tasks = [
            ("Buy groceries", False),
            ("Read a book", True),
            ("Complete assignment", False)
        ]
        cursor.executemany(
            'INSERT INTO tasks (title, done) VALUES (?, ?)',
            seed_tasks
        )
        conn.commit()
    conn.close()

def get_all_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, done FROM tasks')
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "title": row["title"], "done": bool(row["done"])} for row in rows]

def get_task_by_id(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, done FROM tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

def create_task(title, done=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (title, done) VALUES (?, ?)', (title, done))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "title": title, "done": bool(done)}

def update_task(task_id, title=None, done=None):
    existing = get_task_by_id(task_id)
    if existing is None:
        return None
    
    new_title = title if title is not None else existing['title']
    new_done = done if done is not None else existing['done']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE tasks SET title = ?, done = ? WHERE id = ?',
        (new_title, new_done, task_id)
    )
    conn.commit()
    conn.close()
    return {"id": task_id, "title": new_title, "done": bool(new_done)}

def delete_task(task_id):
    existing = get_task_by_id(task_id)
    if existing is None:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return True



