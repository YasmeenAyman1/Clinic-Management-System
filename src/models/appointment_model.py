class Appointment:
    def __init__(self, id, patient_id, doctor_id, date, appointment_time, status, follow_up_date=None, assistant_id=None, created_at=None):
        self.id = id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.date = date
        self.appointment_time = appointment_time
        self.status = status
        self.follow_up_date = follow_up_date
        self.assistant_id = assistant_id
        self.created_at = created_at