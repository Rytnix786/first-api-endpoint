from datetime import datetime, timezone
from flask import Flask, jsonify

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(port=5000)
