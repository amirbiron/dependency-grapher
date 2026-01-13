"""
Dependency Grapher - AST-based Python dependency analyzer

מנתח תלויות בפרויקטי Python באמצעות Abstract Syntax Tree (AST)
ומייצר גרפים אינטראקטיביים של הקשרים בין קבצים.
"""

from .core import DependencyAnalyzer
from .ast_parser import ASTParser, FileAnalysis, ImportInfo
from .graph_builder import GraphBuilder
from .resolver import ImportResolver, ResolvedImport
from .metrics import MetricsCalculator

__version__ = "0.1.0"
__author__ = "Amir Haim"

__all__ = [
    "DependencyAnalyzer",
    "ASTParser",
    "FileAnalysis",
    "ImportInfo",
    "GraphBuilder",
    "ImportResolver",
    "ResolvedImport",
    "MetricsCalculator"
]
