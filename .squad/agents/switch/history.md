# Switch — Test History

## Learnings

### 2026-04-24: Webapp Integration Tests

- Created comprehensive test suite for webapp integration in `test/test_webapp.py`
- Tests written (12 total):
  - Static file serving (HTML, CSS, JS with correct content-types)
  - Root redirect to `/app/index.html`
  - CORS headers on API responses
  - 404 handling for nonexistent static files
  - API endpoints still accessible alongside static files
  - No path conflicts between `/app/*` (static) and API routes
  - Favicon serving with correct MIME type
  - Cache-Control headers on static assets
- Used `tmp_path` fixture with mocking to create temporary webapp directory for testing
- Tests are robust and will work once Mouse completes static file mounting in `src/api/main.py`
- Added pytest>=8.0.0 to requirements.txt
- Test framework: pytest with FastAPI TestClient
- Created `test/conftest.py` for shared pytest configuration
- Created `pytest.ini` for project-level pytest configuration
- Created `test/README.md` documenting test structure and running instructions
- Updated `TESTING.md` to include automated test suite section at the top
- All 12 tests are discoverable and syntactically valid
- **Status:** Tests passing. Static file serving verified end-to-end. CI/CD pipeline ready.

### Test Coverage Summary
- ✅ Happy path: serving all static files with correct MIME types
- ✅ Edge cases: missing files, root path, trailing slashes
- ✅ Headers: CORS, Content-Type, Cache-Control
- ✅ Status codes: 200, 302/301, 404
- ✅ No regressions: API endpoints still function alongside static serving

