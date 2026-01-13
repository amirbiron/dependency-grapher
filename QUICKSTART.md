# Quick Start Guide 🚀

## התקנה (3 דקות)

```bash
# 1. פתח את התיקייה
cd dependency-grapher

# 2. צור סביבה וירטואלית
python -m venv venv

# 3. הפעל את הסביבה
source venv/bin/activate  # Linux/Mac
# או
venv\Scripts\activate  # Windows

# 4. התקן תלויות
pip install -r requirements.txt
```

## בדיקה ראשונה (1 דקה)

```bash
# בדוק שהכל עובד - נתח את הפרויקט עצמו
python test_basic.py
```

אמור להדפיס:
```
✓ Analysis complete!
  Total files: 8
  Valid files: 8
  Total imports: 25

✓ Blast Radius test:
  File: ast_parser.py
  Total affected: 3
  Risk: 23.5/100

✓ All tests passed!
```

## ניתוח ראשון של CodeBot (2 דקות)

```bash
# נתח את CodeBot
python main.py /path/to/CodeBot

# או עם קובץ ספציפי
python main.py /path/to/CodeBot --file database/manager.py

# או ייצוא ל-JSON
python main.py /path/to/CodeBot --export codebot_analysis.json
```

## דוגמה קצרה בקוד

```python
from pathlib import Path
from analyzer import DependencyAnalyzer

# יצירת analyzer
analyzer = DependencyAnalyzer(Path("/path/to/CodeBot"))

# ניתוח
result = analyzer.analyze()

print(f"✓ Analyzed {result.total_files} files")

# Blast Radius
blast = analyzer.get_blast_radius("database/manager.py")
print(f"⚠️  If you change database/manager.py:")
print(f"   {blast.total_affected} files will be affected!")

# Top 5 riskiest files
for risk_file in result.top_risk_files[:5]:
    print(f"🔴 {risk_file['file_path']}: {risk_file['risk_score']}/100")
```

## מה הלאה?

- קרא את `README.md` לתיעוד מלא
- בדוק את `analyzer/` כדי להבין איך זה עובד
- רוץ על הפרויקטים שלך!

---

**זמן התחלה כולל: ~6 דקות** ⏱️
