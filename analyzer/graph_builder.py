"""
Graph Builder - בונה גרף תלויות מתוצאות הניתוח
משתמש ב-NetworkX ליצירת Directed Graph של התלויות בין קבצים
"""
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import logging
import networkx as nx

from .ast_parser import FileAnalysis
from .resolver import ResolvedImport

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """צומת בגרף - מייצג קובץ"""
    file_path: str
    relative_path: str
    name: str
    total_lines: int
    code_lines: int
    num_imports: int
    num_functions: int
    num_classes: int
    has_main: bool
    complexity_score: float
    node_type: str = "module"  # module, package, script
    
    @classmethod
    def from_analysis(cls, analysis: FileAnalysis, project_root: Path):
        """יצירה מתוצאת ניתוח"""
        abs_path = Path(analysis.file_path)
        try:
            rel_path = abs_path.relative_to(project_root)
        except ValueError:
            rel_path = abs_path
        
        # קביעת סוג הצומת
        node_type = "module"
        if abs_path.name == "__init__.py":
            node_type = "package"
        elif analysis.has_main:
            node_type = "script"
        
        return cls(
            file_path=str(abs_path),
            relative_path=str(rel_path),
            name=abs_path.stem if abs_path.name != "__init__.py" else abs_path.parent.name,
            total_lines=analysis.total_lines,
            code_lines=analysis.code_lines,
            num_imports=len(analysis.imports),
            num_functions=len(analysis.functions),
            num_classes=len(analysis.classes),
            has_main=analysis.has_main,
            complexity_score=analysis.complexity_score,
            node_type=node_type
        )


@dataclass
class GraphEdge:
    """קשת בגרף - מייצגת תלות בין קבצים"""
    source: str  # קובץ מקור
    target: str  # קובץ יעד
    import_type: str  # "import" או "from"
    is_relative: bool
    line_number: int
    imported_names: List[str]


class GraphBuilder:
    """
    בונה גרף תלויות מניתוח AST
    
    הגרף הוא Directed Graph שבו:
    - כל צומת = קובץ Python
    - כל קשת = import (תלות)
    - כיוון הקשת: מי שמייבא -> מי שמיובא
    
    Example:
        >>> builder = GraphBuilder(project_root)
        >>> builder.add_file_analysis(analysis, resolved_imports)
        >>> graph = builder.build()
        >>> print(f"Nodes: {graph.number_of_nodes()}")
    """
    
    def __init__(self, project_root: Path):
        """
        Args:
            project_root: שורש הפרויקט
        """
        self.project_root = project_root
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # הגרף עצמו
        self.graph = nx.DiGraph()
        
        # מידע נוסף
        self._file_analyses: Dict[str, FileAnalysis] = {}
        self._resolved_imports: Dict[str, List[ResolvedImport]] = {}
    
    def add_file_analysis(self, 
                         analysis: FileAnalysis,
                         resolved_imports: List[ResolvedImport]):
        """
        מוסיף קובץ לגרף
        
        Args:
            analysis: תוצאת ניתוח הקובץ
            resolved_imports: רשימת imports שנפתרו
        """
        file_path = analysis.file_path
        
        # שמירה למידע
        self._file_analyses[file_path] = analysis
        self._resolved_imports[file_path] = resolved_imports
        
        # יצירת צומת
        node_data = GraphNode.from_analysis(analysis, self.project_root)
        self.graph.add_node(
            file_path,
            **node_data.__dict__
        )
        
        # הוספת קשתות (edges) לכל import שנפתר
        for resolved in resolved_imports:
            if resolved.is_local and resolved.resolved_path:
                target_path = str(resolved.resolved_path)
                
                # יצירת קשת
                edge_data = GraphEdge(
                    source=file_path,
                    target=target_path,
                    import_type=resolved.original_import.import_type,
                    is_relative=resolved.original_import.is_relative,
                    line_number=resolved.original_import.lineno,
                    imported_names=resolved.original_import.names
                )
                
                self.graph.add_edge(
                    file_path,
                    target_path,
                    **edge_data.__dict__
                )
    
    def build(self) -> nx.DiGraph:
        """
        מחזיר את הגרף המלא
        
        Returns:
            NetworkX DiGraph
        """
        self.logger.info(f"Built graph with {self.graph.number_of_nodes()} nodes "
                        f"and {self.graph.number_of_edges()} edges")
        return self.graph
    
    def get_node_data(self, file_path: str) -> Optional[GraphNode]:
        """מחזיר את הנתונים של צומת"""
        if file_path not in self.graph:
            return None
        
        data = self.graph.nodes[file_path]
        return GraphNode(**data)
    
    def get_dependencies(self, file_path: str) -> List[str]:
        """
        מחזיר את כל הקבצים שהקובץ הזה תלוי בהם
        (ישירות - רמה 1 בלבד)
        """
        if file_path not in self.graph:
            return []
        
        return list(self.graph.successors(file_path))
    
    def get_dependents(self, file_path: str) -> List[str]:
        """
        מחזיר את כל הקבצים שתלויים בקובץ הזה
        (ישירות - רמה 1 בלבד)
        """
        if file_path not in self.graph:
            return []
        
        return list(self.graph.predecessors(file_path))
    
    def get_all_dependencies(self, file_path: str, max_depth: int = 10) -> Set[str]:
        """
        מחזיר את כל התלויות (גם עקיפות)
        
        Args:
            file_path: נתיב הקובץ
            max_depth: עומק מקסימלי
            
        Returns:
            סט של כל הקבצים שהקובץ תלוי בהם
        """
        if file_path not in self.graph:
            return set()
        
        # BFS עם הגבלת עומק
        dependencies = set()
        queue = [(file_path, 0)]
        visited = {file_path}
        
        while queue:
            current, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            for dep in self.graph.successors(current):
                if dep not in visited:
                    visited.add(dep)
                    dependencies.add(dep)
                    queue.append((dep, depth + 1))
        
        return dependencies
    
    def get_all_dependents(self, file_path: str, max_depth: int = 10) -> Set[str]:
        """
        מחזיר את כל התלויים (גם עקיפים) - ה"Blast Radius"
        
        זה מה שישבר אם נשנה את הקובץ!
        
        Args:
            file_path: נתיב הקובץ
            max_depth: עומק מקסימלי
            
        Returns:
            סט של כל הקבצים שתלויים בקובץ הזה
        """
        if file_path not in self.graph:
            return set()
        
        # BFS הפוך
        dependents = set()
        queue = [(file_path, 0)]
        visited = {file_path}
        
        while queue:
            current, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            for dependent in self.graph.predecessors(current):
                if dependent not in visited:
                    visited.add(dependent)
                    dependents.add(dependent)
                    queue.append((dependent, depth + 1))
        
        return dependents
    
    def find_cycles(self) -> List[List[str]]:
        """
        מחפש מעגלים בגרף (circular dependencies)
        
        Returns:
            רשימה של מעגלים, כל מעגל הוא רשימת קבצים
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            self.logger.info(f"Found {len(cycles)} circular dependencies")
            return cycles
        except Exception as e:
            self.logger.error(f"Error finding cycles: {e}")
            return []
    
    def get_isolated_nodes(self) -> List[str]:
        """
        מחזיר קבצים מבודדים (ללא תלויות כלל)
        """
        isolated = [
            node for node in self.graph.nodes()
            if self.graph.in_degree(node) == 0 and self.graph.out_degree(node) == 0
        ]
        return isolated
    
    def get_entry_points(self) -> List[str]:
        """
        מחזיר קבצי entry point (בעלי __main__ או ללא תלויים)
        """
        entry_points = []
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            
            # קובץ עם __main__
            if node_data.get('has_main', False):
                entry_points.append(node)
            # או קובץ שאף אחד לא תלוי בו (leaf)
            elif self.graph.in_degree(node) == 0:
                entry_points.append(node)
        
        return entry_points
    
    def get_hub_nodes(self, threshold: int = 5) -> List[Tuple[str, int]]:
        """
        מחזיר "Hub" nodes - קבצים שהרבה קבצים תלויים בהם
        
        Args:
            threshold: מספר מינימלי של תלויים
            
        Returns:
            רשימה של (file_path, num_dependents)
        """
        hubs = []
        
        for node in self.graph.nodes():
            in_degree = self.graph.in_degree(node)
            if in_degree >= threshold:
                hubs.append((node, in_degree))
        
        # מיון לפי מספר תלויים
        hubs.sort(key=lambda x: x[1], reverse=True)
        return hubs
    
    def get_leaf_nodes(self) -> List[str]:
        """
        מחזיר "Leaf" nodes - קבצים שלא תלויים באף אחד
        """
        return [
            node for node in self.graph.nodes()
            if self.graph.out_degree(node) == 0
        ]
    
    def calculate_centrality(self) -> Dict[str, float]:
        """
        מחשב Betweenness Centrality - עד כמה קובץ "מרכזי"
        
        קבצים עם centrality גבוה הם bottlenecks קריטיים
        """
        try:
            centrality = nx.betweenness_centrality(self.graph)
            return centrality
        except Exception as e:
            self.logger.error(f"Error calculating centrality: {e}")
            return {}
    
    def get_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        מחזיר את המסלול הקצר ביותר בין שני קבצים
        """
        try:
            path = nx.shortest_path(self.graph, source, target)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def export_to_dict(self) -> Dict:
        """
        ייצוא לפורמט JSON-friendly
        """
        nodes = []
        for node in self.graph.nodes():
            node_data = dict(self.graph.nodes[node])
            node_data['id'] = node
            nodes.append(node_data)
        
        edges = []
        for source, target in self.graph.edges():
            edge_data = dict(self.graph[source][target])
            edge_data['source'] = source
            edge_data['target'] = target
            edges.append(edge_data)
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': self.get_stats()
        }
    
    def export_for_cytoscape(self) -> Dict:
        """
        ייצוא לפורמט Cytoscape.js
        
        זה הפורמט שה-Frontend יצטרך!
        """
        nodes = []
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            
            # קיצור הנתיב להצגה
            display_name = Path(node_data['relative_path']).name
            
            nodes.append({
                'data': {
                    'id': node,
                    'label': display_name,
                    'full_path': node_data['relative_path'],
                    'lines': node_data['code_lines'],
                    'complexity': node_data['complexity_score'],
                    'type': node_data['node_type'],
                    'has_main': node_data['has_main']
                }
            })
        
        edges = []
        for source, target in self.graph.edges():
            edge_data = self.graph[source][target]
            
            edges.append({
                'data': {
                    'id': f"{source}-{target}",
                    'source': source,
                    'target': target,
                    'type': edge_data['import_type'],
                    'is_relative': edge_data['is_relative']
                }
            })
        
        return {
            'elements': {
                'nodes': nodes,
                'edges': edges
            }
        }
    
    def get_stats(self) -> Dict:
        """סטטיסטיקות על הגרף"""
        if self.graph.number_of_nodes() == 0:
            return {
                'total_nodes': 0,
                'total_edges': 0
            }
        
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'avg_dependencies': sum(dict(self.graph.out_degree()).values()) / self.graph.number_of_nodes(),
            'avg_dependents': sum(dict(self.graph.in_degree()).values()) / self.graph.number_of_nodes(),
            'isolated_nodes': len(self.get_isolated_nodes()),
            'entry_points': len(self.get_entry_points()),
            'circular_dependencies': len(self.find_cycles()),
            'density': nx.density(self.graph)
        }
    
    def visualize_subgraph(self, 
                          center_file: str, 
                          depth: int = 2) -> nx.DiGraph:
        """
        יצירת תת-גרף סביב קובץ מסוים
        
        שימושי לויזואליזציה של "אזור" ספציפי בפרויקט
        
        Args:
            center_file: הקובץ המרכזי
            depth: עומק (כמה רמות של תלויות להציג)
            
        Returns:
            תת-גרף
        """
        if center_file not in self.graph:
            return nx.DiGraph()
        
        # איסוף כל הצמתים הרלוונטיים
        nodes = {center_file}
        
        # תלויות (מה הקובץ משתמש בו)
        deps = self.get_all_dependencies(center_file, max_depth=depth)
        nodes.update(deps)
        
        # תלויים (מי משתמש בקובץ)
        dependents = self.get_all_dependents(center_file, max_depth=depth)
        nodes.update(dependents)
        
        # יצירת תת-גרף
        subgraph = self.graph.subgraph(nodes).copy()
        return subgraph


# Example usage & CLI
if __name__ == "__main__":
    import sys
    from .ast_parser import ASTParser
    from .resolver import ImportResolver
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python graph_builder.py <project_root>")
        sys.exit(1)
    
    project_root = Path(sys.argv[1])
    
    if not project_root.is_dir():
        print(f"Error: {project_root} is not a directory")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Building dependency graph for: {project_root}")
    print(f"{'='*60}\n")
    
    # יצירת הכלים
    parser = ASTParser(skip_stdlib=True)
    resolver = ImportResolver(project_root)
    builder = GraphBuilder(project_root)
    
    # סריקת כל הקבצים
    python_files = list(project_root.rglob("*.py"))
    print(f"Found {len(python_files)} Python files")
    
    for i, py_file in enumerate(python_files, 1):
        # דילוג על תיקיות מיוחדות
        if any(skip in py_file.parts for skip in ["__pycache__", ".venv", "venv"]):
            continue
        
        print(f"[{i}/{len(python_files)}] Analyzing {py_file.name}...", end='\r')
        
        # ניתוח
        analysis = parser.parse_file(py_file)
        if not analysis.is_valid:
            continue
        
        # פתרון imports
        resolved = resolver.resolve_batch(analysis.imports, py_file)
        
        # הוספה לגרף
        builder.add_file_analysis(analysis, resolved)
    
    print("\n")
    
    # בניית הגרף
    graph = builder.build()
    
    # סטטיסטיקות
    print(f"\n{'='*60}")
    print("Graph Statistics:")
    print(f"{'='*60}")
    
    stats = builder.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Hubs
    print(f"\n{'='*60}")
    print("Top 10 Hub Files (most dependents):")
    print(f"{'='*60}")
    
    hubs = builder.get_hub_nodes(threshold=1)
    for file_path, count in hubs[:10]:
        rel_path = Path(file_path).relative_to(project_root)
        print(f"  {count:3d} dependents: {rel_path}")
    
    # Entry points
    print(f"\n{'='*60}")
    print("Entry Points:")
    print(f"{'='*60}")
    
    entry_points = builder.get_entry_points()
    for ep in entry_points[:10]:
        rel_path = Path(ep).relative_to(project_root)
        print(f"  • {rel_path}")
    
    # Circular dependencies
    cycles = builder.find_cycles()
    if cycles:
        print(f"\n{'='*60}")
        print(f"⚠️  Found {len(cycles)} Circular Dependencies:")
        print(f"{'='*60}")
        
        for i, cycle in enumerate(cycles[:5], 1):
            print(f"\nCycle {i}:")
            for file_path in cycle:
                rel_path = Path(file_path).relative_to(project_root)
                print(f"  → {rel_path}")
            print(f"  → {Path(cycle[0]).relative_to(project_root)}")
