from datetime import datetime, timezone
from flask import Flask, jsonify, request
import db

app = Flask(__name__)

# Initialize database table and initial seed data
db.init_db()

# GET / returns a simple hello message
@app.route('/')
def hello():
    return jsonify({"message": "Hello, World!"})

# GET /status returns health status and current ISO timestamp
@app.route('/status')
def status():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    })

# GET /tasks - Return list of all tasks
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = db.get_all_tasks()
    return jsonify(tasks), 200

# POST /tasks - Create a new task in SQLite
@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    if not title or not str(title).strip():
        return jsonify({"error": "Title is required"}), 400
    
    done = bool(data.get('done', False))
    new_task = db.create_task(str(title).strip(), done)
    return jsonify(new_task), 201

# GET /tasks/<id> - Return single task by ID or 404
@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = db.get_task_by_id(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task), 200

# PUT /tasks/<id> - Update existing task in SQLite
@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    done = data.get('done')

    if title is not None and not str(title).strip():
        return jsonify({"error": "Title cannot be empty"}), 400

    updated = db.update_task(
        task_id,
        title=str(title).strip() if title is not None else None,
        done=bool(done) if done is not None else None
    )
    if updated is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(updated), 200

# DELETE /tasks/<id> - Delete task by ID from SQLite
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    success = db.delete_task(task_id)
    if not success:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Task deleted successfully"}), 200

if __name__ == '__main__':
    app.run(port=5000)
