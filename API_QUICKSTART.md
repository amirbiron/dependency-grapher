# API Quick Start Guide 🚀

התחלה מהירה עם Dependency Grapher API.

---

## התקנה (5 דקות)

### 1. התקן Dependencies

```bash
# Base dependencies
pip install -r requirements.txt

# API dependencies
pip install -r requirements-api.txt
```

### 2. הגדר MongoDB

**אופציה A: Local MongoDB**
```bash
# Ubuntu/Debian
sudo apt install mongodb
sudo systemctl start mongodb

# macOS
brew install mongodb-community
brew services start mongodb-community
```

**אופציה B: MongoDB Atlas (Cloud - מומלץ)**
1. צור חשבון ב-[MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. צור Cluster חינמי
3. קבל את ה-Connection String
4. הוסף ל-.env

### 3. הגדר Environment Variables

```bash
# העתק את הדוגמה
cp .env-api.example .env

# ערוך את .env
nano .env
```

ערוך:
```bash
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
DATABASE_NAME=dependency_grapher
```

### 4. הרץ את השרת

```bash
python api/run.py
```

אמור לראות:
```
╔════════════════════════════════════════╗
║  Dependency Grapher API Server         ║
╠════════════════════════════════════════╣
║  Running on: http://localhost:5000     ║
║  Debug mode: True                      ║
╚════════════════════════════════════════╝
```

---

## בדיקה ראשונה (2 דקות)

### בדוק שהשרת עובד

```bash
curl http://localhost:5000/health
```

צריך להחזיר:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "0.1.0"
}
```

### התחל ניתוח

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/psf/requests"
  }'
```

תקבל:
```json
{
  "analysis_id": "a1b2c3d4e5f6g7h8",
  "status": "pending",
  "message": "Analysis started successfully"
}
```

### בדוק סטטוס

```bash
# שנה את analysis_id לזה שקיבלת
curl http://localhost:5000/api/analysis/a1b2c3d4e5f6g7h8
```

המתן עד ש-`status` יהיה `complete`.

### קבל את הגרף

```bash
curl http://localhost:5000/api/analysis/a1b2c3d4e5f6g7h8/graph
```

---

## Python Client Example

```python
import requests
import time

BASE_URL = "http://localhost:5000"

# 1. התחל ניתוח
print("Starting analysis...")
response = requests.post(f"{BASE_URL}/api/analyze", json={
    "repo_url": "https://github.com/psf/requests",
    "branch": "main"
})

analysis_id = response.json()["analysis_id"]
print(f"Analysis ID: {analysis_id}")

# 2. המתן להשלמה
print("Waiting for completion...")
while True:
    status_response = requests.get(f"{BASE_URL}/api/analysis/{analysis_id}")
    status = status_response.json()
    
    if status["status"] == "complete":
        print("✓ Analysis complete!")
        break
    elif status["status"] == "error":
        print(f"✗ Error: {status.get('error')}")
        break
    
    progress = status.get("progress", 0)
    print(f"  Progress: {progress}%")
    time.sleep(2)

# 3. קבל תוצאות
graph = requests.get(f"{BASE_URL}/api/analysis/{analysis_id}/graph").json()
print(f"\nNodes: {len(graph['elements']['nodes'])}")
print(f"Edges: {len(graph['elements']['edges'])}")

# 4. Top risk files
risks = requests.get(f"{BASE_URL}/api/analysis/{analysis_id}/risk-files").json()
print(f"\nTop Risk Files:")
for risk in risks["risk_files"][:5]:
    print(f"  {risk['file_path']}: {risk['risk_score']}/100")
```

---

## JavaScript/Fetch Example

```javascript
const BASE_URL = 'http://localhost:5000';

async function analyzeRepo(repoUrl) {
  // Start analysis
  const response = await fetch(`${BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({repo_url: repoUrl})
  });
  
  const {analysis_id} = await response.json();
  console.log('Analysis ID:', analysis_id);
  
  // Poll for completion
  while (true) {
    const statusResponse = await fetch(
      `${BASE_URL}/api/analysis/${analysis_id}`
    );
    const status = await statusResponse.json();
    
    if (status.status === 'complete') {
      console.log('Analysis complete!');
      break;
    }
    
    console.log(`Progress: ${status.progress}%`);
    await new Promise(r => setTimeout(r, 2000));
  }
  
  // Get graph
  const graphResponse = await fetch(
    `${BASE_URL}/api/analysis/${analysis_id}/graph`
  );
  const graph = await graphResponse.json();
  
  console.log('Nodes:', graph.elements.nodes.length);
  console.log('Edges:', graph.elements.edges.length);
  
  return graph;
}

// Usage
analyzeRepo('https://github.com/psf/requests');
```

---

## Troubleshooting

### "Connection refused"
- ודא שהשרת רץ: `python api/run.py`
- בדוק את הפורט: ברירת מחדל 5000

### "Database error"
- ודא ש-MongoDB רץ
- בדוק את `MONGODB_URI` ב-.env
- נסה: `mongo` או `mongosh` בטרמינל

### "Analysis stays in 'pending'"
- בדוק logs של השרת
- ודא שיש גישה לאינטרנט (לclone repos)
- בדוק שה-repo URL תקין

### "Timeout"
- repos גדולים לוקחים זמן
- ב-Frontend הגדל את ה-timeout של הקריאות ל-API:
  - `REACT_APP_API_TIMEOUT_MS` (ברירת מחדל: 300000)
  - `REACT_APP_GRAPH_TIMEOUT_MS` (ברירת מחדל: 600000)

---

## Next Steps

1. **קרא את [API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - תיעוד מלא
2. **הוסף Frontend** - React + Cytoscape.js
3. **Deploy ל-Render** - ראה [Deploy Guide](#deploy)

---

## Deploy to Render

### 1. העלה לGitHub

```bash
git add .
git commit -m "Add API"
git push origin main
```

### 2. צור Web Service ב-Render

1. לך ל-[Render Dashboard](https://dashboard.render.com/)
2. New → Web Service
3. Connect GitHub repo
4. הגדרות:
   - **Build Command**: `pip install -r requirements.txt && pip install -r requirements-api.txt`
   - **Start Command**: `gunicorn api.app:app --bind 0.0.0.0:$PORT`

### 3. Environment Variables

הוסף ב-Render:
```
MONGODB_URI=mongodb+srv://...
DATABASE_NAME=dependency_grapher
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

### 4. Deploy!

Render יעשה deploy אוטומטית. קבל URL כמו:
```
https://dependency-grapher-api.onrender.com
```

---

## WebSocket Support (Optional)

אם רוצה real-time updates:

```bash
pip install flask-socketio

# ב-api/app.py:
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('subscribe')
def handle_subscribe(analysis_id):
    join_room(analysis_id)
    
# ב-tasks.py:
from api.app import socketio

socketio.emit('progress', {
    'progress': 50
}, room=analysis_id)
```

Frontend:
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:5000');

socket.emit('subscribe', analysis_id);
socket.on('progress', (data) => {
  console.log('Progress:', data.progress);
});
```

---

**זמן התחלה: ~7 דקות** ⏱️

הצלחה! 🎉
