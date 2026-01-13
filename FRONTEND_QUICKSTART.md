# Frontend Quick Start 🎨

התחלה מהירה עם ה-React Frontend.

---

## התקנה (5 דקות)

### 1. התקן Node.js

צריך Node.js 16+ ו-npm:

```bash
# בדוק גרסה
node --version  # v16.0.0+
npm --version   # 8.0.0+
```

[הורד Node.js](https://nodejs.org/)

### 2. התקן Dependencies

```bash
cd frontend
npm install
```

זה יתקין:
- React 18
- Cytoscape.js
- Axios
- Lucide icons

### 3. הרץ את ה-API

בטרמינל נפרד:

```bash
cd ..
python api/run.py
```

### 4. הרץ את ה-Frontend

```bash
npm start
```

הדפדפן ייפתח אוטומטית ב-`http://localhost:3000`

---

## שימוש ראשון (2 דקות)

### 1. הזן Repository URL

```
https://github.com/psf/requests
```

### 2. לחץ "Start Analysis"

תראה progress bar:
```
⏳ 50% - Analyzing file 75/150...
```

### 3. צפה בגרף!

אחרי ~30 שניות הגרף יופיע.

---

## בדיקה מהירה

אם אין לך API server:

```bash
# במקום הAPI, השתמש במוק
cd frontend/src
# ערוך api.js והוסף:
# const MOCK_MODE = true;
```

---

## Controls

### בגרף:

| פעולה | איך |
|-------|-----|
| Zoom In | גלגלת למעלה |
| Zoom Out | גלגלת למטה |
| Pan | גרור עם העכבר |
| Fit | לחצן Maximize |
| Export | לחצן Download |

### Layouts:

בחר מהתפריט למטה-ימין:
- **Force Directed** (ברירת מחדל)
- **Circle**
- **Grid**
- **Hierarchy**

---

## דוגמה מלאה

```bash
# Terminal 1: API
cd dependency-grapher
python api/run.py

# Terminal 2: Frontend
cd dependency-grapher/frontend
npm install
npm start

# Terminal 3: MongoDB (אם local)
mongod

# Browser
http://localhost:3000
```

---

## Environment Variables

צור `.env` בתיקיית `frontend/`:

```bash
REACT_APP_API_URL=http://localhost:5000
```

---

## Troubleshooting

### Port 3000 תפוס
```bash
# Linux/Mac
lsof -ti:3000 | xargs kill

# או שנה את הפורט
PORT=3001 npm start
```

### API לא מגיב
```bash
# בדוק שהשרת רץ
curl http://localhost:5000/health

# צפוי:
# {"status": "healthy"}
```

### גרף לא נטען
1. פתח DevTools (F12)
2. Network tab
3. חפש שגיאות אדומות
4. Console tab לשגיאות JavaScript

---

## Build לייצור

```bash
npm run build

# זה יוצר build/ תיקייה
# להעלות לVercel/Netlify/Render
```

---

## הרצה עם Docker (אופציונלי)

```dockerfile
# Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "start"]
```

```bash
docker build -t dep-grapher-frontend .
docker run -p 3000:3000 dep-grapher-frontend
```

---

## Deploy ל-Vercel

```bash
npm install -g vercel
vercel --prod
```

הגדר Environment Variable:
```
REACT_APP_API_URL=https://your-api.onrender.com
```

---

## Features להתנסות

### 1. בחר קובץ
לחץ על צומת בגרף → רואה פרטים + Blast Radius

### 2. Risk Dashboard
לחץ על "Risk Files" → רשימת הקבצים המסוכנים

### 3. Highlight
כשבוחר קובץ, כל התלויים מסומנים בצהוב

### 4. Export
לחצן Download → שמור PNG של הגרף

---

## Next Steps

1. נסה repos שונים
2. שחק עם ה-layouts
3. התאם צבעים ב-`App.css`
4. הוסף features חדשים!

---

**זמן התחלה: ~7 דקות** ⏱️

בהצלחה! 🎉
