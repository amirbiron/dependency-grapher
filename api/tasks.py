"""
Background Tasks for Analysis

משימות שרצות ברקע (threading או Celery)
"""

import os
import logging
import tempfile
import shutil
import threading
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import GitCommandError

from analyzer import DependencyAnalyzer
from .database import db
from .utils import cleanup_temp_dir

logger = logging.getLogger(__name__)


class AnalysisTask:
    """
    משימת ניתוח שרצה ברקע
    
    Example:
        task = AnalysisTask(analysis_id, repo_url)
        task.start()
    """
    
    def __init__(self, 
                 analysis_id: str,
                 repo_url: str,
                 branch: str = "main",
                 skip_stdlib: bool = True):
        """
        Args:
            analysis_id: מזהה ייחודי לניתוח
            repo_url: URL של הrepo
            branch: ענף לניתוח
            skip_stdlib: האם לדלג על ספריית סטנדרט
        """
        self.analysis_id = analysis_id
        self.repo_url = repo_url
        self.branch = branch
        self.skip_stdlib = skip_stdlib
        
        self.temp_dir: Optional[Path] = None
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """התחלת המשימה ברקע"""
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        logger.info(f"Started background task for analysis {self.analysis_id}")
    
    def run(self):
        """הרצת המשימה (לא לקרוא ישירות - רק דרך start())"""
        try:
            logger.info(f"Running analysis {self.analysis_id} for {self.repo_url}")
            
            # עדכון סטטוס
            db.update_analysis_status(self.analysis_id, "processing")
            db.update_analysis_progress(self.analysis_id, 0, "Starting analysis...")
            
            # שלב 1: Clone הrepo (20%)
            logger.info(f"[{self.analysis_id}] Cloning repository...")
            db.update_analysis_progress(self.analysis_id, 10, "Cloning repository...")
            
            self.temp_dir = self._clone_repo()
            
            db.update_analysis_progress(self.analysis_id, 20, "Repository cloned")
            
            # שלב 2: ניתוח (60%)
            logger.info(f"[{self.analysis_id}] Analyzing project...")
            db.update_analysis_progress(self.analysis_id, 30, "Analyzing dependencies...")
            
            analyzer = DependencyAnalyzer(
                self.temp_dir,
                skip_stdlib=self.skip_stdlib
            )
            
            # ניתוח עם progress callback
            def progress_callback(current, total):
                percent = int((current / total) * 40) + 30  # 30-70%
                db.update_analysis_progress(
                    self.analysis_id, 
                    percent,
                    f"Analyzing file {current}/{total}..."
                )
            
            result = analyzer.analyze(progress_callback=progress_callback)
            
            db.update_analysis_progress(self.analysis_id, 70, "Generating graph...")
            
            # שלב 3: ייצוא נתונים (20%)
            logger.info(f"[{self.analysis_id}] Exporting data...")
            
            # ייצוא לפורמט Cytoscape
            graph_cytoscape = analyzer.builder.export_for_cytoscape()
            
            # ייצוא לפורמט רגיל
            graph_data = analyzer.builder.export_to_dict()
            
            db.update_analysis_progress(self.analysis_id, 90, "Finalizing...")
            
            # שלב 4: שמירה ב-DB
            logger.info(f"[{self.analysis_id}] Saving results...")
            
            # Extract summary from result.to_dict() to avoid double nesting
            # result.to_dict() returns { summary: { total_files, ... }, ... }
            # We want status.summary.total_files, not status.summary.summary.total_files
            result_dict = result.to_dict()
            
            analysis_results = {
                "summary": result_dict.get('summary', {}),
                "graph_cytoscape": graph_cytoscape,
                "graph_data": graph_data,
                "graph_stats": result.graph_stats,
                "project_metrics": result.project_metrics,
                "top_risk_files": result.top_risk_files,
                "circular_dependencies": result.circular_dependencies
            }
            
            db.complete_analysis(self.analysis_id, analysis_results)
            
            logger.info(f"[{self.analysis_id}] Analysis completed successfully")
            
        except Exception as e:
            logger.error(f"[{self.analysis_id}] Analysis failed: {str(e)}", exc_info=True)
            db.update_analysis_status(
                self.analysis_id, 
                "error",
                error=str(e)
            )
        
        finally:
            # ניקוי
            self._cleanup()
    
    def _clone_repo(self) -> Path:
        """
        Clone הrepo לתיקייה זמנית
        
        Returns:
            נתיב לתיקייה הזמנית
        """
        try:
            # יצירת תיקייה זמנית
            temp_dir = Path(tempfile.mkdtemp(prefix=f"dep_graph_{self.analysis_id}_"))
            
            logger.info(f"Cloning {self.repo_url} to {temp_dir}")
            
            # Clone
            Repo.clone_from(
                self.repo_url,
                temp_dir,
                branch=self.branch,
                depth=1  # shallow clone לביצועים
            )
            
            logger.info(f"Successfully cloned to {temp_dir}")
            
            return temp_dir
            
        except GitCommandError as e:
            logger.error(f"Git clone failed: {str(e)}")
            raise Exception(f"Failed to clone repository: {str(e)}")
        except Exception as e:
            logger.error(f"Clone error: {str(e)}")
            raise
    
    def _cleanup(self):
        """ניקוי תיקיות זמניות"""
        if self.temp_dir and self.temp_dir.exists():
            try:
                cleanup_temp_dir(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
            except Exception as e:
                logger.error(f"Failed to cleanup temp dir: {str(e)}")


# ============================================
# Celery Alternative (Optional)
# ============================================

# אם רוצים להשתמש ב-Celery במקום threading:

"""
from celery import Celery

celery = Celery(
    'dependency_grapher',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

@celery.task(bind=True)
def analyze_repo_celery(self, analysis_id, repo_url, branch, skip_stdlib):
    '''
    משימת Celery לניתוח
    '''
    try:
        # עדכון התקדמות
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100})
        
        # Clone
        temp_dir = Path(tempfile.mkdtemp())
        Repo.clone_from(repo_url, temp_dir, branch=branch, depth=1)
        
        self.update_state(state='PROGRESS', meta={'current': 20, 'total': 100})
        
        # ניתוח
        analyzer = DependencyAnalyzer(temp_dir, skip_stdlib=skip_stdlib)
        
        def progress_callback(current, total):
            percent = int((current / total) * 60) + 20
            self.update_state(
                state='PROGRESS', 
                meta={'current': percent, 'total': 100}
            )
        
        result = analyzer.analyze(progress_callback=progress_callback)
        
        # ייצוא
        graph_cytoscape = analyzer.builder.export_for_cytoscape()
        graph_data = analyzer.builder.export_to_dict()
        
        self.update_state(state='PROGRESS', meta={'current': 90, 'total': 100})
        
        # שמירה
        analysis_results = {
            "summary": result.to_dict(),
            "graph_cytoscape": graph_cytoscape,
            "graph_data": graph_data,
            "graph_stats": result.graph_stats,
            "project_metrics": result.project_metrics,
            "top_risk_files": result.top_risk_files,
            "circular_dependencies": result.circular_dependencies
        }
        
        db.complete_analysis(analysis_id, analysis_results)
        
        # ניקוי
        shutil.rmtree(temp_dir)
        
        return {'status': 'complete'}
        
    except Exception as e:
        db.update_analysis_status(analysis_id, "error", error=str(e))
        raise
"""
