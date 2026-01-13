# Dependency Grapher Frontend

React frontend עם Cytoscape.js לויזואליזציה של תלויות.

---

## 🚀 Quick Start

### התקנה

```bash
cd frontend
npm install
```

### הרצה

```bash
# Development
npm start

# Production build
npm run build
```

האפליקציה תיפתח ב-`http://localhost:3000`

---

## 🏗️ מבנה

```
src/
├── components/          # React components
│   ├── AnalysisForm     # טופס התחלת ניתוח
│   ├── GraphViewer      # תצוגת הגרף (Cytoscape)
│   ├── FileDetails      # פרטי קובץ
│   ├── RiskDashboard    # דשבורד סיכונים
│   ├── ProgressBar      # Progress bar
│   └── ProjectStats     # סטטיסטיקות פרויקט
│
├── hooks/              # Custom hooks
│   └── useAnalysis     # ניהול ניתוחים
│
├── services/           # API client
│   └── api.js          # Axios client
│
└── styles/             # CSS files
    └── App.css         # Global styles
```

---

## 🎨 Features

### Graph Viewer
- ✅ Cytoscape.js visualization
- ✅ 4 layouts (Force, Circle, Grid, Hierarchy)
- ✅ Zoom/Pan controls
- ✅ Node highlighting
- ✅ Export PNG
- ✅ Interactive tooltips

### File Details
- ✅ Code statistics
- ✅ Blast radius calculation
- ✅ Risk scoring
- ✅ Dependents list

### Risk Dashboard
- ✅ Top 10 risky files
- ✅ Risk level badges
- ✅ Click to highlight

### Analysis
- ✅ Real-time progress
- ✅ Error handling
- ✅ Repository validation

---

## 🔧 Configuration

### API URL

ברירת מחדל: `http://localhost:5000`

לשינוי, צור `.env`:

```bash
REACT_APP_API_URL=https://your-api-url.com
```

### Proxy

ה-`package.json` כבר מוגדר עם proxy:

```json
"proxy": "http://localhost:5000"
```

זה מאפשר לעבוד עם ה-API בלי CORS issues בפיתוח.

---

## 📦 Dependencies

### Main
- **React 18** - UI framework
- **Cytoscape.js** - Graph visualization
- **Axios** - HTTP client
- **Lucide React** - Icons

### Layouts
- **cose-bilkent** - Force-directed layout

---

## 🎯 Usage

### 1. התחלת ניתוח

```jsx
// הזן URL
https://github.com/user/repo

// לחץ "Start Analysis"
// המתן להשלמה (~30 שניות)
```

### 2. צפייה בגרף

```
- Zoom: גלגלת העכבר
- Pan: גרור
- Select: לחץ על צומת
```

### 3. Blast Radius

```
- לחץ על קובץ
- הקבצים המושפעים יסומנו בצהוב
- פרטים בפאנל הימני
```

---

## 🎨 Customization

### Colors

ערוך את `App.css`:

```css
:root {
  --accent-primary: #4f93ff;
  --bg-primary: #0f1419;
  /* ... */
}
```

### Graph Style

ערוך את `GraphViewer.jsx` → `getGraphStyle()`:

```javascript
{
  selector: 'node',
  style: {
    'background-color': '#4f93ff',
    'width': '30px',
    // ...
  }
}
```

---

## 🐛 Troubleshooting

### "Proxy error"
- ודא שה-API server רץ (`python api/run.py`)
- בדוק את ה-proxy ב-`package.json`

### "Failed to load graph"
- בדוק Network tab ב-DevTools
- ודא שה-analysis_id נכון
- בדוק שהניתוח הושלם (`status: "complete"`)

### גרף לא מוצג
- פתח Console לשגיאות
- ודא שיש `elements.nodes` בנתונים
- נסה layout אחר

---

## 📱 Responsive

האפליקציה responsive למובייל:
- Sidebar מתקפל
- Controls מותאמים
- Touch-friendly

---

## 🚀 Production Build

```bash
# Build
npm run build

# Serve
npx serve -s build
```

או deploy ל-Vercel/Netlify:

```bash
# Vercel
vercel --prod

# Netlify
netlify deploy --prod
```

---

## 🔮 Future Features

- [ ] WebSocket לעדכונים בזמן אמת
- [ ] Search & filters
- [ ] Dark/Light theme toggle
- [ ] Export options (JSON, PDF)
- [ ] Keyboard shortcuts
- [ ] Multiple graph views
- [ ] Collaborative features

---

**נוצר על ידי אמיר חיים** 🚀
