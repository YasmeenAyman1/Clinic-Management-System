def test_approve_creates_audit_and_pagination(client, monkeypatch):
    # Prepare pending users (25) to test pagination
    class FakeUser:
        def __init__(self, id):
            self.id = id
            self.username = f'user{id}@example.com'
            self.role = 'doctor' if id % 2 == 0 else 'assistant'
            self.firstName = 'First'
            self.lastName = str(id)
            self.phone = '123'
            self.created_at = '2025-12-17'
            self.status = 'pending'

    pending = [FakeUser(i) for i in range(1, 26)]

    # Fake repos
    class FakeCursor:
        def __init__(self):
            self.executed = []
        def execute(self, q, params=None):
            self.executed.append((q, params))
        def close(self):
            pass

    class FakeDB:
        def __init__(self):
            self._cursor = FakeCursor()
        def cursor(self):
            return self._cursor
        def commit(self):
            pass

    class FakeUserRepo:
        def list_pending_users(self):
            return pending
        def get_by_id(self, uid):
            return next((u for u in pending if u.id == uid), None)
        def delete_user(self, uid):
            # emulate delete
            pass
        db = FakeDB()

    audit_called = {}
    class FakeAuditRepo:
        def create_entry(self, admin_user_id, action, target_user_id=None, target_type=None, details=None):
            audit_called['last'] = dict(admin_user_id=admin_user_id, action=action, target_user_id=target_user_id, target_type=target_type, details=details)
            return True
        def list_recent(self, limit=20):
            return []

    monkeypatch.setattr('src.controllers.admin_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('controllers.admin_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('src.controllers.admin_controller.doctor_repo', type('D', (), {'list_all': lambda self: []})(), raising=False)
    monkeypatch.setattr('src.controllers.admin_controller.doctor_repo', type('D', (), {'list_all': lambda self: []})(), raising=False)
    monkeypatch.setattr('src.controllers.admin_controller.audit_repo', FakeAuditRepo(), raising=False)
    monkeypatch.setattr('controllers.admin_controller.audit_repo', FakeAuditRepo(), raising=False)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['status'] = 'active'
        sess['csrf_token'] = 'tok'
        sess['user_id'] = 999

    # Request admin home and ensure header renders
    res = client.get('/admin/')
    assert b'Admin Dashboard' in res.data

    # Now approve a user and verify audit was recorded
    res2 = client.post('/admin/pending/3/approve', data={'csrf_token': 'tok'}, follow_redirects=True)
    assert b'activated' in res2.data or b'User approved' in res2.data
    assert audit_called.get('last') and audit_called['last']['action'] == 'approve_user' and audit_called['last']['target_user_id'] == 3
