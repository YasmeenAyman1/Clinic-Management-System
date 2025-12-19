from src.app import app


def test_admin_route_requires_login(client):
    # client fixture from pytest-flask expected; fallback to manual client
    with app.test_client() as c:
        res = c.get('/admin/')
        # not logged in, should redirect to login
        assert res.status_code == 302
        assert '/auth/login' in res.headers['Location']


def test_admin_csrf_and_access():
    with app.test_client() as c:
        # simulate logged-in admin in session
        with c.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['status'] = 'active'
            sess['username'] = 'admin@example.com'
            sess['csrf_token'] = 'valid-token'

        # GET should be allowed
        res_get = c.get('/admin/')
        assert res_get.status_code == 200

        # POST with invalid CSRF should be rejected and flash message visible
        res_post = c.post('/admin/pending/1/approve', data={'csrf_token': 'invalid'}, follow_redirects=True)
        assert res_post.status_code == 200
        assert b'Invalid CSRF token' in res_post.data
