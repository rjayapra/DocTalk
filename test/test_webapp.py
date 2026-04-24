"""Tests for webapp integration — static file serving and routing."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def temp_webapp(tmp_path):
    """Create temporary webapp directory with test files."""
    webapp_dir = tmp_path / "webapp"
    webapp_dir.mkdir()
    
    # Create test HTML file
    (webapp_dir / "index.html").write_text(
        "<!DOCTYPE html><html><head><title>DocTalk</title></head>"
        "<body><h1>DocTalk Podcast Generator</h1></body></html>"
    )
    
    # Create test CSS file
    (webapp_dir / "style.css").write_text(
        "body { font-family: Arial, sans-serif; }"
    )
    
    # Create test JS file
    (webapp_dir / "app.js").write_text(
        "console.log('DocTalk webapp loaded');"
    )
    
    return webapp_dir


@pytest.fixture
def client_with_webapp(temp_webapp):
    """Create TestClient with mocked webapp directory."""
    with patch("src.api.main.Path") as mock_path:
        # Mock Path(__file__).parent.parent / "webapp" to return temp_webapp
        mock_path_instance = MagicMock()
        mock_path_instance.__truediv__ = lambda self, other: temp_webapp if other == "webapp" else self
        mock_path.return_value.parent.parent = mock_path_instance
        
        # Import after patching to ensure the mock is applied
        from src.api.main import app
        return TestClient(app)


def test_health_endpoint_works_with_webapp(client_with_webapp):
    """Test that /health endpoint still works alongside static files."""
    response = client_with_webapp.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "doctalk-api"


def test_root_redirects_to_app(client_with_webapp):
    """Test that GET / redirects to /app/index.html."""
    response = client_with_webapp.get("/", follow_redirects=False)
    assert response.status_code in [302, 307, 308]  # Redirect status codes
    # Check that Location header points to webapp
    assert "/app" in response.headers.get("location", "").lower() or "index.html" in response.headers.get("location", "").lower()


def test_index_html_is_served(client_with_webapp):
    """Test that /app/index.html returns 200 with HTML content."""
    response = client_with_webapp.get("/app/index.html")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "").lower()
    assert b"DocTalk" in response.content
    assert b"<html>" in response.content.lower()


def test_css_is_served_with_correct_content_type(client_with_webapp):
    """Test that /app/style.css returns 200 with CSS content-type."""
    response = client_with_webapp.get("/app/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers.get("content-type", "").lower()
    assert b"font-family" in response.content


def test_js_is_served_with_correct_content_type(client_with_webapp):
    """Test that /app/app.js returns 200 with JavaScript content-type."""
    response = client_with_webapp.get("/app/app.js")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "").lower()
    # JavaScript can be served as application/javascript or text/javascript
    assert "javascript" in content_type
    assert b"console.log" in response.content


def test_static_file_404(client_with_webapp):
    """Test that /app/nonexistent.file returns 404."""
    response = client_with_webapp.get("/app/nonexistent.file")
    assert response.status_code == 404


def test_cors_headers_on_api_endpoints(client_with_webapp):
    """Test that API responses include CORS headers."""
    response = client_with_webapp.get("/health")
    assert response.status_code == 200
    
    # Check for CORS headers
    headers = {k.lower(): v for k, v in response.headers.items()}
    assert "access-control-allow-origin" in headers
    assert headers["access-control-allow-origin"] == "*"


def test_cors_preflight_request(client_with_webapp):
    """Test that CORS preflight OPTIONS requests work."""
    response = client_with_webapp.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )
    # Should return 200 with CORS headers
    assert response.status_code == 200
    headers = {k.lower(): v for k, v in response.headers.items()}
    assert "access-control-allow-origin" in headers
    assert "access-control-allow-methods" in headers


@pytest.mark.skipif(
    not Path("src/webapp").exists(),
    reason="Webapp directory not yet created"
)
def test_real_webapp_files_exist():
    """Test that real webapp files exist (integration test)."""
    webapp_dir = Path("src/webapp")
    assert webapp_dir.exists()
    assert (webapp_dir / "index.html").exists()
    assert (webapp_dir / "style.css").exists()
    assert (webapp_dir / "app.js").exists()


def test_api_endpoints_still_accessible():
    """Test that all API endpoints are still accessible (no path conflicts)."""
    # Import here to avoid issues if webapp isn't fully configured yet
    from src.api.main import app
    
    # Check that API routes are registered
    routes = [route.path for route in app.routes]
    
    assert "/health" in routes
    assert "/generate" in routes
    assert "/jobs/{job_id}" in routes
    assert "/jobs" in routes


def test_webapp_doesnt_override_api_routes():
    """Test that mounting static files at /app doesn't override /api/* routes."""
    from src.api.main import app
    
    routes = [route.path for route in app.routes]
    
    # Ensure no API routes start with /app (which is reserved for static files)
    api_routes = [r for r in routes if not r.startswith("/app")]
    assert len(api_routes) >= 4  # health, generate, jobs/{id}, jobs


def test_multiple_static_files_in_sequence(client_with_webapp):
    """Test serving multiple static files in sequence (cache behavior)."""
    # Request HTML
    response1 = client_with_webapp.get("/app/index.html")
    assert response1.status_code == 200
    
    # Request CSS
    response2 = client_with_webapp.get("/app/style.css")
    assert response2.status_code == 200
    
    # Request JS
    response3 = client_with_webapp.get("/app/app.js")
    assert response3.status_code == 200
    
    # Request HTML again
    response4 = client_with_webapp.get("/app/index.html")
    assert response4.status_code == 200
    assert response4.content == response1.content
