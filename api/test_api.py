"""
Basic API Tests

להרצה:
    pytest api/test_api.py -v
"""

import pytest


@pytest.fixture()
def client():
    """Flask test client (no external server required)."""
    from api.app import app
    return app.test_client()


def test_health_check(client):
    """בדיקת health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_health_check(client):
    """בדיקת API health"""
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["status"] == "healthy"


def test_start_analysis_invalid_url(client):
    """בדיקת התחלת ניתוח עם URL לא תקין"""
    response = client.post("/api/analyze", json={"repo_url": "not-a-valid-url"})
    
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_get_nonexistent_analysis(client, monkeypatch):
    """בדיקת קבלת ניתוח שלא קיים"""
    # Avoid needing a real MongoDB for this unit test.
    import api.app as app_module
    monkeypatch.setattr(app_module.db, "get_analysis", lambda _analysis_id: None)

    response = client.get("/api/analysis/nonexistent123")
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
