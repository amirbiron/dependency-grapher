"""
Basic API Tests

להרצה:
    pytest api/test_api.py -v
"""

import pytest
import json
from pathlib import Path

# נניח שהשרת רץ בlocalhost:5000
BASE_URL = "http://localhost:5000"


def test_health_check():
    """בדיקת health endpoint"""
    import requests
    
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_health_check():
    """בדיקת API health"""
    import requests
    
    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"


def test_start_analysis_invalid_url():
    """בדיקת התחלת ניתוח עם URL לא תקין"""
    import requests
    
    response = requests.post(f"{BASE_URL}/api/analyze", json={
        "repo_url": "not-a-valid-url"
    })
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_get_nonexistent_analysis():
    """בדיקת קבלת ניתוח שלא קיים"""
    import requests
    
    response = requests.get(f"{BASE_URL}/api/analysis/nonexistent123")
    assert response.status_code == 404


def test_validate_repo_url():
    """בדיקת validation של URLs"""
    from api.utils import validate_repo_url
    
    # תקינים
    assert validate_repo_url("https://github.com/user/repo") == True
    assert validate_repo_url("https://github.com/user/repo.git") == True
    assert validate_repo_url("https://gitlab.com/user/repo") == True
    
    # לא תקינים
    assert validate_repo_url("") == False
    assert validate_repo_url("not-a-url") == False
    assert validate_repo_url("ftp://example.com") == False


def test_generate_analysis_id():
    """בדיקת יצירת analysis ID"""
    from api.utils import generate_analysis_id
    
    id1 = generate_analysis_id()
    id2 = generate_analysis_id()
    
    assert len(id1) == 16  # 8 bytes = 16 hex chars
    assert id1 != id2  # ייחודי
    assert id1.isalnum()  # רק אותיות ומספרים


if __name__ == "__main__":
    # בדיקה מהירה
    print("Running basic tests...")
    
    test_validate_repo_url()
    print("✓ validate_repo_url")
    
    test_generate_analysis_id()
    print("✓ generate_analysis_id")
    
    print("\nAll tests passed!")
