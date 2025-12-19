def test_doctor_approval_creates_audit(client, monkeypatch):
    # Fake repos
    approval_called = {'ok': False}
    audit_called = {}

    class FakeAppointmentRepo:
        def approve_appointment(self, appointment_id, doctor_id):
            approval_called['ok'] = True
            approval_called['args'] = (appointment_id, doctor_id)
            return True

    class FakeDoctorRepo:
        def get_by_user_id(self, uid):
            class D: pass
            d = D(); d.id = 100
            return d

    class FakeAuditRepo:
        def create_entry(self, admin_user_id, action, target_user_id=None, target_type=None, details=None):
            audit_called['last'] = dict(admin_user_id=admin_user_id, action=action, target_user_id=target_user_id, target_type=target_type, details=details)

    monkeypatch.setattr('src.controllers.doctor_controller.appointment_repo', FakeAppointmentRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.appointment_repo', FakeAppointmentRepo(), raising=False)
    monkeypatch.setattr('src.controllers.doctor_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('src.controllers.doctor_controller.audit_repo', FakeAuditRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.audit_repo', FakeAuditRepo(), raising=False)

    # Setup session as doctor
    with client.session_transaction() as sess:
        sess['role'] = 'doctor'; sess['status'] = 'active'; sess['user_id'] = 42; sess['csrf_token'] = 'tok'

    res = client.post('/doctor/appointment/555/approve', data={'csrf_token': 'tok'}, follow_redirects=False)
    assert approval_called['ok'] is True
    assert audit_called.get('last') and audit_called['last']['action'] == 'approve_appointment' and audit_called['last']['target_user_id'] == 555


def test_assistant_can_approve_for_assigned_doctor(client, monkeypatch):
    approval_called = {'ok': False}
    audit_called = {}

    class FakeAppointmentRepo:
        def approve_appointment(self, appointment_id, doctor_id):
            approval_called['ok'] = True
            approval_called['args'] = (appointment_id, doctor_id)
            return True

    class FakeAssistantRepo:
        def get_by_user_id(self, uid):
            class A: pass
            a = A(); a.id = 10; a.doctor_id = 100
            return a

    class FakeDoctorRepo:
        def get_by_id(self, did):
            class D: pass
            d = D(); d.id = did; return d

    class FakeAuditRepo:
        def create_entry(self, admin_user_id, action, target_user_id=None, target_type=None, details=None):
            audit_called['last'] = dict(admin_user_id=admin_user_id, action=action, target_user_id=target_user_id)

    monkeypatch.setattr('src.controllers.doctor_controller.appointment_repo', FakeAppointmentRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.appointment_repo', FakeAppointmentRepo(), raising=False)
    monkeypatch.setattr('src.controllers.doctor_controller.assistant_repo', FakeAssistantRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.assistant_repo', FakeAssistantRepo(), raising=False)
    # Also ensure RepositoryFactory will return our fake for 'assistant' within the controller
    monkeypatch.setattr('src.controllers.doctor_controller.RepositoryFactory.get_repository', lambda k: FakeAssistantRepo() if k=='assistant' else FakeDoctorRepo() if k=='doctor' else FakeAppointmentRepo() if k=='appointment' else FakeAuditRepo() if k=='admin_audit' else None, raising=False)

    monkeypatch.setattr('controllers.doctor_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('src.controllers.doctor_controller.audit_repo', FakeAuditRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.audit_repo', FakeAuditRepo(), raising=False)

    with client.session_transaction() as sess:
        sess['role'] = 'assistant'; sess['status'] = 'active'; sess['user_id'] = 7; sess['csrf_token'] = 'tok'

    res = client.post('/doctor/appointment/777/approve', data={'csrf_token': 'tok'}, follow_redirects=False)
    assert approval_called['ok'] is True
    assert audit_called.get('last') and audit_called['last']['action'] == 'approve_appointment'