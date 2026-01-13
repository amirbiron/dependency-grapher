# Dependency Grapher API Documentation

REST API לניתוח תלויות בפרויקטי Python.

---

## Base URL

```
Development: http://localhost:5000
Production: https://your-app.onrender.com
```

---

## Authentication

כרגע אין authentication. בעתיד ניתן להוסיף API keys או JWT.

---

## Endpoints

### 1. Health Check

**GET** `/health`

בדיקת תקינות השרת.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-13T10:30:00Z",
  "version": "0.1.0"
}
```

---

### 2. API Health Check

**GET** `/api/health`

בדיקת תקינות API + MongoDB.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-01-13T10:30:00Z"
}
```

---

### 3. Start Analysis

**POST** `/api/analyze`

התחלת ניתוח פרויקט חדש.

**Request Body:**
```json
{
  "repo_url": "https://github.com/user/repo",
  "branch": "main",          // optional, default: "main"
  "skip_stdlib": true        // optional, default: true
}
```

**Response (202 Accepted):**
```json
{
  "analysis_id": "a1b2c3d4e5f6g7h8",
  "status": "pending",
  "message": "Analysis started successfully"
}
```

**Error (400 Bad Request):**
```json
{
  "error": "Bad Request",
  "message": "Invalid repository URL"
}
```

---

### 4. Get Analysis Status

**GET** `/api/analysis/{analysis_id}`

קבלת סטטוס ומידע על ניתוח.

**Response:**
```json
{
  "analysis_id": "a1b2c3d4e5f6g7h8",
  "repo_url": "https://github.com/user/repo",
  "branch": "main",
  "status": "complete",      // pending | processing | complete | error
  "progress": 100,           // 0-100
  "progress_message": "Analysis complete",
  "created_at": "2025-01-13T10:00:00Z",
  "updated_at": "2025-01-13T10:05:00Z",
  "completed_at": "2025-01-13T10:05:00Z",
  "summary": {
    "total_files": 150,
    "valid_files": 148,
    "total_imports": 542,
    ...
  }
}
```

**Status Values:**
- `pending`: ממתין להתחלה
- `processing`: בתהליך ניתוח
- `complete`: הושלם בהצלחה
- `error`: שגיאה בניתוח

---

### 5. Get Graph Data

**GET** `/api/analysis/{analysis_id}/graph`

קבלת הגרף המלא.

**Query Parameters:**
- `format`: `cytoscape` (default) או `networkx`

**Response (Cytoscape format):**
```json
{
  "elements": {
    "nodes": [
      {
        "data": {
          "id": "/path/to/file.py",
          "label": "file.py",
          "full_path": "myapp/file.py",
          "lines": 150,
          "complexity": 23.5,
          "type": "module"
        }
      }
    ],
    "edges": [
      {
        "data": {
          "id": "source-target",
          "source": "/path/to/source.py",
          "target": "/path/to/target.py",
          "type": "from",
          "is_relative": false
        }
      }
    ]
  }
}
```

---

### 6. Get Blast Radius

**GET** `/api/analysis/{analysis_id}/blast-radius/{file_path}`

חישוב Blast Radius לקובץ ספציפי.

**Example:**
```
GET /api/analysis/abc123/blast-radius/database/manager.py
```

**Response:**
```json
{
  "file_path": "database/manager.py",
  "direct_dependents": [
    "webapp/app.py",
    "api/routes.py"
  ],
  "indirect_dependents": [
    "bot/main.py",
    "scripts/migrate.py"
  ],
  "total_affected": 23,
  "max_depth": 3,
  "risk_score": 87.3,
  "risk_level": "high"
}
```

**Risk Levels:**
- `low`: < 20
- `medium`: 20-50
- `high`: 50-80
- `critical`: > 80

---

### 7. Get Top Risk Files

**GET** `/api/analysis/{analysis_id}/risk-files`

קבלת הקבצים המסוכנים ביותר.

**Query Parameters:**
- `limit`: מספר תוצאות (default: 10)

**Response:**
```json
{
  "risk_files": [
    {
      "file_path": "database/manager.py",
      "risk_score": 87.3,
      "risk_level": "high",
      "blast_radius": 23,
      "risk_factors": [
        "High blast radius: 23 files affected",
        "Unstable: instability=0.82"
      ]
    }
  ],
  "total": 45
}
```

---

### 8. Get Project Metrics

**GET** `/api/analysis/{analysis_id}/metrics`

קבלת מטריקות הפרויקט.

**Response:**
```json
{
  "graph_stats": {
    "total_nodes": 150,
    "total_edges": 340,
    "avg_dependencies": 2.3,
    "avg_dependents": 2.3,
    "circular_dependencies": 2,
    "density": 0.015
  },
  "project_metrics": {
    "total_files": 150,
    "avg_blast_radius": 5.2,
    "avg_instability": 0.45,
    "high_risk_files": 8,
    "hub_files": 5
  },
  "circular_dependencies": [
    ["file1.py", "file2.py", "file3.py"]
  ]
}
```

---

### 9. Get Files List

**GET** `/api/analysis/{analysis_id}/files`

רשימת כל הקבצים בפרויקט.

**Query Parameters:**
- `search`: חיפוש לפי שם
- `risk_level`: סינון לפי רמת סיכון

**Response:**
```json
{
  "files": [
    {
      "path": "database/manager.py",
      "name": "manager.py",
      "lines": 150,
      "complexity": 23.5,
      "type": "module"
    }
  ],
  "total": 150
}
```

---

### 10. Delete Analysis

**DELETE** `/api/analysis/{analysis_id}`

מחיקת ניתוח.

**Response:**
```json
{
  "message": "Analysis deleted successfully"
}
```

---

### 11. List Analyses

**GET** `/api/analyses`

רשימת כל הניתוחים.

**Query Parameters:**
- `limit`: מספר תוצאות (default: 20)
- `offset`: offset (default: 0)
- `status`: סינון לפי סטטוס

**Response:**
```json
{
  "analyses": [
    {
      "analysis_id": "abc123",
      "repo_url": "https://github.com/user/repo",
      "status": "complete",
      "created_at": "2025-01-13T10:00:00Z"
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

---

## Error Responses

כל השגיאות מחזירות JSON בפורמט:

```json
{
  "error": "Error Type",
  "message": "Error description",
  "status_code": 400
}
```

**Common Error Codes:**
- `400 Bad Request`: פרמטרים לא תקינים
- `404 Not Found`: ניתוח לא נמצא
- `500 Internal Server Error`: שגיאת שרת

---

## Rate Limiting

כרגע אין rate limiting. בעתיד ניתן להוסיף.

---

## Examples

### Python Example

```python
import requests

BASE_URL = "http://localhost:5000"

# התחלת ניתוח
response = requests.post(f"{BASE_URL}/api/analyze", json={
    "repo_url": "https://github.com/user/repo",
    "branch": "main"
})

analysis_id = response.json()["analysis_id"]
print(f"Analysis started: {analysis_id}")

# המתנה להשלמה
import time
while True:
    status = requests.get(f"{BASE_URL}/api/analysis/{analysis_id}").json()
    
    if status["status"] == "complete":
        print("Analysis complete!")
        break
    
    print(f"Progress: {status['progress']}%")
    time.sleep(2)

# קבלת הגרף
graph = requests.get(f"{BASE_URL}/api/analysis/{analysis_id}/graph").json()
print(f"Nodes: {len(graph['elements']['nodes'])}")

# Blast Radius
blast = requests.get(
    f"{BASE_URL}/api/analysis/{analysis_id}/blast-radius/myapp/core.py"
).json()
print(f"Blast Radius: {blast['total_affected']} files")
```

### cURL Examples

```bash
# Start analysis
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo"}'

# Get status
curl http://localhost:5000/api/analysis/abc123

# Get graph
curl http://localhost:5000/api/analysis/abc123/graph

# Get blast radius
curl http://localhost:5000/api/analysis/abc123/blast-radius/myapp/core.py

# Get risk files
curl http://localhost:5000/api/analysis/abc123/risk-files?limit=5
```

---

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-api.txt

# Set environment variables
cp .env-api.example .env
# Edit .env with your settings

# Run server
python api/run.py
```

### Production (Render)

1. העלה לGitHub
2. צור Web Service בRender
3. הגדר Environment Variables:
   - `MONGODB_URI`
   - `SECRET_KEY`
4. Deploy אוטומטית מGitHub

---

## WebSocket Support (Future)

בעתיד ניתן להוסיף WebSocket לעדכונים בזמן אמת:

```python
from flask_socketio import SocketIO

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('subscribe_analysis')
def handle_subscribe(analysis_id):
    join_room(analysis_id)

# בתוך המשימה:
socketio.emit('progress', {
    'progress': 50,
    'message': 'Analyzing...'
}, room=analysis_id)
```

---

**Created by Amir Haim** 🚀
