def test_patient_booking_creates_pending(client, monkeypatch):
    called = {}

    class FakeAppointmentRepo:
        def get_available_slots(self, doctor_id, date):
            # Simulate that 10:00 is available for booking
            return ['10:00']
        def create_appointment(self, patient_id, doctor_id, date, appointment_time, assistant_id=None, status='PENDING'):
            called['args'] = dict(patient_id=patient_id, doctor_id=doctor_id, date=date, appointment_time=appointment_time, status=status)
            class A:
                def __init__(self, st):
                    self.id = 1
                    self.status = st
            return A(status)
        def get_by_doctor_id(self, doctor_id, date=None):
            return []
        def get_by_patient_id(self, patient_id):
            return []

    # Patch controllers' repo (both import paths)
    monkeypatch.setattr('src.controllers.patient_controller.appointment_repo', FakeAppointmentRepo(), raising=False)
    monkeypatch.setattr('controllers.patient_controller.appointment_repo', FakeAppointmentRepo(), raising=False)

    # Patch patient repo to return a patient id
    class FakePatientRepo:
        def get_by_user_id(self, user_id):
            class P:
                id = 10
            return P()
    monkeypatch.setattr('src.controllers.patient_controller.patient_repo', FakePatientRepo(), raising=False)
    monkeypatch.setattr('controllers.patient_controller.patient_repo', FakePatientRepo(), raising=False)

    # Fake doctor repo (doctors list for booking page)
    class FakeDoctorRepo:
        def list_all(self):
            class D:
                id = 2
                firstName = 'Alice'
                lastName = 'Smith'
            return [D()]
    monkeypatch.setattr('src.controllers.patient_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('controllers.patient_controller.doctor_repo', FakeDoctorRepo(), raising=False)

    # login as patient
    with client.session_transaction() as sess:
        sess['role'] = 'patient'
        sess['user_id'] = 99
        sess['status'] = 'active'

    res = client.post('/patient/appointments', data={'book_appointment': '1', 'doctor_id': 2, 'date': '2025-12-20', 'appointment_time': '10:00'}, follow_redirects=True)
    assert b'Appointment booked successfully' in res.data
    assert called['args']['status'] == 'PENDING'


def test_doctor_can_approve_and_csrf(client, monkeypatch):
    # Fake appointment repo
    class FakeAppointmentRepo:
        def approve_appointment(self, appointment_id, doctor_id):
            called['approved'] = (appointment_id, doctor_id)
            return True
        def list_pending_by_doctor(self, doctor_id):
            return []
        def get_by_doctor_id(self, doctor_id, date=None):
            return []
    called = {}
    monkeypatch.setattr('src.controllers.doctor_controller.appointment_repo', FakeAppointmentRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.appointment_repo', FakeAppointmentRepo(), raising=False)

    # Fake doctor repo so get_by_user_id succeeds
    class FakeDoctorRepo:
        def get_by_user_id(self, user_id):
            class D:
                id = user_id
            return D()
    monkeypatch.setattr('src.controllers.doctor_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.doctor_repo', FakeDoctorRepo(), raising=False)

    # login as doctor in session
    with client.session_transaction() as sess:
        sess['role'] = 'doctor'
        sess['user_id'] = 5
        sess['status'] = 'active'
        sess['csrf_token'] = 'tok'

    # POST with invalid token
    res = client.post('/doctor/appointment/1/approve', data={'csrf_token': 'bad'}, follow_redirects=True)
    assert b'Invalid CSRF token' in res.data

    # POST with valid token
    res2 = client.post('/doctor/appointment/1/approve', data={'csrf_token': 'tok'}, follow_redirects=True)
    assert b'Appointment approved' in res2.data
    assert called.get('approved') == (1, 5)
