def test_doctor_slots_api_returns_slots(client, monkeypatch):
    # fake slots
    def fake_get_slots(doctor_id, date):
        return ['09:00', '09:30']

    class FakeRepo:
        def get_available_slots(self, doctor_id, date):
            return ['09:00', '09:30']
    # patch both import paths
    monkeypatch.setattr('src.controllers.patient_controller.appointment_repo', FakeRepo(), raising=False)
    monkeypatch.setattr('controllers.patient_controller.appointment_repo', FakeRepo(), raising=False)

    with client.session_transaction() as sess:
        sess['role'] = 'patient'
        sess['user_id'] = 1
        sess['status'] = 'active'

    res = client.get('/patient/api/doctor/2/slots?date=2025-12-20')
    assert res.status_code == 200
    data = res.get_json()
    assert 'slots' in data
    assert '09:00' in data['slots']

def test_booking_rejects_unavailable_slot(client, monkeypatch):
    # Simulate no available slots and prevent create_appointment from being called
    class FakeApptRepo:
        def get_available_slots(self, d, date):
            return []
        def create_appointment(self, *args, **kwargs):
            raise AssertionError('create_appointment should not be called when slot unavailable')
        def get_by_patient_id(self, patient_id):
            return []
        def get_by_doctor_id(self, doctor_id, date=None):
            return []

    fake_appt = FakeApptRepo()
    monkeypatch.setattr('src.controllers.patient_controller.appointment_repo', fake_appt, raising=False)
    monkeypatch.setattr('controllers.patient_controller.appointment_repo', fake_appt, raising=False)

    # setup patient (avoid real DB patient repo)
    class FakePatientRepo:
        def get_by_user_id(self, uid):
            class P:
                id = 10
            return P()
    monkeypatch.setattr('src.controllers.patient_controller.patient_repo', FakePatientRepo(), raising=False)
    monkeypatch.setattr('controllers.patient_controller.patient_repo', FakePatientRepo(), raising=False)

    # avoid real doctor repo DB access
    class FakeDoctorRepo:
        def list_all(self):
            class D:
                id = 2
                firstName = 'Alice'
                lastName = 'Smith'
                specialization = 'General'
            return [D()]
    monkeypatch.setattr('src.controllers.patient_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('controllers.patient_controller.doctor_repo', FakeDoctorRepo(), raising=False)

    with client.session_transaction() as sess:
        sess['role'] = 'patient'
        sess['user_id'] = 99
        sess['status'] = 'active'

    res = client.post('/patient/appointments', data={'book_appointment': '1', 'doctor_id': 2, 'date': '2025-12-20', 'appointment_time': '09:00'}, follow_redirects=True)
    assert b'Selected time slot is no longer available' in res.data
