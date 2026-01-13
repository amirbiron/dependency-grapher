"""
Flask API Server for Dependency Grapher

נקודות קצה:
- POST /api/analyze - התחלת ניתוח פרויקט
- GET /api/analysis/{id} - קבלת סטטוס ניתוח
- GET /api/analysis/{id}/graph - קבלת הגרף
- GET /api/analysis/{id}/blast-radius/{file} - Blast Radius לקובץ
- GET /api/analysis/{id}/risk-files - Top risk files
- GET /api/analysis/{id}/metrics - מטריקות הפרויקט
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from .database import db, DatabaseUnavailable
from .tasks import AnalysisTask
from .utils import validate_repo_url, generate_analysis_id

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config.from_object('config.config')

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize database
db.init_app(app)


# ============================================
# Error Handlers
# ============================================

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """טיפול בשגיאות HTTP"""
    response = {
        "error": e.name,
        "message": e.description,
        "status_code": e.code
    }
    return jsonify(response), e.code


@app.errorhandler(Exception)
def handle_exception(e):
    """טיפול בשגיאות כלליות"""
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    response = {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "status_code": 500
    }
    return jsonify(response), 500


@app.errorhandler(DatabaseUnavailable)
def handle_db_unavailable(e):
    """Return a clear 503 when MongoDB isn't available."""
    return jsonify({
        "error": "Service Unavailable",
        "message": str(e),
        "status_code": 503
    }), 503


# ============================================
# Health Check
# ============================================

@app.route('/', methods=['GET'])
def root():
    """Root route (useful for platform health checks)."""
    return jsonify({
        "service": "dependency-grapher-api",
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "api_health": "/api/health",
            "start_analysis": "/api/analyze"
        }
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """בדיקת תקינות השרת"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    })


@app.route('/api/health', methods=['GET'])
def api_health_check():
    """בדיקת תקינות API"""
    # בדיקת חיבור ל-MongoDB
    try:
        db_status = db.check_connection()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    })


# ============================================
# Analysis Endpoints
# ============================================

@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    """
    התחלת ניתוח פרויקט חדש
    
    Body:
    {
        "repo_url": "https://github.com/user/repo",
        "branch": "main",  // optional
        "skip_stdlib": true  // optional
    }
    
    Response:
    {
        "analysis_id": "abc123",
        "status": "pending",
        "message": "Analysis started"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'repo_url' not in data:
            return jsonify({
                "error": "Bad Request",
                "message": "repo_url is required"
            }), 400
        
        repo_url = data['repo_url']
        branch = data.get('branch', 'main')
        skip_stdlib = data.get('skip_stdlib', True)
        
        # Validate repo URL
        if not validate_repo_url(repo_url):
            return jsonify({
                "error": "Bad Request",
                "message": "Invalid repository URL"
            }), 400
        
        # בדיקה אם כבר יש ניתוח לrepo הזה
        existing = db.find_analysis_by_repo(repo_url)
        if existing and existing['status'] == 'complete':
            # אם יש ניתוח מוכן, החזר אותו
            return jsonify({
                "analysis_id": existing['analysis_id'],
                "status": "complete",
                "message": "Analysis already exists",
                "cached": True
            }), 200
        
        # יצירת analysis ID
        analysis_id = generate_analysis_id()
        
        # שמירה ראשונית ב-DB
        db.create_analysis({
            "analysis_id": analysis_id,
            "repo_url": repo_url,
            "branch": branch,
            "skip_stdlib": skip_stdlib,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # התחלת ניתוח ברקע
        task = AnalysisTask(analysis_id, repo_url, branch, skip_stdlib)
        task.start()
        
        logger.info(f"Started analysis {analysis_id} for {repo_url}")
        
        return jsonify({
            "analysis_id": analysis_id,
            "status": "pending",
            "message": "Analysis started successfully"
        }), 202
        
    except Exception as e:
        logger.error(f"Error starting analysis: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@app.route('/api/analysis/<analysis_id>', methods=['GET'])
def get_analysis(analysis_id: str):
    """
    קבלת סטטוס ומידע על ניתוח
    
    Response:
    {
        "analysis_id": "abc123",
        "repo_url": "...",
        "status": "complete|pending|error",
        "progress": 75,  // אחוזי התקדמות
        "created_at": "...",
        "updated_at": "...",
        "summary": {...}  // אם complete
    }
    """
    try:
        analysis = db.get_analysis(analysis_id)
        
        if not analysis:
            return jsonify({
                "error": "Not Found",
                "message": f"Analysis {analysis_id} not found"
            }), 404
        
        # הסרת _id של MongoDB (לא serializable)
        if '_id' in analysis:
            del analysis['_id']
        
        return jsonify(analysis), 200
        
    except Exception as e:
        logger.error(f"Error getting analysis: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@app.route('/api/analysis/<analysis_id>/graph', methods=['GET'])
def get_graph(analysis_id: str):
    """
    קבלת הגרף המלא בפורמט Cytoscape
    
    Query params:
    - format: "cytoscape" (default) או "networkx"
    
    Response:
    {
        "elements": {
            "nodes": [...],
            "edges": [...]
        }
    }
    """
    try:
        analysis = db.get_analysis(analysis_id)
        
        if not analysis:
            return jsonify({
                "error": "Not Found",
                "message": f"Analysis {analysis_id} not found"
            }), 404
        
        if analysis['status'] != 'complete':
            return jsonify({
                "error": "Bad Request",
                "message": f"Analysis is {analysis['status']}, not complete"
            }), 400
        
        format_type = request.args.get('format', 'cytoscape')
        
        if format_type == 'cytoscape':
            graph_data = analysis.get('graph_cytoscape', {})
        else:
            graph_data = analysis.get('graph_data', {})
        
        return jsonify(graph_data), 200
        
    except Exception as e:
        logger.error(f"Error getting graph: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@app.route('/api/analysis/<analysis_id>/blast-radius/<path:file_path>', methods=['GET'])
def get_blast_radius(analysis_id: str, file_path: str):
    """
    קבלת Blast Radius לקובץ ספציפי
    
    Response:
    {
        "file_path": "...",
        "direct_dependents": [...],
        "indirect_dependents": [...],
        "total_affected": 23,
        "risk_score": 87.3,
        "risk_level": "high"
    }
    """
    try:
        # בדיקה אם יש ב-cache
        cached = db.get_cached_blast_radius(analysis_id, file_path)
        if cached:
            return jsonify(cached), 200
        
        # אם לא, טען את הניתוח וחשב
        analysis = db.get_analysis(analysis_id)
        
        if not analysis:
            return jsonify({
                "error": "Not Found",
                "message": f"Analysis {analysis_id} not found"
            }), 404
        
        if analysis['status'] != 'complete':
            return jsonify({
                "error": "Bad Request",
                "message": f"Analysis is {analysis['status']}"
            }), 400
        
        # חישוב Blast Radius
        # (נטען את הגרף ונחשב - זה יהיה במשימה נפרדת)
        blast_data = _calculate_blast_radius_from_analysis(analysis, file_path)
        
        # שמירה ב-cache
        db.cache_blast_radius(analysis_id, file_path, blast_data)
        
        return jsonify(blast_data), 200
        
    except Exception as e:
        logger.error(f"Error calculating blast radius: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@app.route('/api/analysis/<analysis_id>/risk-files', methods=['GET'])
def get_risk_files(analysis_id: str):
    """
    קבלת Top Risk Files
    
    Query params:
    - limit: מספר תוצאות (default: 10)
    
    Response:
    {
        "risk_files": [
            {
                "file_path": "...",
                "risk_score": 87.3,
                "risk_level": "high",
                "blast_radius": 23
            },
            ...
        ]
    }
    """
    try:
        limit = int(request.args.get('limit', 10))
        
        analysis = db.get_analysis(analysis_id)
        
        if not analysis:
            return jsonify({
                "error": "Not Found",
                "message": f"Analysis {analysis_id} not found"
            }), 404
        
        if analysis['status'] != 'complete':
            return jsonify({
                "error": "Bad Request",
                "message": "Analysis not complete"
            }), 400
        
        risk_files = analysis.get('top_risk_files', [])[:limit]
        
        return jsonify({
            "risk_files": risk_files,
            "total": len(analysis.get('top_risk_files', []))
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting risk files: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@app.route('/api/analysis/<analysis_id>/metrics', methods=['GET'])
def get_metrics(analysis_id: str):
    """
    קבלת מטריקות הפרויקט
    
    Response:
    {
        "graph_stats": {...},
        "project_metrics": {...},
        "circular_dependencies": [...]
    }
    """
    try:
        analysis = db.get_analysis(analysis_id)
        
        if not analysis:
            return jsonify({
                "error": "Not Found",
                "message": f"Analysis {analysis_id} not found"
            }), 404
        
        if analysis['status'] != 'complete':
            return jsonify({
                "error": "Bad Request",
                "message": "Analysis not complete"
            }), 400
        
        return jsonify({
            "graph_stats": analysis.get('graph_stats', {}),
            "project_metrics": analysis.get('project_metrics', {}),
            "circular_dependencies": analysis.get('circular_dependencies', [])
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@app.route('/api/analysis/<analysis_id>/files', methods=['GET'])
def get_files(analysis_id: str):
    """
    קבלת רשימת כל הקבצים בפרויקט
    
    Query params:
    - search: חיפוש לפי שם
    - risk_level: סינון לפי רמת סיכון (low/medium/high/critical)
    
    Response:
    {
        "files": [
            {
                "path": "...",
                "name": "...",
                "lines": 150,
                "risk_score": 45.2
            },
            ...
        ]
    }
    """
    try:
        search = request.args.get('search', '').lower()
        risk_level = request.args.get('risk_level', None)
        
        analysis = db.get_analysis(analysis_id)
        
        if not analysis:
            return jsonify({
                "error": "Not Found",
                "message": f"Analysis {analysis_id} not found"
            }), 404
        
        if analysis['status'] != 'complete':
            return jsonify({
                "error": "Bad Request",
                "message": "Analysis not complete"
            }), 400
        
        # חילוץ קבצים מהגרף
        graph_data = analysis.get('graph_data', {})
        nodes = graph_data.get('nodes', [])
        
        files = []
        for node in nodes:
            file_path = node.get('relative_path', '')
            file_name = Path(file_path).name
            
            # סינון חיפוש
            if search and search not in file_path.lower():
                continue
            
            # סינון risk level
            # (נצטרך להוסיף risk_level לכל node בניתוח)
            
            files.append({
                "path": file_path,
                "name": file_name,
                "lines": node.get('code_lines', 0),
                "complexity": node.get('complexity_score', 0),
                "type": node.get('node_type', 'module')
            })
        
        return jsonify({
            "files": files,
            "total": len(files)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@app.route('/api/analysis/<analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id: str):
    """
    מחיקת ניתוח
    """
    try:
        result = db.delete_analysis(analysis_id)
        
        if not result:
            return jsonify({
                "error": "Not Found",
                "message": f"Analysis {analysis_id} not found"
            }), 404
        
        return jsonify({
            "message": "Analysis deleted successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting analysis: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


# ============================================
# List & Search
# ============================================

@app.route('/api/analyses', methods=['GET'])
def list_analyses():
    """
    רשימת כל הניתוחים
    
    Query params:
    - limit: מספר תוצאות (default: 20)
    - offset: offset (default: 0)
    - status: סינון לפי סטטוס
    
    Response:
    {
        "analyses": [...],
        "total": 45,
        "limit": 20,
        "offset": 0
    }
    """
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        status = request.args.get('status', None)
        
        analyses = db.list_analyses(limit, offset, status)
        total = db.count_analyses(status)
        
        # הסרת _id
        for analysis in analyses:
            if '_id' in analysis:
                del analysis['_id']
        
        return jsonify({
            "analyses": analyses,
            "total": total,
            "limit": limit,
            "offset": offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing analyses: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


# ============================================
# Helper Functions
# ============================================

def _calculate_blast_radius_from_analysis(analysis: Dict, file_path: str) -> Dict:
    """
    חישוב Blast Radius מתוך נתוני הניתוח
    
    מחפש את הנתונים ב-top_risk_files או בגרף השמור
    """
    # נסה למצוא את הקובץ ב-top_risk_files
    top_risk_files = analysis.get('top_risk_files', [])
    for risk_file in top_risk_files:
        # השוואה של הנתיב (יכול להיות מלא או יחסי)
        if risk_file.get('file_path', '').endswith(file_path) or file_path.endswith(risk_file.get('file_path', '')):
            return {
                "file_path": file_path,
                "direct_dependents": [],  # אין לנו את הפירוט המלא
                "indirect_dependents": [],
                "total_affected": risk_file.get('blast_radius', 0),
                "max_depth": 0,
                "risk_score": risk_file.get('risk_score', 0),
                "risk_level": risk_file.get('risk_level', 'low'),
                "risk_factors": risk_file.get('risk_factors', [])
            }
    
    # אם לא נמצא ב-top_risk_files, נסה לחפש בגרף
    graph_data = analysis.get('graph_data', {})
    nodes = graph_data.get('nodes', [])
    
    for node in nodes:
        node_path = node.get('relative_path', '') or node.get('file_path', '')
        if node_path.endswith(file_path) or file_path.endswith(node_path):
            # מצאנו את הצומת, אבל אין לנו מידע מלא על blast radius
            return {
                "file_path": file_path,
                "direct_dependents": [],
                "indirect_dependents": [],
                "total_affected": 0,
                "max_depth": 0,
                "risk_score": node.get('complexity_score', 0) * 10,  # הערכה גסה
                "risk_level": "low"
            }
    
    # לא נמצא - החזר ברירת מחדל
    return {
        "file_path": file_path,
        "direct_dependents": [],
        "indirect_dependents": [],
        "total_affected": 0,
        "max_depth": 0,
        "risk_score": 0,
        "risk_level": "low"
    }


# ============================================
# Run Server
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
