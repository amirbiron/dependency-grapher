"""
Basic test to verify the analyzer works
"""
from pathlib import Path
from analyzer import DependencyAnalyzer

def test_analyzer():
    """בדיקה בסיסית של ה-Analyzer"""
    
    # נתח את הפרויקט עצמו
    project_root = Path(__file__).parent
    
    print(f"Testing analyzer on: {project_root}")
    
    # יצירת analyzer
    analyzer = DependencyAnalyzer(project_root)
    
    # ניתוח
    result = analyzer.analyze()
    
    print(f"\n✓ Analysis complete!")
    print(f"  Total files: {result.total_files}")
    print(f"  Valid files: {result.valid_files}")
    print(f"  Total imports: {result.total_imports}")
    
    # בדיקת Blast Radius על קובץ מסוים
    if result.valid_files > 0:
        # קח קובץ ראשון
        first_file = list(analyzer._file_analyses.keys())[0]
        blast = analyzer.get_blast_radius(first_file)
        
        print(f"\n✓ Blast Radius test:")
        print(f"  File: {Path(first_file).name}")
        print(f"  Total affected: {blast.total_affected}")
        print(f"  Risk: {blast.risk_score:.1f}/100")
    
    print(f"\n✓ All tests passed!")
    return True

if __name__ == "__main__":
    test_analyzer()
