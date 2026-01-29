import pytest
from create_app import create_app
from models.user_model import User
import json


@pytest.fixture
def client():
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_home_route(client):
    """Test home page redirects to login when not authenticated"""
    response = client.get('/')
    assert response.status_code == 302  # Redirect to login
    assert '/auth/login' in response.location

def test_login_page(client):
    """Test login page loads"""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_doctor_routes_require_auth(client):
    """Test doctor routes require authentication"""
    routes = ['/doctor', '/doctor/schedule', '/doctor/patients']
    
    for route in routes:
        response = client.get(route)
        assert response.status_code == 302  # Should redirect to login
        assert '/auth/login' in response.location

def test_patient_routes_require_auth(client):
    """Test patient routes require authentication"""
    routes = ['/patient', '/patient/appointments']
    
    for route in routes:
        response = client.get(route)
        assert response.status_code == 302
        assert '/auth/login' in response.location

def test_404_page(client):
    """Test 404 error page"""
    response = client.get('/non-existent-route')
    assert response.status_code == 404
    assert b'Page Not Found' in response.data or b'404' in response.data