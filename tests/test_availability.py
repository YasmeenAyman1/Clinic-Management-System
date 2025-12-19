def test_schedule_requires_doctor_role(client):
    # Not logged in should redirect
    res = client.get('/doctor/schedule')
    assert res.status_code == 302


def test_add_availability_csrf(client, monkeypatch):
    # Fake repo to avoid DB
    class FakeRepo:
        def create_availability(self, doctor_id, date, start_time, end_time):
            class R:
                id = 1
            return R()
        def list_by_doctor(self, doctor_id):
            return []
        def delete_availability(self, av_id):
            return True
        def get_by_user_id(self, user_id):
            class D:
                id = user_id
                firstName = 'Test'
                lastName = 'Doctor'
            return D()

    # Replace controller repos directly to avoid real DB access
    # Patch module-level variables by module path to ensure flask route uses the fakes
    monkeypatch.setattr('src.controllers.doctor_controller.doctor_repo', FakeRepo(), raising=False)
    monkeypatch.setattr('src.controllers.doctor_controller.availability_repo', FakeRepo(), raising=False)
    # also patch the non-src module path in case flask imported via top-level package
    monkeypatch.setattr('controllers.doctor_controller.doctor_repo', FakeRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.availability_repo', FakeRepo(), raising=False)

    # create session with doctor role and csrf
    with client.session_transaction() as sess:
        sess['role'] = 'doctor'
        sess['user_id'] = 1
        sess['status'] = 'active'
        sess['csrf_token'] = 'tok'

    # POST with invalid CSRF should flash error and redirect
    res = client.post('/doctor/availability/add', data={'date':'2025-12-18','start_time':'09:00','end_time':'10:00','csrf_token':'bad'}, follow_redirects=True)
    assert b'Invalid CSRF token' in res.data

    # POST with valid CSRF should succeed
    res2 = client.post('/doctor/availability/add', data={'date':'2025-12-18','start_time':'09:00','end_time':'10:00','csrf_token':'tok'}, follow_redirects=True)
    assert b'Availability added' in res2.data
