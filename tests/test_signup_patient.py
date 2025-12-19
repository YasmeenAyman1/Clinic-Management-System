def test_patient_signup_creates_profile_without_birthdate(client, monkeypatch):
    called = {}

    class FakeUserRepo:
        def create_user(self, username, password, role, status='active'):
            called['user'] = dict(username=username, role=role, status=status)
            class U:
                def __init__(self):
                    self.id = 321
            return U()
        def get_by_username(self, username):
            return None

    class FakePatientRepo:
        def create_patient(self, first_name, last_name, phone, user_id, gender='other', birth_date=None, address=None):
            called['patient'] = dict(first_name=first_name, last_name=last_name, phone=phone, user_id=user_id, birth_date=birth_date, address=address)
            class P:
                id = 3
            return P()

    monkeypatch.setattr('src.controllers.authO_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('controllers.authO_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('src.controllers.authO_controller.patient_repo', FakePatientRepo(), raising=False)
    monkeypatch.setattr('controllers.authO_controller.patient_repo', FakePatientRepo(), raising=False)

    res = client.post('/auth/signup', data={
        'full_name': 'Patient Zero',
        'email': 'patient@example.com',
        'phone': '0111111111',
        'password': 'secret123',
        'confirm_password': 'secret123',
        'role': 'patient'
    }, follow_redirects=True)

    assert b'Account created successfully' in res.data or b'Please log in' in res.data
    assert called['user']['role'] == 'patient'
    assert 'patient' in called and called['patient']['birth_date'] is None
