#!/usr/bin/env python3
"""
Development Server Runner

להרצה בפיתוח:
    python api/run.py

לייצור:
    gunicorn api.app:app
"""

import os
import sys
from pathlib import Path

# הוספת root לpath
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from api.app import app

# טעינת .env
load_dotenv()

if __name__ == '__main__':
    # הגדרות פיתוח
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"""
    ╔════════════════════════════════════════╗
    ║  Dependency Grapher API Server         ║
    ╠════════════════════════════════════════╣
    ║  Running on: http://localhost:{port}    ║
    ║  Debug mode: {debug}                       ║
    ╚════════════════════════════════════════╝
    """)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
