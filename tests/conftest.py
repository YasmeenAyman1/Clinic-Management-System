import pytest
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# If you're using Option 1 (separate create_app.py)
try:
    from create_app import create_app
except ImportError:
    # If using Option 3 (factory in app.py)
    from app import create_app

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app(config_name='testing')
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create CLI runner"""
    return app.test_cli_runner()