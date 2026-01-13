"""
Advanced Usage Example - מציאת Bottlenecks בפרויקט

דוגמה זו מראה איך למצוא קבצים שהם "bottlenecks" קריטיים בפרויקט.
"""
from pathlib import Path
from analyzer import DependencyAnalyzer
import json

def find_critical_bottlenecks(project_path: str):
    """
    מוצא קבצים קריטיים בפרויקט
    
    Bottleneck = קובץ שיש לו:
    1. Blast Radius גבוה (הרבה קבצים תלויים בו)
    2. Instability נמוכה (הוא יציב)
    3. הרבה תלויות נכנסות
    """
    print(f"🔍 מחפש bottlenecks ב-{project_path}...")
    
    # ניתוח
    analyzer = DependencyAnalyzer(Path(project_path))
    result = analyzer.analyze()
    
    print(f"✓ ניתוח הושלם: {result.valid_files} קבצים\n")
    
    # איסוף מידע על כל קובץ
    bottlenecks = []
    
    for file_path in analyzer.get_graph().nodes():
        risk = analyzer.get_file_risk(file_path)
        
        # קריטריונים ל-bottleneck
        is_bottleneck = (
            risk.blast_radius.total_affected > 5 and  # לפחות 5 תלויים
            risk.stability.afferent_coupling > 3 and  # לפחות 3 תלויות נכנסות
            risk.stability.instability < 0.5  # יחסית יציב
        )
        
        if is_bottleneck:
            bottlenecks.append({
                'file': str(Path(file_path).relative_to(project_path)),
                'blast_radius': risk.blast_radius.total_affected,
                'afferent_coupling': risk.stability.afferent_coupling,
                'instability': round(risk.stability.instability, 2),
                'risk_score': round(risk.risk_score, 1)
            })
    
    # מיון לפי Blast Radius
    bottlenecks.sort(key=lambda x: x['blast_radius'], reverse=True)
    
    # הדפסה
    print(f"{'='*60}")
    print(f"🎯 נמצאו {len(bottlenecks)} Bottlenecks קריטיים")
    print(f"{'='*60}\n")
    
    for i, bn in enumerate(bottlenecks, 1):
        print(f"{i}. {bn['file']}")
        print(f"   📊 Blast Radius: {bn['blast_radius']} files")
        print(f"   🔗 Incoming Dependencies: {bn['afferent_coupling']}")
        print(f"   ⚖️  Instability: {bn['instability']}")
        print(f"   ⚠️  Risk: {bn['risk_score']}/100")
        print()
    
    # המלצות
    print(f"{'='*60}")
    print("💡 המלצות:")
    print(f"{'='*60}")
    print("1. הוסף tests מקיפים לקבצים אלה")
    print("2. שקול לפצל קבצים גדולים למודולים קטנים יותר")
    print("3. הוסף documentation מפורט")
    print("4. שקול dependency injection להפחתת coupling")
    
    return bottlenecks


def analyze_dependency_depth(project_path: str, target_file: str):
    """
    מנתח את עומק שרשראות התלויות
    
    עוזר להבין כמה "עמוק" קובץ מסוים בעץ התלויות
    """
    print(f"🌲 מנתח עומק תלויות עבור {target_file}...\n")
    
    analyzer = DependencyAnalyzer(Path(project_path))
    analyzer.analyze()
    
    blast = analyzer.get_blast_radius(target_file)
    
    print(f"📊 סטטיסטיקות:")
    print(f"   Max Depth: {blast.max_depth} רמות")
    print(f"   Total Affected: {blast.total_affected} קבצים")
    
    if blast.dependency_chain:
        print(f"\n🔗 שרשראות התלויות הארוכות ביותר:")
        for i, chain in enumerate(blast.dependency_chain[:3], 1):
            print(f"\n   Chain {i} (אורך {len(chain)}):")
            for file in chain:
                rel = Path(file).relative_to(project_path)
                print(f"   → {rel}")


def compare_files_impact(project_path: str, file1: str, file2: str):
    """
    משווה את ההשפעה של שני קבצים
    """
    analyzer = DependencyAnalyzer(Path(project_path))
    analyzer.analyze()
    
    risk1 = analyzer.get_file_risk(file1)
    risk2 = analyzer.get_file_risk(file2)
    
    print(f"⚖️  השוואה: {Path(file1).name} vs {Path(file2).name}\n")
    
    print(f"{'Metric':<25} {Path(file1).name:<20} {Path(file2).name:<20}")
    print(f"{'-'*70}")
    print(f"{'Blast Radius':<25} {risk1.blast_radius.total_affected:<20} {risk2.blast_radius.total_affected:<20}")
    print(f"{'Risk Score':<25} {risk1.risk_score:<20.1f} {risk2.risk_score:<20.1f}")
    print(f"{'Afferent Coupling':<25} {risk1.stability.afferent_coupling:<20} {risk2.stability.afferent_coupling:<20}")
    print(f"{'Instability':<25} {risk1.stability.instability:<20.2f} {risk2.stability.instability:<20.2f}")
    
    # קביעת "מנצח"
    if risk1.blast_radius.total_affected > risk2.blast_radius.total_affected:
        print(f"\n🏆 {Path(file1).name} has greater impact")
    else:
        print(f"\n🏆 {Path(file2).name} has greater impact")


# שימוש
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python advanced_example.py <project_path>")
        sys.exit(1)
    
    project = sys.argv[1]
    
    # מציאת bottlenecks
    bottlenecks = find_critical_bottlenecks(project)
    
    # שמירה ל-JSON
    with open('bottlenecks_report.json', 'w', encoding='utf-8') as f:
        json.dump(bottlenecks, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 הדוח נשמר ב-bottlenecks_report.json")
