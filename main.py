#!/usr/bin/env python3
"""
Dependency Grapher - Main Entry Point

דוגמאות שימוש:

1. ניתוח פרויקט:
   python main.py /path/to/project

2. ניתוח קובץ ספציפי:
   python main.py /path/to/project --file myapp/core.py

3. ייצוא ל-JSON:
   python main.py /path/to/project --export results.json

4. ייצוא ל-Cytoscape:
   python main.py /path/to/project --cytoscape graph.json
"""

from analyzer.core import main

if __name__ == "__main__":
    main()
