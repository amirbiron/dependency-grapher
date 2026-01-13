"""
Utility Functions for API
"""

import os
import re
import shutil
import secrets
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


def validate_repo_url(url: str) -> bool:
    """
    אימות URL של repository
    
    Args:
        url: כתובת הrepo
        
    Returns:
        True אם תקין
    """
    if not url:
        return False
    
    # בדיקה בסיסית של URL
    try:
        parsed = urlparse(url)
        
        # חייב להיות scheme (http/https בלבד)
        if parsed.scheme not in ("http", "https"):
            return False
        
        # חייב להיות netloc (github.com וכו')
        if not parsed.netloc:
            return False
        
        # רשימת מארחים מותרים
        allowed_hosts = [
            'github.com',
            'gitlab.com',
            'bitbucket.org',
            'git.example.com'  # להוסיף לפי הצורך
        ]
        
        # בדיקה אם המארח מותר (אופציונלי - אפשר להסיר)
        # if parsed.netloc not in allowed_hosts:
        #     return False
        
        # בדיקת תבנית GitHub
        if 'github.com' in parsed.netloc:
            # https://github.com/user/repo או https://github.com/user/repo.git
            pattern = r'^/[\w-]+/[\w.-]+(\.git)?/?$'
            if not re.match(pattern, parsed.path):
                return False
        
        return True
        
    except Exception:
        return False


def generate_analysis_id() -> str:
    """
    יצירת analysis_id ייחודי
    
    Returns:
        מזהה ייחודי (16 תווים hex)
    """
    return secrets.token_hex(8)


def cleanup_temp_dir(temp_dir: Path) -> bool:
    """
    מחיקת תיקייה זמנית
    
    Args:
        temp_dir: נתיב לתיקייה
        
    Returns:
        True אם נמחק בהצלחה
    """
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return True
    except Exception as e:
        print(f"Error cleaning up temp dir: {str(e)}")
        return False


def extract_repo_name(repo_url: str) -> str:
    """
    חילוץ שם הrepo מהURL
    
    Args:
        repo_url: כתובת הrepo
        
    Returns:
        שם הrepo
        
    Example:
        https://github.com/user/my-repo.git -> my-repo
    """
    try:
        parsed = urlparse(repo_url)
        path = parsed.path.rstrip('/')
        
        # הסרת .git
        if path.endswith('.git'):
            path = path[:-4]
        
        # לקיחת החלק האחרון
        repo_name = path.split('/')[-1]
        
        return repo_name
        
    except Exception:
        return "unknown"


def format_file_size(size_bytes: int) -> str:
    """
    המרת bytes לפורמט קריא
    
    Args:
        size_bytes: גודל בbytes
        
    Returns:
        מחרוזת בפורמט KB/MB/GB
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """
    ניקוי שם קובץ מתווים לא חוקיים
    
    Args:
        filename: שם הקובץ
        
    Returns:
        שם קובץ מנוקה
    """
    # החלפת תווים לא חוקיים ב-underscore
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # הגבלת אורך
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized


def calculate_percentage(current: int, total: int) -> int:
    """
    חישוב אחוזים
    
    Args:
        current: ערך נוכחי
        total: סה"כ
        
    Returns:
        אחוזים (0-100)
    """
    if total == 0:
        return 0
    
    percentage = int((current / total) * 100)
    return min(max(percentage, 0), 100)


def is_valid_branch_name(branch: str) -> bool:
    """
    בדיקה אם שם ענף תקין
    
    Args:
        branch: שם הענף
        
    Returns:
        True אם תקין
    """
    if not branch:
        return False
    
    # תבנית בסיסית לשם ענף
    pattern = r'^[\w\-/\.]+$'
    return bool(re.match(pattern, branch))
