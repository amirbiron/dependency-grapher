"""
MongoDB Database Layer for Dependency Grapher

Collections:
- analyses: מידע על ניתוחים
- blast_radius_cache: cache של חישובי blast radius
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure

logger = logging.getLogger(__name__)


class Database:
    """
    מנהל חיבור ל-MongoDB ופעולות CRUD
    """
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.analyses_collection = None
        self.cache_collection = None
    
    def init_app(self, app):
        """
        אתחול החיבור ל-MongoDB
        
        Args:
            app: Flask application
        """
        try:
            mongodb_uri = app.config.get('MONGODB_URI') or os.getenv('MONGODB_URI')
            database_name = app.config.get('DATABASE_NAME') or os.getenv('DATABASE_NAME', 'dependency_grapher')
            
            if not mongodb_uri:
                logger.warning("MONGODB_URI not set, using localhost")
                mongodb_uri = "mongodb://localhost:27017/"
            
            # יצירת חיבור
            self.client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            
            # בדיקת חיבור
            self.client.admin.command('ping')
            
            # בחירת database
            self.db = self.client[database_name]
            
            # Collections
            self.analyses_collection = self.db['analyses']
            self.cache_collection = self.db['blast_radius_cache']
            
            # יצירת indexes
            self._create_indexes()
            
            logger.info(f"Connected to MongoDB: {database_name}")
            
        except Exception as e:
            # לא מפילים את השרת אם ה-DB לא זמין (בריאות/API בסיסי עדיין יכולים לעבוד).
            # קריאות שתלויות ב-DB יחזירו שגיאה בהמשך.
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
            self.analyses_collection = None
            self.cache_collection = None
            return
    
    def _create_indexes(self):
        """יצירת indexes לביצועים"""
        try:
            # Index על analysis_id
            self.analyses_collection.create_index(
                [("analysis_id", ASCENDING)],
                unique=True
            )
            
            # Index על repo_url
            self.analyses_collection.create_index(
                [("repo_url", ASCENDING)]
            )
            
            # Index על status
            self.analyses_collection.create_index(
                [("status", ASCENDING)]
            )
            
            # Index על created_at
            self.analyses_collection.create_index(
                [("created_at", DESCENDING)]
            )
            
            # Index על cache (analysis_id + file_path)
            self.cache_collection.create_index(
                [("analysis_id", ASCENDING), ("file_path", ASCENDING)],
                unique=True
            )
            
            # TTL index על cache (מחיקה אוטומטית אחרי 7 ימים)
            self.cache_collection.create_index(
                [("created_at", ASCENDING)],
                expireAfterSeconds=7 * 24 * 60 * 60
            )
            
            logger.info("Database indexes created")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
    
    def check_connection(self) -> str:
        """בדיקת חיבור ל-DB"""
        try:
            if not self.client:
                return "not configured"
            self.client.admin.command('ping')
            return "connected"
        except Exception as e:
            return f"disconnected: {str(e)}"
    
    # ============================================
    # Analyses CRUD
    # ============================================
    
    def create_analysis(self, analysis_data: Dict) -> str:
        """
        יצירת ניתוח חדש
        
        Args:
            analysis_data: מידע על הניתוח
            
        Returns:
            analysis_id
        """
        try:
            result = self.analyses_collection.insert_one(analysis_data)
            logger.info(f"Created analysis: {analysis_data['analysis_id']}")
            return analysis_data['analysis_id']
            
        except Exception as e:
            logger.error(f"Error creating analysis: {str(e)}")
            raise
    
    def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """
        קבלת ניתוח לפי ID
        
        Args:
            analysis_id: מזהה הניתוח
            
        Returns:
            מידע על הניתוח או None
        """
        try:
            return self.analyses_collection.find_one({"analysis_id": analysis_id})
        except Exception as e:
            logger.error(f"Error getting analysis: {str(e)}")
            return None
    
    def update_analysis(self, analysis_id: str, updates: Dict) -> bool:
        """
        עדכון ניתוח
        
        Args:
            analysis_id: מזהה הניתוח
            updates: שדות לעדכון
            
        Returns:
            True אם הצליח
        """
        try:
            updates['updated_at'] = datetime.utcnow()
            
            result = self.analyses_collection.update_one(
                {"analysis_id": analysis_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating analysis: {str(e)}")
            return False
    
    def update_analysis_status(self, analysis_id: str, status: str, error: Optional[str] = None) -> bool:
        """
        עדכון סטטוס הניתוח
        
        Args:
            analysis_id: מזהה הניתוח
            status: הסטטוס החדש (pending/processing/complete/error)
            error: הודעת שגיאה (אם יש)
        """
        updates = {"status": status}
        if error:
            updates['error'] = error
        
        return self.update_analysis(analysis_id, updates)
    
    def update_analysis_progress(self, analysis_id: str, progress: int, message: str = "") -> bool:
        """
        עדכון התקדמות הניתוח
        
        Args:
            analysis_id: מזהה הניתוח
            progress: אחוזי התקדמות (0-100)
            message: הודעה על השלב הנוכחי
        """
        updates = {
            "progress": progress,
            "progress_message": message
        }
        
        return self.update_analysis(analysis_id, updates)
    
    def complete_analysis(self, analysis_id: str, results: Dict) -> bool:
        """
        סיום ניתוח והוספת תוצאות
        
        Args:
            analysis_id: מזהה הניתוח
            results: תוצאות הניתוח
        """
        updates = {
            "status": "complete",
            "progress": 100,
            "completed_at": datetime.utcnow(),
            **results
        }
        
        return self.update_analysis(analysis_id, updates)
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """
        מחיקת ניתוח
        
        Args:
            analysis_id: מזהה הניתוח
            
        Returns:
            True אם נמחק
        """
        try:
            # מחיקת הניתוח
            result = self.analyses_collection.delete_one({"analysis_id": analysis_id})
            
            # מחיקת cache קשור
            self.cache_collection.delete_many({"analysis_id": analysis_id})
            
            logger.info(f"Deleted analysis: {analysis_id}")
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting analysis: {str(e)}")
            return False
    
    def find_analysis_by_repo(self, repo_url: str) -> Optional[Dict]:
        """
        מציאת ניתוח קיים לפי URL של הrepo
        
        Args:
            repo_url: כתובת הrepo
            
        Returns:
            הניתוח האחרון או None
        """
        try:
            return self.analyses_collection.find_one(
                {"repo_url": repo_url},
                sort=[("created_at", DESCENDING)]
            )
        except Exception as e:
            logger.error(f"Error finding analysis by repo: {str(e)}")
            return None
    
    def list_analyses(self, 
                     limit: int = 20, 
                     offset: int = 0,
                     status: Optional[str] = None) -> List[Dict]:
        """
        רשימת ניתוחים
        
        Args:
            limit: מספר תוצאות
            offset: offset
            status: סינון לפי סטטוס (אופציונלי)
            
        Returns:
            רשימת ניתוחים
        """
        try:
            query = {}
            if status:
                query['status'] = status
            
            cursor = self.analyses_collection.find(query) \
                .sort("created_at", DESCENDING) \
                .skip(offset) \
                .limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Error listing analyses: {str(e)}")
            return []
    
    def count_analyses(self, status: Optional[str] = None) -> int:
        """
        ספירת ניתוחים
        
        Args:
            status: סינון לפי סטטוס (אופציונלי)
            
        Returns:
            מספר הניתוחים
        """
        try:
            query = {}
            if status:
                query['status'] = status
            
            return self.analyses_collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"Error counting analyses: {str(e)}")
            return 0
    
    # ============================================
    # Blast Radius Cache
    # ============================================
    
    def cache_blast_radius(self, 
                          analysis_id: str, 
                          file_path: str, 
                          blast_data: Dict) -> bool:
        """
        שמירת blast radius ב-cache
        
        Args:
            analysis_id: מזהה הניתוח
            file_path: נתיב הקובץ
            blast_data: נתוני ה-blast radius
            
        Returns:
            True אם נשמר
        """
        try:
            cache_entry = {
                "analysis_id": analysis_id,
                "file_path": file_path,
                "blast_data": blast_data,
                "created_at": datetime.utcnow()
            }
            
            # update or insert
            self.cache_collection.update_one(
                {"analysis_id": analysis_id, "file_path": file_path},
                {"$set": cache_entry},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching blast radius: {str(e)}")
            return False
    
    def get_cached_blast_radius(self, 
                                analysis_id: str, 
                                file_path: str) -> Optional[Dict]:
        """
        קבלת blast radius מה-cache
        
        Args:
            analysis_id: מזהה הניתוח
            file_path: נתיב הקובץ
            
        Returns:
            נתוני blast radius או None
        """
        try:
            cached = self.cache_collection.find_one({
                "analysis_id": analysis_id,
                "file_path": file_path
            })
            
            if cached:
                return cached['blast_data']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached blast radius: {str(e)}")
            return None
    
    def clear_cache(self, analysis_id: str) -> bool:
        """
        ניקוי cache לניתוח מסוים
        
        Args:
            analysis_id: מזהה הניתוח
            
        Returns:
            True אם נוקה
        """
        try:
            result = self.cache_collection.delete_many({"analysis_id": analysis_id})
            logger.info(f"Cleared {result.deleted_count} cache entries for {analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    # ============================================
    # Stats & Maintenance
    # ============================================
    
    def get_stats(self) -> Dict:
        """
        סטטיסטיקות על הDB
        
        Returns:
            מידע סטטיסטי
        """
        try:
            total_analyses = self.analyses_collection.count_documents({})
            complete = self.analyses_collection.count_documents({"status": "complete"})
            pending = self.analyses_collection.count_documents({"status": "pending"})
            processing = self.analyses_collection.count_documents({"status": "processing"})
            error = self.analyses_collection.count_documents({"status": "error"})
            
            cache_size = self.cache_collection.count_documents({})
            
            return {
                "total_analyses": total_analyses,
                "complete": complete,
                "pending": pending,
                "processing": processing,
                "error": error,
                "cache_entries": cache_size
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}
    
    def cleanup_old_analyses(self, days: int = 30) -> int:
        """
        מחיקת ניתוחים ישנים
        
        Args:
            days: מספר ימים (ניתוחים ישנים מזה יימחקו)
            
        Returns:
            מספר ניתוחים שנמחקו
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = self.analyses_collection.delete_many({
                "created_at": {"$lt": cutoff_date},
                "status": {"$in": ["complete", "error"]}
            })
            
            deleted = result.deleted_count
            logger.info(f"Cleaned up {deleted} old analyses")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up old analyses: {str(e)}")
            return 0
    
    def close(self):
        """סגירת החיבור"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Global instance
db = Database()
