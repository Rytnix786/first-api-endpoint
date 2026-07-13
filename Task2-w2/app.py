from datetime import datetime, timezone
from flask import Flask, jsonify
import db

app = Flask(__name__)

# GET / returns a simple hello message
@app.route('/')
def hello():
    db.log_visit()
    return jsonify({"message": "Hello, World!"})

# GET /status returns health status and current ISO timestamp
@app.route('/status')
def status():
    db_status = db.get_status()
    return jsonify({
        "status": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
