"""
Import Resolver - פותר את הנתיבים האמיתיים של imports
"""
from pathlib import Path
from typing import Optional, Dict, Set, List
from dataclasses import dataclass
import logging

from .ast_parser import ImportInfo

logger = logging.getLogger(__name__)


@dataclass
class ResolvedImport:
    """Import שנפתר לנתיב קובץ אמיתי"""
    original_import: ImportInfo
    resolved_path: Optional[Path]
    is_external: bool  # חיצוני (pip package)
    is_builtin: bool   # ספריית סטנדרט
    resolution_method: str  # איך פתרנו אותו
    confidence: float = 1.0  # רמת ביטחון (0-1)
    
    @property
    def is_local(self) -> bool:
        """האם זה import מקומי (מהפרויקט עצמו)"""
        return not self.is_external and not self.is_builtin and self.resolved_path is not None
    
    @property
    def is_resolved(self) -> bool:
        """האם הצלחנו לפתור את ה-import"""
        return self.resolved_path is not None or self.is_builtin


class ImportResolver:
    """
    פותר imports לנתיבי קבצים אמיתיים
    
    אתגרים שהוא פותר:
    1. Relative imports: from ..utils import helper
    2. Package imports: from mypackage.module import func
    3. __init__.py: from mypackage import Something
    4. Nested packages: from deep.nested.package import module
    
    Example:
        >>> resolver = ImportResolver(Path("my_project"))
        >>> import_info = ImportInfo(module="utils.helpers", ...)
        >>> resolved = resolver.resolve(import_info, current_file)
        >>> print(resolved.resolved_path)
    """
    
    def __init__(self, project_root: Path):
        """
        Args:
            project_root: שורש הפרויקט
        """
        self.project_root = project_root.resolve()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Cache של נתיבים שכבר נפתרו
        self._resolution_cache: Dict[str, Optional[Path]] = {}
        
        # מפה של כל קבצי הפייתון בפרויקט
        # {relative_path: absolute_path}
        self._project_files: Dict[str, Path] = {}
        
        # מפה של packages (תיקיות עם __init__.py)
        self._packages: Set[Path] = set()
        
        self._build_project_index()
    
    def _build_project_index(self):
        """בונה אינדקס של כל קבצי ה-Python בפרויקט"""
        self.logger.info(f"Building project index from {self.project_root}")
        
        for py_file in self.project_root.rglob("*.py"):
            # דילוג על קבצים בתיקיות שצריך לדלג עליהן
            if any(skip in py_file.parts for skip in ["__pycache__", ".venv", "venv", "env", ".git"]):
                continue
            
            # נתיב יחסי
            try:
                rel_path = py_file.relative_to(self.project_root)
                self._project_files[str(rel_path)] = py_file
                
                # אם זה __init__.py, התיקייה היא package
                if py_file.name == "__init__.py":
                    self._packages.add(py_file.parent)
                    
            except ValueError:
                # קובץ מחוץ ל-project_root
                continue
        
        self.logger.info(f"Found {len(self._project_files)} Python files")
        self.logger.info(f"Found {len(self._packages)} packages")
    
    def resolve(self, 
                import_info: ImportInfo, 
                current_file: Path) -> ResolvedImport:
        """
        פותר import לנתיב קובץ
        
        Args:
            import_info: המידע על ה-import
            current_file: הקובץ שבו ה-import מופיע
            
        Returns:
            ResolvedImport עם הנתיב שנפתר (או None אם לא נמצא)
        """
        # המרה לנתיב מוחלט
        current_file = current_file.resolve()
        
        # בדיקה ב-cache
        cache_key = f"{current_file}::{import_info.module}::{import_info.level}"
        if cache_key in self._resolution_cache:
            cached_path = self._resolution_cache[cache_key]
            return ResolvedImport(
                original_import=import_info,
                resolved_path=cached_path,
                is_external=cached_path is None,
                is_builtin=import_info.is_standard_library,
                resolution_method="cache",
                confidence=1.0
            )
        
        # ספריית סטנדרט - לא צריך לפתור
        if import_info.is_standard_library:
            return ResolvedImport(
                original_import=import_info,
                resolved_path=None,
                is_external=False,
                is_builtin=True,
                resolution_method="builtin",
                confidence=1.0
            )
        
        # ניסיון פתרון לפי סוג ה-import
        resolved_path = None
        method = "none"
        confidence = 0.0
        
        if import_info.is_relative:
            resolved_path = self._resolve_relative(import_info, current_file)
            method = "relative"
            confidence = 0.9 if resolved_path else 0.0
        else:
            resolved_path = self._resolve_absolute(import_info)
            method = "absolute"
            confidence = 0.8 if resolved_path else 0.0
        
        # שמירה ב-cache
        self._resolution_cache[cache_key] = resolved_path
        
        # קביעה אם זה external (לא נמצא בפרויקט)
        is_external = resolved_path is None and not import_info.is_standard_library
        
        return ResolvedImport(
            original_import=import_info,
            resolved_path=resolved_path,
            is_external=is_external,
            is_builtin=False,
            resolution_method=method,
            confidence=confidence
        )
    
    def _resolve_relative(self, 
                         import_info: ImportInfo, 
                         current_file: Path) -> Optional[Path]:
        """
        פותר relative import
        
        דוגמה:
        - קובץ: myproject/webapp/routes/api.py
        - import: from ..utils import helper (level=2)
        - תוצאה: myproject/webapp/utils.py או myproject/webapp/utils/__init__.py
        """
        # מיקום נוכחי
        current_dir = current_file.parent
        
        # עליה במספר רמות לפי ה-level
        target_dir = current_dir
        for _ in range(import_info.level):
            if target_dir == self.project_root:
                self.logger.warning(
                    f"Relative import at root level: {import_info.module} in {current_file}"
                )
                return None
            target_dir = target_dir.parent
            if not target_dir.is_relative_to(self.project_root):
                self.logger.warning(
                    f"Relative import goes outside project: {import_info.module}"
                )
                return None
        
        # הוספת הנתיב של המודול
        if import_info.module:
            module_parts = import_info.module.split('.')
            for part in module_parts:
                target_dir = target_dir / part
        
        # חיפוש הקובץ
        return self._find_module_file(target_dir)
    
    def _resolve_absolute(self, import_info: ImportInfo) -> Optional[Path]:
        """
        פותר absolute import
        
        דוגמה:
        - import: from database.manager import DatabaseManager
        - חיפוש: project_root/database/manager.py
        """
        if not import_info.module:
            return None
        
        # המרת שם מודול לנתיב
        module_parts = import_info.module.split('.')
        
        # נסה מהשורש
        target_path = self.project_root
        for part in module_parts:
            target_path = target_path / part
        
        return self._find_module_file(target_path)
    
    def _find_module_file(self, base_path: Path) -> Optional[Path]:
        """
        מחפש את קובץ המודול
        
        נסיונות:
        1. base_path.py (קובץ בודד)
        2. base_path/__init__.py (package)
        
        Args:
            base_path: הנתיב הבסיסי לחיפוש
            
        Returns:
            הנתיב המוחלט לקובץ, או None אם לא נמצא
        """
        # נסיון 1: קובץ בודד
        py_file = base_path.with_suffix('.py')
        try:
            rel_path = str(py_file.relative_to(self.project_root))
            if rel_path in self._project_files:
                return self._project_files[rel_path]
        except ValueError:
            pass
        
        # נסיון 2: package (תיקייה עם __init__.py)
        init_file = base_path / '__init__.py'
        try:
            rel_path = str(init_file.relative_to(self.project_root))
            if rel_path in self._project_files:
                return self._project_files[rel_path]
        except ValueError:
            pass
        
        # לא נמצא
        self.logger.debug(f"Could not resolve: {base_path}")
        return None
    
    def resolve_batch(self, 
                     imports: List[ImportInfo], 
                     current_file: Path) -> List[ResolvedImport]:
        """פותר כמה imports בבת אחת"""
        return [self.resolve(imp, current_file) for imp in imports]
    
    def is_package(self, directory: Path) -> bool:
        """בדיקה אם תיקייה היא Python package"""
        return directory in self._packages
    
    def get_package_files(self, package_dir: Path) -> List[Path]:
        """מחזיר את כל הקבצים ב-package"""
        files = []
        for rel_path, abs_path in self._project_files.items():
            try:
                if abs_path.is_relative_to(package_dir):
                    files.append(abs_path)
            except (ValueError, AttributeError):
                continue
        return files
    
    def get_stats(self) -> Dict[str, int]:
        """סטטיסטיקות על הפתרון"""
        external_count = sum(
            1 for path in self._resolution_cache.values()
            if path is None
        )
        
        return {
            "total_files": len(self._project_files),
            "total_packages": len(self._packages),
            "cached_resolutions": len(self._resolution_cache),
            "external_imports": external_count,
            "resolved_imports": len(self._resolution_cache) - external_count
        }
    
    def clear_cache(self):
        """מנקה את ה-cache"""
        self._resolution_cache.clear()
        self.logger.info("Resolution cache cleared")
    
    def refresh_index(self):
        """מרענן את האינדקס (שימושי אם הפרויקט השתנה)"""
        self._project_files.clear()
        self._packages.clear()
        self.clear_cache()
        self._build_project_index()


# Example usage & CLI
if __name__ == "__main__":
    import sys
    from .ast_parser import ASTParser
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python resolver.py <project_root> [test_file]")
        print("\nExamples:")
        print("  python resolver.py /path/to/project")
        print("  python resolver.py /path/to/project /path/to/project/main.py")
        sys.exit(1)
    
    project_root = Path(sys.argv[1])
    
    if not project_root.is_dir():
        print(f"Error: {project_root} is not a directory")
        sys.exit(1)
    
    # בניית resolver
    resolver = ImportResolver(project_root)
    
    print(f"\n{'='*60}")
    print(f"Project: {project_root}")
    print(f"{'='*60}")
    print("Stats:", resolver.get_stats())
    
    # אם צוין קובץ לבדיקה
    if len(sys.argv) > 2:
        test_file = Path(sys.argv[2])
        
        if not test_file.is_file():
            print(f"Error: {test_file} is not a file")
            sys.exit(1)
        
        # ניתוח הקובץ
        parser = ASTParser(skip_stdlib=False)
        analysis = parser.parse_file(test_file)
        
        print(f"\n{'='*60}")
        print(f"Resolving imports in: {test_file.name}")
        print(f"{'='*60}\n")
        
        for imp in analysis.imports:
            resolved = resolver.resolve(imp, test_file)
            
            # אייקון לפי סטטוס
            if resolved.is_builtin:
                icon = "📚"
                status = "BUILTIN"
            elif resolved.is_external:
                icon = "📦"
                status = "EXTERNAL"
            elif resolved.is_local:
                icon = "✅"
                status = "RESOLVED"
            else:
                icon = "❌"
                status = "NOT FOUND"
            
            print(f"{icon} [{status}] {imp.module}")
            print(f"   Type: {imp.import_type}, Level: {imp.level}")
            
            if resolved.resolved_path:
                try:
                    rel = resolved.resolved_path.relative_to(project_root)
                    print(f"   Path: {rel}")
                except ValueError:
                    print(f"   Path: {resolved.resolved_path}")
            
            print(f"   Method: {resolved.resolution_method}, Confidence: {resolved.confidence:.0%}")
            print()
    
    else:
        # סריקה כללית
        print(f"\n{'='*60}")
        print("Packages found:")
        print(f"{'='*60}")
        
        for package in sorted(resolver._packages):
            try:
                rel = package.relative_to(project_root)
                files = resolver.get_package_files(package)
                print(f"  📁 {rel} ({len(files)} files)")
            except ValueError:
                continue
