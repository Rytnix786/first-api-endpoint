# first-api-endpoint

A minimal Flask backend server with two API endpoints.

## Installation

Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

Start the Flask application:
```bash
python app.py
```

## API Endpoints

### 1. Hello World
Returns a simple welcome message.
```bash
curl http://127.0.0.1:5000/
```

### 2. Status Check
Returns the current server status and UTC ISO timestamp.
```bash
curl http://127.0.0.1:5000/status
```
