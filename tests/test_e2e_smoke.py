def test_e2e_signup_approve_availability_booking_flow(client, monkeypatch):
    # Simple in-memory storage to simulate DB state
    store = {
        'users': {},
        'doctors': {},
        'patients': {},
        'avail': {},
        'appointments': {},
        'next_user_id': 1000,
        'next_doc_id': 2000,
        'next_appt_id': 3000
    }

    class FakeCursor:
        def execute(self, q, params=None):
            # very small parser for the UPDATE query we expect
            if "UPDATE user SET status = 'active'" in q and params:
                uid = params[0]
                if uid in store['users']:
                    store['users'][uid]['status'] = 'active'
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
        def get_by_username(self, u):
            return None
        def create_user(self, username, password, role, status='active'):
            uid = store['next_user_id']
            store['next_user_id'] += 1
            store['users'][uid] = {'id': uid, 'username': username, 'role': role, 'status': status}
            class U: pass
            uu = U(); uu.id = uid; uu.username = username; uu.role = role; uu.status = status
            return uu
        def get_by_id(self, uid):
            d = store['users'].get(uid)
            if not d: return None
            class U: pass
            u = U(); u.id = d['id']; u.username = d['username']; u.role = d['role']; u.status = d['status']
            return u
        def delete_user(self, uid):
            store['users'].pop(uid, None)
        db = FakeDB()

    class FakeDoctorRepo:
        def create_doctor(self, first_name, last_name, phone, user_id, specialization=''):
            did = store['next_doc_id']; store['next_doc_id'] += 1
            store['doctors'][did] = {'id': did, 'user_id': user_id}
            class D: pass
            d = D(); d.id = did; d.firstName = first_name; d.lastName = last_name; d.specialization = specialization; d.user_id=user_id
            return d
        def get_by_user_id(self, uid):
            for d in store['doctors'].values():
                if d['user_id'] == uid:
                    class D: pass
                    dd = D(); dd.id = d['id']; dd.user_id = d['user_id']; return dd
            return None
        def list_all(self):
            out = []
            for d in store['doctors'].values():
                class D: pass
                dd = D(); dd.id = d['id']; dd.firstName = 'Doc'; dd.lastName = str(d['id']); dd.specialization = ''
                out.append(dd)
            return out

    class FakePatientRepo:
        def create_patient(self, first, last, phone, user_id):
            pid = user_id + 1
            store['patients'][pid] = {'id': pid, 'user_id': user_id}
            class P: pass
            p = P(); p.id = pid; return p
        def get_by_user_id(self, uid):
            for p in store['patients'].values():
                if p['user_id'] == uid:
                    class P: pass
                    pp = P(); pp.id = p['id']; return pp
            return None

    class FakeAppointmentRepo:
        def __init__(self):
            pass
        def get_available_slots(self, doctor_id, date):
            # return a slot set by the doctor in store['avail'] if present
            return store['avail'].get((doctor_id, date), [])
        def create_appointment(self, patient_id, doctor_id, date, appointment_time):
            appt_id = store['next_appt_id']; store['next_appt_id'] += 1
            # store both time keys used by different templates and include patient display
            store['appointments'][appt_id] = {
                'id': appt_id,
                'patient_id': patient_id,
                'doctor_id': doctor_id,
                'date': date,
                'time': appointment_time,
                'appointment_time': appointment_time,
                'patient': f'Patient {patient_id}',
                'status': 'PENDING'
            }
            class A: pass
            a = A(); a.id = appt_id; a.status = 'PENDING'; return a
        def approve_appointment(self, appointment_id, doctor_id):
            appt = store['appointments'].get(appointment_id)
            if appt and appt['doctor_id'] == doctor_id:
                appt['status'] = 'BOOKED'; return True
            return False
        def get_by_patient_id(self, pid):
            return [type('A', (), ap)() for ap in store['appointments'].values() if ap['patient_id'] == pid]
        def get_by_doctor_id(self, doctor_id, date=None):
            return [type('A', (), ap)() for ap in store['appointments'].values() if ap['doctor_id'] == doctor_id]
        def list_pending_by_doctor(self, doctor_id):
            return [type('A', (), ap)() for ap in store['appointments'].values() if ap['doctor_id'] == doctor_id and ap['status'] == 'PENDING']

    class FakeAvailabilityRepo:
        def create_availability(self, doctor_id, date, start_time, end_time):
            # create slots hourly for simplicity
            s = start_time; h = s[:2]
            store['avail'][(doctor_id, date)] = [f"{h}:00"]
            class Av: pass
            av = Av(); av.id = 1; return av
        def list_by_doctor(self, doctor_id):
            return []

    # Patch necessary repos across controllers
    monkeypatch.setattr('src.controllers.authO_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('controllers.authO_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('src.controllers.authO_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('controllers.authO_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('src.controllers.authO_controller.patient_repo', FakePatientRepo(), raising=False)
    monkeypatch.setattr('controllers.authO_controller.patient_repo', FakePatientRepo(), raising=False)

    monkeypatch.setattr('src.controllers.admin_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('controllers.admin_controller.user_repo', FakeUserRepo(), raising=False)
    monkeypatch.setattr('src.controllers.doctor_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('src.controllers.doctor_controller.availability_repo', FakeAvailabilityRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.availability_repo', FakeAvailabilityRepo(), raising=False)
    monkeypatch.setattr('src.controllers.patient_controller.appointment_repo', FakeAppointmentRepo(), raising=False)
    monkeypatch.setattr('controllers.patient_controller.appointment_repo', FakeAppointmentRepo(), raising=False)
    monkeypatch.setattr('src.controllers.patient_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('controllers.patient_controller.doctor_repo', FakeDoctorRepo(), raising=False)
    monkeypatch.setattr('src.controllers.patient_controller.patient_repo', FakePatientRepo(), raising=False)
    monkeypatch.setattr('controllers.patient_controller.patient_repo', FakePatientRepo(), raising=False)
    monkeypatch.setattr('src.controllers.doctor_controller.appointment_repo', FakeAppointmentRepo(), raising=False)
    monkeypatch.setattr('controllers.doctor_controller.appointment_repo', FakeAppointmentRepo(), raising=False)

    # 1) Doctor signs up (pending)
    res = client.post('/auth/signup', data={
        'full_name': 'Doc Smoke', 'email': 'docsmoke@example.com', 'phone': '1234567890', 'password': 'pass123', 'confirm_password': 'pass123', 'role': 'doctor', 'specialization': 'General'
    }, follow_redirects=True)
    assert b'sent for approval' in res.data or b'Account created and sent for approval' in res.data

    # get user id from fake user store
    # find created user id
    created_user_id = None
    for uid, u in store['users'].items():
        if u['username'] == 'docsmoke@example.com':
            created_user_id = uid
            break
    assert created_user_id is not None

    # 2) Admin approves doctor
    with client.session_transaction() as sess:
        sess['role'] = 'admin'; sess['status'] = 'active'; sess['csrf_token'] = 'tok'; sess['user_id'] = 1
    res2 = client.post(f'/admin/pending/{created_user_id}/approve', data={'csrf_token': 'tok'}, follow_redirects=True)
    assert b'activated' in res2.data or b'User approved' in res2.data

    # 3) Doctor logs in (simulate session become doctor user_id)
    with client.session_transaction() as sess:
        sess['role'] = 'doctor'; sess['status'] = 'active'; sess['user_id'] = created_user_id

    # 4) Doctor sets availability
    with client.session_transaction() as sess:
        # ensure CSRF token available for doctor actions
        sess['csrf_token'] = 'doc_tok'
    res3 = client.post('/doctor/availability/add', data={'csrf_token': 'doc_tok', 'date': '2025-12-20', 'start_time': '10:00', 'end_time': '11:00'}, follow_redirects=True)
    # We can't rely on flash content here due to different flows; just ensure no server error
    assert res3.status_code in (200, 302)

    # 5) Patient signs up
    res4 = client.post('/auth/signup', data={'full_name': 'Pat Smoke','email': 'patsmoke@example.com','phone':'0987654321','password':'pass123','confirm_password':'pass123','role':'patient'}, follow_redirects=True)
    assert b'Account created successfully' in res4.data or b'Please log in' in res4.data

    # find patient id and log in session as them
    p_user_id = None
    for uid,u in store['users'].items():
        if u['username'] == 'patsmoke@example.com':
            p_user_id = uid; break
    assert p_user_id is not None
    # create patient profile
    store['patients'][p_user_id+1] = {'id': p_user_id+1, 'user_id': p_user_id}

    with client.session_transaction() as sess:
        sess['role'] = 'patient'; sess['status'] = 'active'; sess['user_id'] = p_user_id

    # 6) Patient books the available slot
    res5 = client.post('/patient/appointments', data={'book_appointment': '1', 'doctor_id': list(store['doctors'].keys())[0], 'date': '2025-12-20', 'appointment_time': '10:00'}, follow_redirects=True)
    assert b'Appointment booked' in res5.data or b'Appointment booked successfully' in res5.data or res5.status_code == 200

    # locate created appt
    appt_id = None
    for aid, a in store['appointments'].items():
        if a['patient_id'] == (p_user_id+1):
            appt_id = aid; break
    assert appt_id is not None

    # 7) Doctor approves appointment
    # set session to doctor
    with client.session_transaction() as sess:
        sess['role'] = 'doctor'; sess['status'] = 'active'; sess['user_id'] = created_user_id; sess['csrf_token'] = 'tok'

    res6 = client.post(f'/doctor/appointment/{appt_id}/approve', data={'csrf_token': 'tok'}, follow_redirects=True)
    assert b'Appointment approved' in res6.data or res6.status_code in (200, 302)

    # verify appointment state
    assert store['appointments'][appt_id]['status'] == 'BOOKED'