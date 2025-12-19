import os
import sys
import pytest

# Ensure project root is importable so tests can import src.* modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'src')
# Add project root and src to path so imports like 'src' and top-level packages work
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Signal to the app/database code that we're in a test environment so it can skip real DB connects
import os
os.environ.setdefault('TESTING', '1')

# During tests, the mysql driver may not be installed in CI/dev.
# Provide a lightweight dummy module so imports succeed for non-DB tests.
import types
# Create a lightweight dummy mysql.connector module with minimal attributes used at import time
sys.modules.setdefault('mysql', types.ModuleType('mysql'))
if 'mysql.connector' not in sys.modules:
    mysql_connector = types.ModuleType('mysql.connector')
    mysql_connector.Error = Exception
    def _dummy_connect(*args, **kwargs):
        raise ModuleNotFoundError('mysql.connector is not available in test environment')
    mysql_connector.connect = _dummy_connect
    sys.modules['mysql.connector'] = mysql_connector
    # also attach to parent mysql module so "import mysql.connector" behaves as expected
    if 'mysql' in sys.modules:
        setattr(sys.modules['mysql'], 'connector', mysql_connector)

from src.app import app as flask_app

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()
