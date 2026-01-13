"""
Metrics Calculator - חישוב מטריקות על גרף התלויות

המטריקות העיקריות:
1. Blast Radius - כמה קבצים ישברו אם נשנה קובץ מסוים
2. Risk Score - ציון סיכון מבוסס על תלויות ומורכבות
3. Stability - עד כמה הקובץ יציב (פחות תלויות = יותר יציב)
"""
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import networkx as nx

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """רמות סיכון"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BlastRadiusResult:
    """
    תוצאת חישוב Blast Radius
    
    "Blast Radius" = כל הקבצים שעלולים להישבר אם נשנה קובץ מסוים
    """
    file_path: str
    direct_dependents: List[str]  # תלויים ישירים (רמה 1)
    indirect_dependents: List[str]  # תלויים עקיפים (רמה 2+)
    total_affected: int  # סה"כ קבצים מושפעים
    max_depth: int  # העומק המקסימלי של שרשרת התלויות
    risk_level: RiskLevel
    risk_score: float  # 0-100
    dependency_chain: List[List[str]] = field(default_factory=list)  # שרשראות תלויות ארוכות
    
    @property
    def all_affected_files(self) -> List[str]:
        """כל הקבצים המושפעים (ישירים + עקיפים)"""
        return self.direct_dependents + self.indirect_dependents


@dataclass
class StabilityMetrics:
    """
    מטריקות יציבות של קובץ
    
    קובץ יציב = קובץ שמשתנה פחות ולכן בטוח יותר לסמוך עליו
    """
    file_path: str
    afferent_coupling: int  # Ce - כמה קבצים תלויים בקובץ הזה (incoming)
    efferent_coupling: int  # Ca - כמה קבצים הקובץ תלוי בהם (outgoing)
    instability: float  # I = Ce / (Ce + Ca), 0 = יציב מאוד, 1 = לא יציב
    abstractness: float  # A - יחס של classes/interfaces לקוד כולל
    distance_from_main: float  # D - מרחק מה-main sequence
    stability_category: str  # "stable", "unstable", "balanced"
    
    @property
    def is_stable(self) -> bool:
        """האם הקובץ יציב"""
        return self.instability < 0.3
    
    @property
    def is_unstable(self) -> bool:
        """האם הקובץ לא יציב"""
        return self.instability > 0.7


@dataclass
class ComplexityMetrics:
    """מטריקות מורכבות"""
    file_path: str
    cyclomatic_complexity: int  # מספר נתיבים עצמאיים
    cognitive_complexity: int  # מורכבות קוגניטיבית
    lines_of_code: int
    num_functions: int
    num_classes: int
    avg_function_length: float
    complexity_score: float  # ציון כולל


@dataclass
class FileRiskAnalysis:
    """ניתוח סיכון מקיף לקובץ"""
    file_path: str
    blast_radius: BlastRadiusResult
    stability: StabilityMetrics
    risk_level: RiskLevel
    risk_score: float  # 0-100
    risk_factors: List[str]  # רשימת גורמי סיכון
    recommendations: List[str]  # המלצות לשיפור


class MetricsCalculator:
    """
    מחשב מטריקות שונות על גרף התלויות
    
    Example:
        >>> calc = MetricsCalculator(graph, project_root)
        >>> blast_radius = calc.calculate_blast_radius("myapp/core.py")
        >>> print(f"Total affected: {blast_radius.total_affected}")
    """
    
    def __init__(self, graph: nx.DiGraph, project_root: Path):
        """
        Args:
            graph: גרף התלויות (מ-GraphBuilder)
            project_root: שורש הפרויקט
        """
        self.graph = graph
        self.project_root = project_root
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Caching
        self._blast_radius_cache: Dict[str, BlastRadiusResult] = {}
        self._stability_cache: Dict[str, StabilityMetrics] = {}
    
    def calculate_blast_radius(self, 
                              file_path: str,
                              max_depth: int = 10) -> BlastRadiusResult:
        """
        מחשב את ה-Blast Radius של קובץ
        
        Args:
            file_path: נתיב הקובץ
            max_depth: עומק מקסימלי לחיפוש
            
        Returns:
            BlastRadiusResult עם כל המידע
        """
        # בדיקת cache
        cache_key = f"{file_path}:{max_depth}"
        if cache_key in self._blast_radius_cache:
            return self._blast_radius_cache[cache_key]
        
        if file_path not in self.graph:
            return BlastRadiusResult(
                file_path=file_path,
                direct_dependents=[],
                indirect_dependents=[],
                total_affected=0,
                max_depth=0,
                risk_level=RiskLevel.LOW,
                risk_score=0.0
            )
        
        # תלויים ישירים (רמה 1)
        direct = list(self.graph.predecessors(file_path))
        
        # תלויים עקיפים (רמה 2+)
        all_dependents = self._get_all_dependents_with_depth(file_path, max_depth)
        indirect = [node for node, depth in all_dependents.items() if depth > 1]
        
        # חישוב עומק מקסימלי
        max_found_depth = max([depth for _, depth in all_dependents.items()], default=0)
        
        # חישוב ציון סיכון
        total_affected = len(direct) + len(indirect)
        risk_score = self._calculate_risk_score(total_affected, max_found_depth)
        risk_level = self._get_risk_level(risk_score)
        
        # מציאת שרשראות תלויות ארוכות
        chains = self._find_dependency_chains(file_path, min_length=3)
        
        result = BlastRadiusResult(
            file_path=file_path,
            direct_dependents=direct,
            indirect_dependents=indirect,
            total_affected=total_affected,
            max_depth=max_found_depth,
            risk_level=risk_level,
            risk_score=risk_score,
            dependency_chain=chains[:5]  # 5 הארוכים ביותר
        )
        
        # שמירה ב-cache
        self._blast_radius_cache[cache_key] = result
        
        return result
    
    def _get_all_dependents_with_depth(self, 
                                       file_path: str, 
                                       max_depth: int) -> Dict[str, int]:
        """
        מחזיר את כל התלויים עם העומק שלהם
        
        Returns:
            {file_path: depth}
        """
        dependents = {}
        queue = [(file_path, 0)]
        visited = {file_path}
        
        while queue:
            current, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            for dependent in self.graph.predecessors(current):
                if dependent not in visited:
                    visited.add(dependent)
                    dependents[dependent] = depth + 1
                    queue.append((dependent, depth + 1))
        
        return dependents
    
    def _calculate_risk_score(self, num_affected: int, max_depth: int) -> float:
        """
        מחשב ציון סיכון (0-100)
        
        הציון מבוסס על:
        - מספר קבצים מושפעים (משקל 70%)
        - עומק שרשרת התלויות (משקל 30%)
        """
        # נרמול מספר קבצים מושפעים (0-50 קבצים = 0-70 נקודות)
        affected_score = min(num_affected / 50 * 70, 70)
        
        # נרמול עומק (0-10 רמות = 0-30 נקודות)
        depth_score = min(max_depth / 10 * 30, 30)
        
        return affected_score + depth_score
    
    def _get_risk_level(self, risk_score: float) -> RiskLevel:
        """המרת ציון סיכון לרמת סיכון"""
        if risk_score < 20:
            return RiskLevel.LOW
        elif risk_score < 50:
            return RiskLevel.MEDIUM
        elif risk_score < 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _find_dependency_chains(self, 
                               file_path: str, 
                               min_length: int = 3) -> List[List[str]]:
        """
        מוצא שרשראות תלויות ארוכות
        
        שרשרת: A -> B -> C -> D (אם נשנה את A, D ישבר)
        """
        chains = []
        
        def dfs(node: str, path: List[str]):
            if len(path) >= min_length:
                chains.append(path[:])
            
            if len(path) >= 10:  # הגבלת אורך
                return
            
            for dependent in self.graph.predecessors(node):
                if dependent not in path:  # מניעת מעגלים
                    path.append(dependent)
                    dfs(dependent, path)
                    path.pop()
        
        dfs(file_path, [file_path])
        
        # מיון לפי אורך (הארוכים ביותר)
        chains.sort(key=len, reverse=True)
        return chains
    
    def calculate_stability(self, file_path: str) -> StabilityMetrics:
        """
        מחשב מטריקות יציבות
        
        Stability Metrics (מבוססות על Robert C. Martin):
        - Afferent Coupling (Ce): כמה מודולים תלויים בקובץ הזה
        - Efferent Coupling (Ca): כמה מודולים הקובץ תלוי בהם
        - Instability (I): Ca / (Ca + Ce)
        """
        # בדיקת cache
        if file_path in self._stability_cache:
            return self._stability_cache[file_path]
        
        if file_path not in self.graph:
            return StabilityMetrics(
                file_path=file_path,
                afferent_coupling=0,
                efferent_coupling=0,
                instability=0.0,
                abstractness=0.0,
                distance_from_main=0.0,
                stability_category="unknown"
            )
        
        # חישוב Coupling
        ce = self.graph.in_degree(file_path)  # Afferent (incoming)
        ca = self.graph.out_degree(file_path)  # Efferent (outgoing)
        
        # חישוב Instability
        total_coupling = ce + ca
        instability = ca / total_coupling if total_coupling > 0 else 0.0
        
        # חישוב Abstractness (מבוסס על נתוני הצומת)
        node_data = self.graph.nodes[file_path]
        num_classes = node_data.get('num_classes', 0)
        num_functions = node_data.get('num_functions', 0)
        abstractness = num_classes / (num_classes + num_functions) if (num_classes + num_functions) > 0 else 0.0
        
        # Distance from Main Sequence: |A + I - 1|
        distance = abs(abstractness + instability - 1)
        
        # קטגוריה
        if instability < 0.3:
            category = "stable"
        elif instability > 0.7:
            category = "unstable"
        else:
            category = "balanced"
        
        result = StabilityMetrics(
            file_path=file_path,
            afferent_coupling=ce,
            efferent_coupling=ca,
            instability=instability,
            abstractness=abstractness,
            distance_from_main=distance,
            stability_category=category
        )
        
        # שמירה ב-cache
        self._stability_cache[file_path] = result
        
        return result
    
    def calculate_file_risk(self, file_path: str) -> FileRiskAnalysis:
        """
        ניתוח סיכון מקיף לקובץ
        
        משלב Blast Radius + Stability + Complexity
        """
        # חישוב מטריקות
        blast_radius = self.calculate_blast_radius(file_path)
        stability = self.calculate_stability(file_path)
        
        # ציון סיכון משוקלל
        risk_score = (
            blast_radius.risk_score * 0.5 +  # 50% - Blast Radius
            (1 - stability.instability) * 50 * 0.3 +  # 30% - Stability
            stability.distance_from_main * 50 * 0.2  # 20% - Distance
        )
        
        risk_level = self._get_risk_level(risk_score)
        
        # זיהוי גורמי סיכון
        risk_factors = []
        if blast_radius.total_affected > 10:
            risk_factors.append(f"High blast radius: {blast_radius.total_affected} files affected")
        if stability.instability > 0.7:
            risk_factors.append(f"Unstable: instability={stability.instability:.2f}")
        if blast_radius.max_depth > 5:
            risk_factors.append(f"Deep dependency chain: {blast_radius.max_depth} levels")
        
        # המלצות
        recommendations = []
        if blast_radius.total_affected > 15:
            recommendations.append("Consider splitting this module into smaller components")
        if stability.efferent_coupling > 10:
            recommendations.append("Too many dependencies - consider dependency injection")
        if stability.afferent_coupling > 15:
            recommendations.append("Critical hub - add comprehensive tests")
        
        return FileRiskAnalysis(
            file_path=file_path,
            blast_radius=blast_radius,
            stability=stability,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def get_project_metrics(self) -> Dict:
        """מטריקות כלליות על כל הפרויקט"""
        all_files = list(self.graph.nodes())
        
        if not all_files:
            return {}
        
        # חישוב ממוצעים
        blast_radii = [self.calculate_blast_radius(f) for f in all_files]
        stabilities = [self.calculate_stability(f) for f in all_files]
        
        avg_blast_radius = sum(br.total_affected for br in blast_radii) / len(blast_radii)
        avg_instability = sum(s.instability for s in stabilities) / len(stabilities)
        
        # זיהוי קבצים בסיכון גבוה
        high_risk_files = [
            br.file_path for br in blast_radii
            if br.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]
        
        # Hub files
        hub_files = [
            f for f in all_files
            if self.graph.in_degree(f) > 10
        ]
        
        return {
            'total_files': len(all_files),
            'avg_blast_radius': avg_blast_radius,
            'avg_instability': avg_instability,
            'high_risk_files': len(high_risk_files),
            'hub_files': len(hub_files),
            'most_critical': max(blast_radii, key=lambda x: x.risk_score).file_path if blast_radii else None
        }
    
    def get_top_risk_files(self, n: int = 10) -> List[FileRiskAnalysis]:
        """מחזיר את N הקבצים המסוכנים ביותר"""
        all_files = list(self.graph.nodes())
        analyses = [self.calculate_file_risk(f) for f in all_files]
        
        # מיון לפי ציון סיכון
        analyses.sort(key=lambda x: x.risk_score, reverse=True)
        
        return analyses[:n]
    
    def clear_cache(self):
        """מנקה את ה-cache"""
        self._blast_radius_cache.clear()
        self._stability_cache.clear()


# Example usage & CLI
if __name__ == "__main__":
    import sys
    from .ast_parser import ASTParser
    from .resolver import ImportResolver
    from .graph_builder import GraphBuilder
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python metrics.py <project_root> [file_to_analyze]")
        sys.exit(1)
    
    project_root = Path(sys.argv[1])
    
    # בניית הגרף
    print("Building dependency graph...")
    parser = ASTParser(skip_stdlib=True)
    resolver = ImportResolver(project_root)
    builder = GraphBuilder(project_root)
    
    for py_file in project_root.rglob("*.py"):
        if any(skip in py_file.parts for skip in ["__pycache__", ".venv"]):
            continue
        
        analysis = parser.parse_file(py_file)
        if analysis.is_valid:
            resolved = resolver.resolve_batch(analysis.imports, py_file)
            builder.add_file_analysis(analysis, resolved)
    
    graph = builder.build()
    
    # חישוב מטריקות
    calc = MetricsCalculator(graph, project_root)
    
    if len(sys.argv) > 2:
        # ניתוח קובץ ספציפי
        target_file = Path(sys.argv[2])
        
        print(f"\n{'='*60}")
        print(f"Risk Analysis: {target_file.name}")
        print(f"{'='*60}\n")
        
        risk = calc.calculate_file_risk(str(target_file))
        
        print(f"Risk Level: {risk.risk_level.value.upper()}")
        print(f"Risk Score: {risk.risk_score:.1f}/100")
        
        print(f"\n--- Blast Radius ---")
        print(f"Direct dependents: {len(risk.blast_radius.direct_dependents)}")
        print(f"Indirect dependents: {len(risk.blast_radius.indirect_dependents)}")
        print(f"Total affected: {risk.blast_radius.total_affected}")
        print(f"Max depth: {risk.blast_radius.max_depth}")
        
        print(f"\n--- Stability ---")
        print(f"Afferent coupling (Ce): {risk.stability.afferent_coupling}")
        print(f"Efferent coupling (Ca): {risk.stability.efferent_coupling}")
        print(f"Instability (I): {risk.stability.instability:.2f}")
        print(f"Category: {risk.stability.stability_category}")
        
        if risk.risk_factors:
            print(f"\n--- Risk Factors ---")
            for factor in risk.risk_factors:
                print(f"  ⚠️  {factor}")
        
        if risk.recommendations:
            print(f"\n--- Recommendations ---")
            for rec in risk.recommendations:
                print(f"  💡 {rec}")
    
    else:
        # סקירה כללית
        print(f"\n{'='*60}")
        print("Project Metrics")
        print(f"{'='*60}\n")
        
        metrics = calc.get_project_metrics()
        for key, value in metrics.items():
            print(f"{key}: {value}")
        
        print(f"\n{'='*60}")
        print("Top 10 Highest Risk Files")
        print(f"{'='*60}\n")
        
        top_risks = calc.get_top_risk_files(10)
        for i, risk in enumerate(top_risks, 1):
            rel_path = Path(risk.file_path).relative_to(project_root)
            print(f"{i}. {rel_path}")
            print(f"   Risk: {risk.risk_score:.1f}/100 ({risk.risk_level.value})")
            print(f"   Blast Radius: {risk.blast_radius.total_affected} files")
            print()
