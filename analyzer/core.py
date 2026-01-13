"""
Dependency Analyzer - המנוע המרכזי

זה הקובץ הראשי שמחבר את כל החלקים:
- AST Parser
- Import Resolver  
- Graph Builder
- Metrics Calculator
"""
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import logging
import json
from datetime import datetime
import networkx as nx

from .ast_parser import ASTParser, FileAnalysis
from .resolver import ImportResolver
from .graph_builder import GraphBuilder
from .metrics import MetricsCalculator, BlastRadiusResult, FileRiskAnalysis

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """תוצאת ניתוח מלאה של פרויקט"""
    project_root: str
    analyzed_at: str
    total_files: int
    valid_files: int
    error_files: int
    total_imports: int
    total_functions: int
    total_classes: int
    graph_stats: Dict
    project_metrics: Dict
    top_risk_files: List[Dict]
    circular_dependencies: List[List[str]]
    
    def to_dict(self) -> Dict:
        """המרה למילון (ל-JSON)"""
        return {
            'project_root': self.project_root,
            'analyzed_at': self.analyzed_at,
            'summary': {
                'total_files': self.total_files,
                'valid_files': self.valid_files,
                'error_files': self.error_files,
                'total_imports': self.total_imports,
                'total_functions': self.total_functions,
                'total_classes': self.total_classes
            },
            'graph_stats': self.graph_stats,
            'project_metrics': self.project_metrics,
            'top_risk_files': self.top_risk_files,
            'circular_dependencies': self.circular_dependencies
        }


class DependencyAnalyzer:
    """
    המנוע המרכזי לניתוח תלויות
    
    Example:
        >>> analyzer = DependencyAnalyzer("/path/to/project")
        >>> result = analyzer.analyze()
        >>> print(f"Analyzed {result.total_files} files")
        >>> blast_radius = analyzer.get_blast_radius("myapp/core.py")
    """
    
    def __init__(self, 
                 project_root: Path | str,
                 skip_stdlib: bool = True,
                 extract_calls: bool = False):
        """
        Args:
            project_root: שורש הפרויקט
            skip_stdlib: האם לדלג על imports מספריית הסטנדרט
            extract_calls: האם לחלץ קריאות לפונקציות (יותר איטי)
        """
        self.project_root = Path(project_root).resolve()
        
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {self.project_root}")
        
        if not self.project_root.is_dir():
            raise ValueError(f"Project root is not a directory: {self.project_root}")
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # יצירת הכלים
        self.parser = ASTParser(skip_stdlib=skip_stdlib, extract_calls=extract_calls)
        self.resolver = ImportResolver(self.project_root)
        self.builder = GraphBuilder(self.project_root)
        
        # Metrics calculator יווצר אחרי בניית הגרף
        self.metrics_calculator: Optional[MetricsCalculator] = None
        
        # מידע על הניתוח
        self._file_analyses: Dict[str, FileAnalysis] = {}
        self._analysis_complete = False
    
    def analyze(self, 
               skip_dirs: Optional[Set[str]] = None,
               progress_callback = None) -> AnalysisResult:
        """
        מנתח את כל הפרויקט
        
        Args:
            skip_dirs: תיקיות נוספות לדלג עליהן
            progress_callback: פונקציה שתקרא עם progress (קובץ נוכחי, סה"כ)
            
        Returns:
            AnalysisResult עם כל התוצאות
        """
        self.logger.info(f"Starting analysis of {self.project_root}")
        
        # תיקיות ברירת מחדל לדלוג
        default_skip = {"__pycache__", ".venv", "venv", "env", ".git", "node_modules"}
        if skip_dirs:
            default_skip.update(skip_dirs)
        
        # איסוף כל קבצי הפייתון
        python_files = []
        for py_file in self.project_root.rglob("*.py"):
            # דילוג על תיקיות מיוחדות
            if any(skip in py_file.parts for skip in default_skip):
                continue
            python_files.append(py_file)
        
        total_files = len(python_files)
        self.logger.info(f"Found {total_files} Python files")
        
        # ניתוח כל קובץ
        valid_count = 0
        error_count = 0
        
        for i, py_file in enumerate(python_files, 1):
            if progress_callback:
                progress_callback(i, total_files)
            
            self.logger.debug(f"[{i}/{total_files}] Analyzing {py_file.name}")
            
            # ניתוח AST
            analysis = self.parser.parse_file(py_file)
            self._file_analyses[str(py_file)] = analysis
            
            if not analysis.is_valid:
                error_count += 1
                self.logger.warning(f"Failed to parse {py_file}: {analysis.parse_error}")
                continue
            
            valid_count += 1
            
            # פתרון imports
            resolved_imports = self.resolver.resolve_batch(analysis.imports, py_file)
            
            # הוספה לגרף
            self.builder.add_file_analysis(analysis, resolved_imports)
        
        # בניית הגרף
        graph = self.builder.build()
        
        # יצירת metrics calculator
        self.metrics_calculator = MetricsCalculator(graph, self.project_root)
        
        # איסוף סטטיסטיקות
        total_imports = sum(len(a.imports) for a in self._file_analyses.values())
        total_functions = sum(len(a.functions) for a in self._file_analyses.values())
        total_classes = sum(len(a.classes) for a in self._file_analyses.values())
        
        graph_stats = self.builder.get_stats()
        project_metrics = self.metrics_calculator.get_project_metrics()
        
        # Top risk files
        top_risks = self.metrics_calculator.get_top_risk_files(10)
        top_risk_dicts = [
            {
                'file_path': str(Path(r.file_path).relative_to(self.project_root)),
                'risk_score': round(r.risk_score, 1),
                'risk_level': r.risk_level.value,
                'blast_radius': r.blast_radius.total_affected,
                'risk_factors': r.risk_factors
            }
            for r in top_risks
        ]
        
        # Circular dependencies
        cycles = self.builder.find_cycles()
        cycle_paths = [
            [str(Path(f).relative_to(self.project_root)) for f in cycle]
            for cycle in cycles
        ]
        
        self._analysis_complete = True
        
        result = AnalysisResult(
            project_root=str(self.project_root),
            analyzed_at=datetime.now().isoformat(),
            total_files=total_files,
            valid_files=valid_count,
            error_files=error_count,
            total_imports=total_imports,
            total_functions=total_functions,
            total_classes=total_classes,
            graph_stats=graph_stats,
            project_metrics=project_metrics,
            top_risk_files=top_risk_dicts,
            circular_dependencies=cycle_paths
        )
        
        self.logger.info(f"Analysis complete: {valid_count} files analyzed successfully")
        
        return result
    
    def get_blast_radius(self, file_path: str | Path) -> BlastRadiusResult:
        """
        מחשב Blast Radius לקובץ ספציפי
        
        Args:
            file_path: נתיב לקובץ (יחסי או מוחלט)
            
        Returns:
            BlastRadiusResult
        """
        if not self._analysis_complete:
            raise RuntimeError("Must call analyze() first")
        
        # המרה לנתיב מוחלט
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / path
        
        return self.metrics_calculator.calculate_blast_radius(str(path))
    
    def get_file_risk(self, file_path: str | Path) -> FileRiskAnalysis:
        """
        ניתוח סיכון מקיף לקובץ
        
        Args:
            file_path: נתיב לקובץ
            
        Returns:
            FileRiskAnalysis
        """
        if not self._analysis_complete:
            raise RuntimeError("Must call analyze() first")
        
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / path
        
        return self.metrics_calculator.calculate_file_risk(str(path))
    
    def get_file_dependencies(self, file_path: str | Path) -> List[str]:
        """מחזיר את כל הקבצים שהקובץ תלוי בהם"""
        if not self._analysis_complete:
            raise RuntimeError("Must call analyze() first")
        
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / path
        
        return self.builder.get_dependencies(str(path))
    
    def get_file_dependents(self, file_path: str | Path) -> List[str]:
        """מחזיר את כל הקבצים שתלויים בקובץ"""
        if not self._analysis_complete:
            raise RuntimeError("Must call analyze() first")
        
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / path
        
        return self.builder.get_dependents(str(path))
    
    def find_path_between(self, 
                         source: str | Path, 
                         target: str | Path) -> Optional[List[str]]:
        """מוצא את המסלול הקצר ביותר בין שני קבצים"""
        if not self._analysis_complete:
            raise RuntimeError("Must call analyze() first")
        
        source_path = Path(source)
        if not source_path.is_absolute():
            source_path = self.project_root / source_path
        
        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = self.project_root / target_path
        
        return self.builder.get_shortest_path(str(source_path), str(target_path))
    
    def export_to_json(self, output_path: str | Path) -> None:
        """
        ייצוא התוצאות ל-JSON
        
        Args:
            output_path: נתיב לקובץ היעד
        """
        if not self._analysis_complete:
            raise RuntimeError("Must call analyze() first")
        
        data = self.builder.export_to_dict()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Exported to {output_path}")
    
    def export_for_cytoscape(self, output_path: str | Path) -> None:
        """
        ייצוא לפורמט Cytoscape.js (ל-Frontend)
        
        Args:
            output_path: נתיב לקובץ היעד
        """
        if not self._analysis_complete:
            raise RuntimeError("Must call analyze() first")
        
        data = self.builder.export_for_cytoscape()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Exported Cytoscape data to {output_path}")
    
    def get_graph(self) -> nx.DiGraph:
        """מחזיר את הגרף (לשימוש מתקדם)"""
        if not self._analysis_complete:
            raise RuntimeError("Must call analyze() first")
        
        return self.builder.graph
    
    def get_stats(self) -> Dict:
        """מחזיר סטטיסטיקות על הניתוח"""
        if not self._analysis_complete:
            return {
                'status': 'not_analyzed',
                'message': 'Call analyze() first'
            }
        
        return {
            'status': 'complete',
            'total_files': len(self._file_analyses),
            'valid_files': sum(1 for a in self._file_analyses.values() if a.is_valid),
            'graph_stats': self.builder.get_stats(),
            'project_metrics': self.metrics_calculator.get_project_metrics()
        }


# CLI
def main():
    """Entry point for CLI usage"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze Python project dependencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a project
  python -m analyzer.core /path/to/project
  
  # Get blast radius for a specific file
  python -m analyzer.core /path/to/project --file myapp/core.py
  
  # Export to JSON
  python -m analyzer.core /path/to/project --export results.json
  
  # Export for Cytoscape
  python -m analyzer.core /path/to/project --cytoscape graph.json
        """
    )
    
    parser.add_argument('project_root', type=Path, help='Project root directory')
    parser.add_argument('--file', type=str, help='Analyze specific file')
    parser.add_argument('--export', type=Path, help='Export results to JSON')
    parser.add_argument('--cytoscape', type=Path, help='Export for Cytoscape.js')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--skip-stdlib', action='store_true', default=True, help='Skip standard library imports')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Validate project root
    if not args.project_root.exists():
        print(f"Error: Project root does not exist: {args.project_root}")
        sys.exit(1)
    
    # Create analyzer
    analyzer = DependencyAnalyzer(
        args.project_root,
        skip_stdlib=args.skip_stdlib
    )
    
    # Progress callback
    def progress(current, total):
        percent = (current / total) * 100
        print(f"Progress: {current}/{total} ({percent:.1f}%)", end='\r')
    
    # Analyze
    print(f"\n{'='*60}")
    print(f"Analyzing: {args.project_root}")
    print(f"{'='*60}\n")
    
    result = analyzer.analyze(progress_callback=progress)
    
    print("\n")  # New line after progress
    
    # Print summary
    print(f"\n{'='*60}")
    print("Analysis Summary")
    print(f"{'='*60}")
    print(f"Total files: {result.total_files}")
    print(f"Valid files: {result.valid_files}")
    print(f"Error files: {result.error_files}")
    print(f"Total imports: {result.total_imports}")
    print(f"Total functions: {result.total_functions}")
    print(f"Total classes: {result.total_classes}")
    
    print(f"\n{'='*60}")
    print("Graph Statistics")
    print(f"{'='*60}")
    for key, value in result.graph_stats.items():
        print(f"{key}: {value}")
    
    # Circular dependencies
    if result.circular_dependencies:
        print(f"\n{'='*60}")
        print(f"⚠️  Found {len(result.circular_dependencies)} Circular Dependencies")
        print(f"{'='*60}")
        for i, cycle in enumerate(result.circular_dependencies[:5], 1):
            print(f"\nCycle {i}:")
            for file_path in cycle:
                print(f"  → {file_path}")
            print(f"  → {cycle[0]}")
    
    # Top risk files
    print(f"\n{'='*60}")
    print("Top 10 Highest Risk Files")
    print(f"{'='*60}\n")
    for i, risk in enumerate(result.top_risk_files, 1):
        print(f"{i}. {risk['file_path']}")
        print(f"   Risk: {risk['risk_score']}/100 ({risk['risk_level']})")
        print(f"   Blast Radius: {risk['blast_radius']} files")
        if risk['risk_factors']:
            print(f"   Factors: {', '.join(risk['risk_factors'][:2])}")
        print()
    
    # Specific file analysis
    if args.file:
        print(f"\n{'='*60}")
        print(f"Detailed Analysis: {args.file}")
        print(f"{'='*60}\n")
        
        risk = analyzer.get_file_risk(args.file)
        
        print(f"Risk Level: {risk.risk_level.value.upper()}")
        print(f"Risk Score: {risk.risk_score:.1f}/100")
        
        print(f"\n--- Blast Radius ---")
        print(f"Direct dependents: {len(risk.blast_radius.direct_dependents)}")
        print(f"Indirect dependents: {len(risk.blast_radius.indirect_dependents)}")
        print(f"Total affected: {risk.blast_radius.total_affected}")
        
        if risk.blast_radius.direct_dependents:
            print(f"\nDirect dependents:")
            for dep in risk.blast_radius.direct_dependents[:5]:
                rel = Path(dep).relative_to(args.project_root)
                print(f"  • {rel}")
        
        print(f"\n--- Stability ---")
        print(f"Afferent coupling (incoming): {risk.stability.afferent_coupling}")
        print(f"Efferent coupling (outgoing): {risk.stability.efferent_coupling}")
        print(f"Instability: {risk.stability.instability:.2f}")
        print(f"Category: {risk.stability.stability_category}")
        
        if risk.recommendations:
            print(f"\n--- Recommendations ---")
            for rec in risk.recommendations:
                print(f"  💡 {rec}")
    
    # Export
    if args.export:
        analyzer.export_to_json(args.export)
        print(f"\n✓ Exported results to {args.export}")
    
    if args.cytoscape:
        analyzer.export_for_cytoscape(args.cytoscape)
        print(f"\n✓ Exported Cytoscape data to {args.cytoscape}")


if __name__ == "__main__":
    main()
