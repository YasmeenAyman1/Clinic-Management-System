def test_admin_ui_shows_pending_and_search(client, monkeypatch):
    class FakeUser:
        def __init__(self, id, username, role, firstName='', lastName='', phone='', created_at='2025-12-17'):
            self.id = id
            self.username = username
            self.role = role
            self.firstName = firstName
            self.lastName = lastName
            self.phone = phone
            self.created_at = created_at

    pending = [FakeUser(1, 'doc1@example.com', 'doctor', 'Doc', 'One', '1234'), FakeUser(2, 'assist@example.com', 'assistant', 'Assist', 'Two', '5678')]
    fake_doctors = []

    class FakeUserRepo:
        def list_pending_users(self):
            return pending
    class FakeDoctorRepo:
        def list_all(self):
            return fake_doctors

    monkeypatch.setattr('src.controllers.admin_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('controllers.admin_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('src.controllers.admin_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('controllers.admin_controller.doctor_repo', FakeDoctorRepo(), raising=False)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['status'] = 'active'

    res = client.get('/admin/')
    # admin header and pending items
    assert b'Admin Dashboard' in res.data
    assert b'doc1@example.com' in res.data
    assert b'assist@example.com' in res.data
    assert b'Assign doctor' in res.data or b'Assign doctor' in res.data
