# Dependency Grapher 🕸️

מנתח תלויות מתקדם לפרויקטי Python. בנוי עם AST parsing, NetworkX, ו-Cytoscape.js.

## 🎯 מה זה עושה?

בפרויקטים גדולים (כמו CodeBot עם 65,000 שורות), קשה לזכור איזה מודול משפיע על מה. 
**Dependency Grapher** מייצר **מפה חיה ואינטראקטיבית** של הקשרים בין הקבצים בפרויקט שלך.

### הפיצ'ר הקטלני: Blast Radius

אתה לוחץ על קובץ במפה, והוא מראה לך את **"רדיוס הפיצוץ"** - כלומר, אילו חלקים בקוד תלויים בו ועלולים להישבר אם תשנה אותו.

## 🚀 התקנה מהירה

```bash
# שכפול או יצירת תיקיית הפרויקט
cd dependency-grapher

# יצירת סביבה וירטואלית
python -m venv venv
source venv/bin/activate  # Linux/Mac
# או
venv\Scripts\activate  # Windows

# התקנת תלויות
pip install -r requirements.txt
```

## 📖 שימוש בסיסי

### 1. ניתוח פרויקט שלם

```bash
python main.py /path/to/your/project
```

פלט לדוגמה:
```
==============================================================
Analyzing: /home/user/my_project
==============================================================

Progress: 150/150 (100.0%)

==============================================================
Analysis Summary
==============================================================
Total files: 150
Valid files: 148
Error files: 2
Total imports: 542
Total functions: 1,234
Total classes: 89

==============================================================
Top 10 Highest Risk Files
==============================================================

1. database/manager.py
   Risk: 87.3/100 (high)
   Blast Radius: 23 files
   
2. api/routes.py
   Risk: 72.1/100 (high)
   Blast Radius: 15 files
...
```

### 2. ניתוח קובץ ספציפי

```bash
python main.py /path/to/project --file database/manager.py
```

פלט:
```
==============================================================
Detailed Analysis: database/manager.py
==============================================================

Risk Level: HIGH
Risk Score: 87.3/100

--- Blast Radius ---
Direct dependents: 12
Indirect dependents: 11
Total affected: 23

Direct dependents:
  • webapp/app.py
  • bot/handlers/code.py
  • api/routes/snippets.py
  ...

--- Stability ---
Afferent coupling (incoming): 12
Efferent coupling (outgoing): 3
Instability: 0.20
Category: stable

--- Recommendations ---
  💡 Critical hub - add comprehensive tests
  💡 Consider caching to reduce coupling
```

### 3. ייצוא ל-JSON

```bash
python main.py /path/to/project --export results.json
```

יצירת קובץ JSON עם כל הנתונים.

### 4. ייצוא ל-Cytoscape (לצד הלקוח)

```bash
python main.py /path/to/project --cytoscape graph.json
```

זה הפורמט שה-Frontend צריך כדי להציג את הגרף!

## 🔧 שימוש Programmatic

```python
from pathlib import Path
from analyzer import DependencyAnalyzer

# יצירת analyzer
analyzer = DependencyAnalyzer(Path("/path/to/project"))

# ניתוח
result = analyzer.analyze()

print(f"Analyzed {result.total_files} files")
print(f"Found {len(result.circular_dependencies)} circular dependencies")

# Blast Radius לקובץ ספציפי
blast_radius = analyzer.get_blast_radius("myapp/core.py")
print(f"Total affected: {blast_radius.total_affected}")
print(f"Risk level: {blast_radius.risk_level}")

# ניתוח סיכון מקיף
risk = analyzer.get_file_risk("myapp/core.py")
print(f"Risk score: {risk.risk_score}/100")
for factor in risk.risk_factors:
    print(f"  - {factor}")

# ייצוא
analyzer.export_to_json("results.json")
analyzer.export_for_cytoscape("graph.json")
```

## 📊 המטריקות שמחושבות

### 1. Blast Radius
- **Direct Dependents**: קבצים שמייבאים ישירות מהקובץ
- **Indirect Dependents**: קבצים שתלויים בצורה עקיפה
- **Total Affected**: כמה קבצים סה"כ ישברו
- **Max Depth**: אורך השרשרת הארוכה ביותר

### 2. Stability Metrics
- **Afferent Coupling (Ce)**: כמה קבצים תלויים בקובץ הזה
- **Efferent Coupling (Ca)**: כמה קבצים הקובץ תלוי בהם
- **Instability (I)**: `Ca / (Ca + Ce)` - 0 = יציב מאוד, 1 = לא יציב

### 3. Risk Score
ציון משוקלל (0-100) המבוסס על:
- Blast Radius (50%)
- Stability (30%)
- Complexity (20%)

### 4. Graph Metrics
- **Hub Files**: קבצים שהרבה קבצים תלויים בהם
- **Entry Points**: קבצים עם `__main__`
- **Circular Dependencies**: מעגלי תלויות
- **Isolated Nodes**: קבצים מבודדים

## 🏗️ ארכיטקטורה

```
analyzer/
├── ast_parser.py       # ניתוח AST
├── resolver.py         # פתרון imports
├── graph_builder.py    # בניית גרף NetworkX
├── metrics.py          # חישוב Blast Radius
└── core.py            # המנוע המרכזי
```

### איך זה עובד?

1. **AST Parser** קורא קובץ Python ומחלץ imports, functions, classes
2. **Import Resolver** פותר את הנתיבים האמיתיים של imports (כולל relative imports)
3. **Graph Builder** בונה גרף מכוון עם NetworkX
4. **Metrics Calculator** מחשב Blast Radius, Stability, Risk Score

## 🎨 Frontend (Cytoscape.js)

הגרף שנוצר יכול להיות מוצג ב-Frontend עם Cytoscape.js:

```javascript
fetch('graph.json')
  .then(res => res.json())
  .then(data => {
    const cy = cytoscape({
      container: document.getElementById('cy'),
      elements: data.elements,
      style: [ /* ... */ ]
    });
    
    // Click על צומת
    cy.on('tap', 'node', function(evt) {
      const node = evt.target;
      // הצג Blast Radius
      highlightBlastRadius(node);
    });
  });
```

## 🔍 דוגמאות שימוש

### מציאת Circular Dependencies

```python
analyzer = DependencyAnalyzer("my_project")
result = analyzer.analyze()

for cycle in result.circular_dependencies:
    print("Found cycle:")
    for file in cycle:
        print(f"  → {file}")
    print(f"  → {cycle[0]}")
```

### מציאת Hub Files (קבצים קריטיים)

```python
graph = analyzer.get_graph()
in_degrees = dict(graph.in_degree())

hubs = [(f, deg) for f, deg in in_degrees.items() if deg > 10]
hubs.sort(key=lambda x: x[1], reverse=True)

for file, degree in hubs[:5]:
    print(f"{file}: {degree} dependents")
```

### מציאת מסלול בין שני קבצים

```python
path = analyzer.find_path_between("app.py", "database/models.py")
if path:
    print(" → ".join(path))
```

## ⚙️ הגדרות מתקדמות

### config.py

```python
class Config:
    MAX_FILE_SIZE = 1024 * 1024  # 1MB
    SKIP_DIRS = {"__pycache__", ".venv", "node_modules"}
    CACHE_TTL = 3600 * 24  # 24 hours
```

### דילוג על תיקיות מסוימות

```python
analyzer = DependencyAnalyzer("my_project")
result = analyzer.analyze(skip_dirs={"tests", "docs", "migrations"})
```

## 🐛 Troubleshooting

### "SyntaxError" בזמן ניתוח
קבצים עם שגיאות syntax ידלגו אוטומטית. בדוק את `result.error_files`.

### Imports לא נפתרים
- ודא שהפרויקט הוא Python package תקין
- בדוק את `__init__.py` בתיקיות
- הפעל עם `--verbose` לראות logs מפורטים

### הגרף גדול מדי
השתמש ב-clustering או סינון:
```python
# הצג רק קבצים מתיקייה מסוימת
subgraph = builder.visualize_subgraph("database/manager.py", depth=2)
```

## 📝 TODO / רעיונות להרחבה

- [ ] תמיכה ב-JavaScript/TypeScript
- [ ] אינטגרציה עם GitHub Actions
- [ ] UI מלא עם React
- [ ] Real-time analysis (watch mode)
- [ ] AI recommendations למבנה טוב יותר

## 🤝 תרומה

Pull requests מתקבלים בברכה!

## 📄 רישיון

MIT License

---

**נוצר על ידי אמיר חיים** 🚀
