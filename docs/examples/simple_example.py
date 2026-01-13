"""
Simple Programmatic Example - שימוש בסיסי ב-API

דוגמה זו מראה את השימושים הבסיסיים ביותר ב-Dependency Analyzer
"""
from pathlib import Path
from analyzer import DependencyAnalyzer

# ============================================
# דוגמה 1: ניתוח בסיסי
# ============================================

def basic_analysis_example():
    """ניתוח פשוט של פרויקט"""
    
    # יצירת analyzer
    analyzer = DependencyAnalyzer(Path("/path/to/your/project"))
    
    # ניתוח הפרויקט
    result = analyzer.analyze()
    
    # הדפסת תוצאות
    print(f"✅ ניתוח הושלם!")
    print(f"📁 סה\"כ קבצים: {result.total_files}")
    print(f"✓ קבצים תקינים: {result.valid_files}")
    print(f"📦 סה\"כ imports: {result.total_imports}")
    print(f"🔧 סה\"כ פונקציות: {result.total_functions}")
    print(f"📝 סה\"כ מחלקות: {result.total_classes}")


# ============================================
# דוגמה 2: Blast Radius לקובץ ספציפי
# ============================================

def blast_radius_example():
    """חישוב Blast Radius"""
    
    analyzer = DependencyAnalyzer(Path("/path/to/project"))
    analyzer.analyze()
    
    # Blast Radius לקובץ מסוים
    blast = analyzer.get_blast_radius("myapp/core.py")
    
    print(f"\n🎯 Blast Radius עבור myapp/core.py:")
    print(f"   Total affected: {blast.total_affected} קבצים")
    print(f"   Risk level: {blast.risk_level.value}")
    print(f"   Risk score: {blast.risk_score:.1f}/100")
    
    # הצגת תלויים ישירים
    if blast.direct_dependents:
        print(f"\n   תלויים ישירים:")
        for dep in blast.direct_dependents[:5]:  # 5 הראשונים
            print(f"     • {Path(dep).name}")


# ============================================
# דוגמה 3: Top Risk Files
# ============================================

def top_risk_files_example():
    """מציאת הקבצים המסוכנים ביותר"""
    
    analyzer = DependencyAnalyzer(Path("/path/to/project"))
    result = analyzer.analyze()
    
    print(f"\n🔴 10 הקבצים המסוכנים ביותר:")
    print(f"{'='*60}")
    
    for i, risk_file in enumerate(result.top_risk_files[:10], 1):
        print(f"{i}. {risk_file['file_path']}")
        print(f"   Risk: {risk_file['risk_score']}/100 ({risk_file['risk_level']})")
        print(f"   Blast Radius: {risk_file['blast_radius']} files")
        print()


# ============================================
# דוגמה 4: מציאת Circular Dependencies
# ============================================

def circular_dependencies_example():
    """מציאת מעגלי תלויות"""
    
    analyzer = DependencyAnalyzer(Path("/path/to/project"))
    result = analyzer.analyze()
    
    if result.circular_dependencies:
        print(f"\n⚠️  נמצאו {len(result.circular_dependencies)} מעגלי תלויות:")
        
        for i, cycle in enumerate(result.circular_dependencies[:3], 1):
            print(f"\nMycle {i}:")
            for file in cycle:
                print(f"  → {file}")
            print(f"  → {cycle[0]}")  # חזרה להתחלה
    else:
        print(f"\n✅ לא נמצאו מעגלי תלויות!")


# ============================================
# דוגמה 5: ניתוח יחסי קבצים
# ============================================

def file_relationships_example():
    """בדיקת יחסים בין קבצים"""
    
    analyzer = DependencyAnalyzer(Path("/path/to/project"))
    analyzer.analyze()
    
    file = "database/manager.py"
    
    # מי תלוי בקובץ הזה?
    dependents = analyzer.get_file_dependents(file)
    print(f"\n📥 קבצים שתלויים ב-{file}:")
    for dep in dependents[:5]:
        print(f"   • {Path(dep).name}")
    
    # במה הקובץ הזה תלוי?
    dependencies = analyzer.get_file_dependencies(file)
    print(f"\n📤 {file} תלוי ב:")
    for dep in dependencies[:5]:
        print(f"   • {Path(dep).name}")


# ============================================
# דוגמה 6: ייצוא תוצאות
# ============================================

def export_example():
    """ייצוא תוצאות לקבצים"""
    
    analyzer = DependencyAnalyzer(Path("/path/to/project"))
    analyzer.analyze()
    
    # ייצוא ל-JSON
    analyzer.export_to_json("analysis_results.json")
    print(f"✅ יוצא ל-analysis_results.json")
    
    # ייצוא לפורמט Cytoscape (לצד הלקוח)
    analyzer.export_for_cytoscape("graph_data.json")
    print(f"✅ יוצא ל-graph_data.json")


# ============================================
# דוגמה 7: Stability Analysis
# ============================================

def stability_example():
    """ניתוח יציבות של קובץ"""
    
    analyzer = DependencyAnalyzer(Path("/path/to/project"))
    analyzer.analyze()
    
    risk = analyzer.get_file_risk("myapp/core.py")
    
    print(f"\n📊 ניתוח יציבות עבור myapp/core.py:")
    print(f"   Afferent Coupling (Ce): {risk.stability.afferent_coupling}")
    print(f"   Efferent Coupling (Ca): {risk.stability.efferent_coupling}")
    print(f"   Instability (I): {risk.stability.instability:.2f}")
    print(f"   Category: {risk.stability.stability_category}")
    
    if risk.stability.is_stable:
        print(f"   ✅ הקובץ יציב")
    elif risk.stability.is_unstable:
        print(f"   ⚠️  הקובץ לא יציב")


# ============================================
# דוגמה 8: מציאת מסלול בין קבצים
# ============================================

def path_between_files_example():
    """מציאת מסלול תלויות בין שני קבצים"""
    
    analyzer = DependencyAnalyzer(Path("/path/to/project"))
    analyzer.analyze()
    
    source = "webapp/app.py"
    target = "database/models.py"
    
    path = analyzer.find_path_between(source, target)
    
    if path:
        print(f"\n🛤️  מסלול מ-{source} ל-{target}:")
        for i, file in enumerate(path):
            print(f"   {'   ' * i}→ {Path(file).name}")
    else:
        print(f"\n❌ לא נמצא מסלול בין הקבצים")


# ============================================
# דוגמה 9: Progress Callback
# ============================================

def progress_callback_example():
    """שימוש ב-progress callback"""
    
    def show_progress(current, total):
        percent = (current / total) * 100
        bar_length = 40
        filled = int(bar_length * current / total)
        bar = '█' * filled + '-' * (bar_length - filled)
        print(f'\r[{bar}] {percent:.1f}% ({current}/{total})', end='')
    
    analyzer = DependencyAnalyzer(Path("/path/to/project"))
    result = analyzer.analyze(progress_callback=show_progress)
    
    print()  # שורה חדשה
    print(f"✅ הושלם!")


# ============================================
# דוגמה 10: Custom Skip Directories
# ============================================

def custom_skip_example():
    """דילוג על תיקיות מסוימות"""
    
    analyzer = DependencyAnalyzer(Path("/path/to/project"))
    
    # דילוג על tests, docs, migrations
    result = analyzer.analyze(
        skip_dirs={"tests", "docs", "migrations", "scripts"}
    )
    
    print(f"✅ ניתוח הושלם (ללא tests/docs/migrations)")
    print(f"   Total files: {result.valid_files}")


# ============================================
# הרצה של כל הדוגמאות
# ============================================

if __name__ == "__main__":
    print("🚀 Dependency Analyzer - דוגמאות שימוש\n")
    print("="*60)
    
    # הערה: שנה את הנתיב לפרויקט שלך
    PROJECT_PATH = Path(__file__).parent.parent.parent
    
    print(f"\n📁 מנתח פרויקט: {PROJECT_PATH}")
    print("="*60)
    
    # הרץ דוגמה אחת (לדוגמה)
    analyzer = DependencyAnalyzer(PROJECT_PATH)
    result = analyzer.analyze()
    
    print(f"\n✅ סה\"כ קבצים: {result.total_files}")
    print(f"✅ קבצים תקינים: {result.valid_files}")
    
    # אם יש קבצים, הצג top risk
    if result.top_risk_files:
        print(f"\n🔴 הקובץ המסוכן ביותר:")
        top = result.top_risk_files[0]
        print(f"   {top['file_path']}")
        print(f"   Risk: {top['risk_score']}/100")
        print(f"   Blast Radius: {top['blast_radius']} files")
