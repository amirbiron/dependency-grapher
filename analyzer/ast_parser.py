"""
AST Parser - מנתח קבצי Python באמצעות Abstract Syntax Tree
"""
import ast
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ImportInfo:
    """מידע על import בודד"""
    module: str  # שם המודול (e.g., "os.path")
    names: List[str]  # רשימת שמות שנייבאו (e.g., ["join", "exists"])
    alias: Optional[str] = None  # אליאס אם קיים (e.g., "import pandas as pd")
    level: int = 0  # רמת relative import (0 = absolute, 1 = ".", 2 = "..")
    lineno: int = 0  # מספר שורה
    import_type: str = "unknown"  # "import" או "from"
    
    @property
    def is_relative(self) -> bool:
        """האם זה relative import"""
        return self.level > 0
    
    @property
    def is_standard_library(self) -> bool:
        """בדיקה בסיסית אם זה ספריית סטנדרט"""
        # רשימה חלקית של מודולים בספריית הסטנדרט
        stdlib = {
            'os', 'sys', 'json', 're', 'math', 'random', 'datetime',
            'collections', 'itertools', 'functools', 'pathlib', 'typing',
            'asyncio', 'threading', 'multiprocessing', 'logging', 'unittest',
            'ast', 'io', 'pickle', 'sqlite3', 'csv', 'xml', 'html', 'time',
            'urllib', 'http', 'email', 'hashlib', 'hmac', 'secrets', 'string',
            'textwrap', 'unicodedata', 'struct', 'codecs', 'tempfile', 'shutil',
            'glob', 'fnmatch', 'linecache', 'pickle', 'copy', 'pprint', 'enum',
            'numbers', 'decimal', 'fractions', 'statistics', 'array', 'weakref',
            'types', 'contextlib', 'abc', 'atexit', 'traceback', 'gc', 'inspect'
        }
        root_module = self.module.split('.')[0] if self.module else ""
        return root_module in stdlib


@dataclass
class FunctionInfo:
    """מידע על פונקציה"""
    name: str
    lineno: int
    args: List[str]
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    calls: List[str] = field(default_factory=list)  # פונקציות שנקראות בתוך הפונקציה
    returns_type: Optional[str] = None  # טיפוס החזרה אם צוין


@dataclass
class ClassInfo:
    """מידע על מחלקה"""
    name: str
    lineno: int
    bases: List[str]  # מחלקות בסיס
    methods: List[FunctionInfo]
    decorators: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)  # class-level attributes


@dataclass
class FileAnalysis:
    """תוצאת ניתוח של קובץ בודד"""
    file_path: str
    imports: List[ImportInfo]
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    total_lines: int
    code_lines: int  # שורות קוד ממשיות (ללא הערות/שורות ריקות)
    has_main: bool = False
    encoding: str = "utf-8"
    parse_error: Optional[str] = None
    docstring: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """האם הניתוח הצליח"""
        return self.parse_error is None
    
    @property
    def all_imported_modules(self) -> Set[str]:
        """כל המודולים שנייבאו (כולל standard library)"""
        return {imp.module for imp in self.imports if imp.module}
    
    @property
    def external_imports(self) -> List[ImportInfo]:
        """רק imports שלא מספריית הסטנדרט"""
        return [imp for imp in self.imports if not imp.is_standard_library]
    
    @property
    def complexity_score(self) -> float:
        """ציון מורכבות בסיסי"""
        # מבוסס על מספר פונקציות, מחלקות, ושורות קוד
        return (
            len(self.functions) * 2 +
            len(self.classes) * 3 +
            self.code_lines / 100
        )


class ASTParser:
    """
    מנתח AST של קבצי Python
    
    Example:
        >>> parser = ASTParser()
        >>> analysis = parser.parse_file(Path("my_module.py"))
        >>> print(f"Found {len(analysis.imports)} imports")
    """
    
    def __init__(self, skip_stdlib: bool = True, extract_calls: bool = False):
        """
        Args:
            skip_stdlib: האם לדלג על imports מספריית הסטנדרט
            extract_calls: האם לחלץ קריאות לפונקציות (יכול להיות איטי)
        """
        self.skip_stdlib = skip_stdlib
        self.extract_calls = extract_calls
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def parse_file(self, file_path: Path) -> FileAnalysis:
        """
        מנתח קובץ Python בודד
        
        Args:
            file_path: נתיב לקובץ
            
        Returns:
            FileAnalysis עם כל המידע שנמצא
        """
        self.logger.debug(f"Parsing file: {file_path}")
        
        try:
            # קריאת הקובץ
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # ספירת שורות
            lines = source.split('\n')
            total_lines = len(lines)
            code_lines = sum(1 for line in lines 
                           if line.strip() and not line.strip().startswith('#'))
            
            # פרסור ל-AST
            tree = ast.parse(source, filename=str(file_path))
            
            # חילוץ docstring
            docstring = ast.get_docstring(tree)
            
            # ניתוח
            imports = self._extract_imports(tree)
            functions = self._extract_functions(tree)
            classes = self._extract_classes(tree)
            has_main = self._check_has_main(tree)
            
            return FileAnalysis(
                file_path=str(file_path),
                imports=imports,
                functions=functions,
                classes=classes,
                total_lines=total_lines,
                code_lines=code_lines,
                has_main=has_main,
                docstring=docstring
            )
            
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {file_path}: {e}")
            return FileAnalysis(
                file_path=str(file_path),
                imports=[],
                functions=[],
                classes=[],
                total_lines=0,
                code_lines=0,
                parse_error=f"SyntaxError: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return FileAnalysis(
                file_path=str(file_path),
                imports=[],
                functions=[],
                classes=[],
                total_lines=0,
                code_lines=0,
                parse_error=str(e)
            )
    
    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        """מחלץ את כל ה-imports מה-AST"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # import os, sys
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[alias.name],
                        alias=alias.asname,
                        level=0,
                        lineno=node.lineno,
                        import_type="import"
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                # from os import path
                # from .utils import helper
                module = node.module or ""
                names = [alias.name for alias in node.names]
                
                imports.append(ImportInfo(
                    module=module,
                    names=names,
                    level=node.level,
                    lineno=node.lineno,
                    import_type="from"
                ))
        
        # סינון ספריית סטנדרט אם נדרש
        if self.skip_stdlib:
            imports = [imp for imp in imports if not imp.is_standard_library]
        
        return imports
    
    def _extract_functions(self, tree: ast.AST) -> List[FunctionInfo]:
        """מחלץ את כל הפונקציות (לא כולל methods במחלקות)"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # בדיקה שזו פונקציה ברמת המודול (לא method)
                if not self._is_class_method(tree, node):
                    functions.append(self._parse_function(node))
        
        return functions
    
    def _extract_classes(self, tree: ast.AST) -> List[ClassInfo]:
        """מחלץ את כל המחלקות"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # שמות מחלקות בסיס
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(self._get_full_attr_name(base))
                
                # Methods
                methods = [
                    self._parse_function(item)
                    for item in node.body
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                
                # Decorators
                decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
                
                # Class attributes
                attributes = self._extract_class_attributes(node)
                
                classes.append(ClassInfo(
                    name=node.name,
                    lineno=node.lineno,
                    bases=bases,
                    methods=methods,
                    decorators=decorators,
                    attributes=attributes
                ))
        
        return classes
    
    def _parse_function(self, node: ast.FunctionDef) -> FunctionInfo:
        """מנתח פונקציה בודדת"""
        # ארגומנטים
        args = [arg.arg for arg in node.args.args]
        
        # Decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # קריאות לפונקציות אחרות (אם מופעל)
        calls = []
        if self.extract_calls:
            calls = self._extract_function_calls(node)
        
        # טיפוס החזרה
        returns_type = None
        if node.returns:
            returns_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else None
        
        return FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            args=args,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            calls=calls,
            returns_type=returns_type
        )
    
    def _extract_function_calls(self, func_node: ast.FunctionDef) -> List[str]:
        """מחלץ את כל הקריאות לפונקציות בתוך פונקציה"""
        calls = []
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(self._get_full_attr_name(node.func))
        
        return list(set(calls))  # הסרת כפילויות
    
    def _extract_class_attributes(self, class_node: ast.ClassDef) -> List[str]:
        """מחלץ class-level attributes"""
        attributes = []
        
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    attributes.append(node.target.id)
        
        return attributes
    
    def _check_has_main(self, tree: ast.AST) -> bool:
        """בדיקה אם יש if __name__ == "__main__":"""
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # בדיקה של התנאי
                if isinstance(node.test, ast.Compare):
                    test = node.test
                    # Python < 3.8
                    if (isinstance(test.left, ast.Name) and 
                        test.left.id == '__name__' and
                        any(isinstance(comp, ast.Eq) for comp in test.ops)):
                        for comp in test.comparators:
                            if isinstance(comp, ast.Str) and comp.s == '__main__':
                                return True
                            # Python 3.8+
                            if isinstance(comp, ast.Constant) and comp.value == '__main__':
                                return True
        return False
    
    def _is_class_method(self, tree: ast.AST, func_node: ast.FunctionDef) -> bool:
        """בדיקה אם הפונקציה היא method של מחלקה"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if func_node in node.body:
                    return True
        return False
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """מחזיר את שם ה-decorator"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        elif isinstance(decorator, ast.Attribute):
            return self._get_full_attr_name(decorator)
        return "unknown"
    
    def _get_full_attr_name(self, node: ast.Attribute) -> str:
        """מחזיר שם מלא של attribute (e.g., "app.route")"""
        parts = []
        current = node
        
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        
        if isinstance(current, ast.Name):
            parts.append(current.id)
        
        return '.'.join(reversed(parts))
    
    def parse_directory(self, directory: Path, recursive: bool = True) -> Dict[str, FileAnalysis]:
        """
        מנתח תיקייה שלמה
        
        Args:
            directory: נתיב לתיקייה
            recursive: האם לסרוק גם תתי-תיקיות
            
        Returns:
            מילון של {file_path: FileAnalysis}
        """
        results = {}
        
        pattern = "**/*.py" if recursive else "*.py"
        
        for py_file in directory.glob(pattern):
            # דילוג על קבצים שצריך לדלג
            if any(skip in py_file.parts for skip in ["__pycache__", ".venv", "venv"]):
                continue
            
            analysis = self.parse_file(py_file)
            results[str(py_file)] = analysis
        
        self.logger.info(f"Parsed {len(results)} files in {directory}")
        return results


# Example usage & CLI
if __name__ == "__main__":
    import sys
    import json
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python ast_parser.py <file.py|directory>")
        print("\nExamples:")
        print("  python ast_parser.py mymodule.py")
        print("  python ast_parser.py /path/to/project")
        sys.exit(1)
    
    target = Path(sys.argv[1])
    parser = ASTParser(skip_stdlib=True, extract_calls=True)
    
    if target.is_file():
        # ניתוח קובץ בודד
        result = parser.parse_file(target)
        
        print(f"\n{'='*60}")
        print(f"File: {result.file_path}")
        print(f"{'='*60}")
        print(f"Total lines: {result.total_lines}")
        print(f"Code lines: {result.code_lines}")
        print(f"Has __main__: {result.has_main}")
        print(f"Complexity: {result.complexity_score:.2f}")
        
        if result.docstring:
            print(f"\nDocstring: {result.docstring[:100]}...")
        
        print(f"\n--- Imports ({len(result.imports)}) ---")
        for imp in result.imports:
            rel = "relative" if imp.is_relative else "absolute"
            print(f"  [{imp.import_type}] {imp.module} ({rel}) - line {imp.lineno}")
        
        print(f"\n--- Functions ({len(result.functions)}) ---")
        for func in result.functions:
            async_marker = "async " if func.is_async else ""
            print(f"  {async_marker}{func.name}({', '.join(func.args)}) - line {func.lineno}")
            if func.decorators:
                print(f"    @{', @'.join(func.decorators)}")
            if func.calls:
                print(f"    Calls: {', '.join(func.calls[:5])}")
        
        print(f"\n--- Classes ({len(result.classes)}) ---")
        for cls in result.classes:
            bases = f"({', '.join(cls.bases)})" if cls.bases else ""
            print(f"  class {cls.name}{bases} - line {cls.lineno}")
            for method in cls.methods:
                print(f"    - {method.name}({', '.join(method.args)})")
    
    elif target.is_dir():
        # ניתוח תיקייה
        results = parser.parse_directory(target)
        
        print(f"\n{'='*60}")
        print(f"Directory: {target}")
        print(f"{'='*60}")
        print(f"Total files: {len(results)}")
        
        valid = sum(1 for r in results.values() if r.is_valid)
        print(f"Valid files: {valid}")
        print(f"Errors: {len(results) - valid}")
        
        # סטטיסטיקות
        total_imports = sum(len(r.imports) for r in results.values())
        total_functions = sum(len(r.functions) for r in results.values())
        total_classes = sum(len(r.classes) for r in results.values())
        
        print(f"\nTotal imports: {total_imports}")
        print(f"Total functions: {total_functions}")
        print(f"Total classes: {total_classes}")
        
        # Top 5 most complex files
        by_complexity = sorted(results.values(), key=lambda x: x.complexity_score, reverse=True)
        print(f"\n--- Top 5 Most Complex Files ---")
        for analysis in by_complexity[:5]:
            print(f"  {Path(analysis.file_path).name}: {analysis.complexity_score:.2f}")
    
    else:
        print(f"Error: {target} is not a file or directory")
        sys.exit(1)
