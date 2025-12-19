def test_doctor_signup_creates_pending(client, monkeypatch):
    called = {}

    class FakeUserRepo:
        def create_user(self, username, password, role, status='active'):
            called['user'] = dict(username=username, role=role, status=status)
            class U:
                def __init__(self):
                    self.id = 123
            return U()
        def get_by_username(self, username):
            return None

    class FakeDoctorRepo:
        def create_doctor(self, first_name, last_name, phone, user_id, specialization=''):
            called['doctor'] = dict(first_name=first_name, last_name=last_name, phone=phone, user_id=user_id, specialization=specialization)
            class D:
                id = 1
            return D()

    # Patch both import paths the controllers might have
    monkeypatch.setattr('src.controllers.authO_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('controllers.authO_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('src.controllers.authO_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('controllers.authO_controller.doctor_repo', FakeDoctorRepo(), raising=False)

    res = client.post('/auth/signup', data={
        'full_name': 'John Doe',
        'email': 'jdoe@example.com',
        'phone': '1234567890',
        'password': 'secret123',
        'confirm_password': 'secret123',
        'role': 'doctor',
        'specialization': 'Cardiology'
    }, follow_redirects=True)

    assert b'sent for approval' in res.data or b'Account created and sent for approval' in res.data
    assert called['user']['status'] == 'pending'
    assert called['user']['role'] == 'doctor'


def test_assistant_signup_creates_pending(client, monkeypatch):
    called = {}

    class FakeUserRepo:
        def create_user(self, username, password, role, status='active'):
            called['user'] = dict(username=username, role=role, status=status)
            class U:
                def __init__(self):
                    self.id = 124
            return U()
        def get_by_username(self, username):
            return None

    class FakeAssistantRepo:
        def create_assistant(self, first_name, last_name, phone, user_id):
            called['assistant'] = dict(first_name=first_name, last_name=last_name, phone=phone, user_id=user_id)
            class A:
                id = 2
            return A()

    monkeypatch.setattr('src.controllers.authO_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('controllers.authO_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('src.controllers.authO_controller.assistant_repo', FakeAssistantRepo(), raising=False)
    monkeypatch.setattr('controllers.authO_controller.assistant_repo', FakeAssistantRepo(), raising=False)

    res = client.post('/auth/signup', data={
        'full_name': 'Sam Assist',
        'email': 'sassist@example.com',
        'phone': '0987654321',
        'password': 'secret123',
        'confirm_password': 'secret123',
        'role': 'assistant'
    }, follow_redirects=True)

    assert b'sent for approval' in res.data or b'An admin will assign you to a doctor' in res.data
    assert called['user']['status'] == 'pending'
    assert called['user']['role'] == 'assistant'


def test_admin_approves_user_and_assigns_doctor(client, monkeypatch):
    # Simulate pending assistant user and capture SQL executed
    class FakeUser:
        id = 500
        status = 'pending'
        role = 'assistant'

    class FakeCursor:
        def __init__(self):
            self.executed = []
        def execute(self, q, params=None):
            self.executed.append((q, params))
        def close(self):
            pass

    class FakeDB:
        def __init__(self, cursor):
            self._cursor = cursor
        def cursor(self):
            return self._cursor
        def commit(self):
            # no-op for tests
            pass

    # Fake repos
    class FakeUserRepo:
        def get_by_id(self, uid):
            return FakeUser()
        db = None
    class FakeAssistantRepo:
        db = None

    fake_cursor = FakeCursor()
    fake_db = FakeDB(fake_cursor)
    fuser = FakeUserRepo()
    fuser.db = fake_db
    fassist = FakeAssistantRepo()
    fassist.db = fake_db

    monkeypatch.setattr('src.controllers.admin_controller.user_repo', fuser, raising=False)
    monkeypatch.setattr('controllers.admin_controller.user_repo', fuser, raising=False)
    monkeypatch.setattr('src.controllers.admin_controller.assistant_repo', fassist, raising=False)
    monkeypatch.setattr('controllers.admin_controller.assistant_repo', fassist, raising=False)

    # login as admin
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['status'] = 'active'
        sess['csrf_token'] = 'admintok'

    res = client.post('/admin/pending/500/approve', data={'csrf_token': 'admintok', 'assign_doctor': 2}, follow_redirects=True)

    assert b'activated' in res.data or b'User approved' in res.data
    # verify SQL to update status was called
    assert any("UPDATE user SET status = 'active'" in q for q, _ in fake_cursor.executed)
    # verify assistant assignment query executed
    assert any('UPDATE assistant SET doctor_id' in q for q, _ in fake_cursor.executed)
