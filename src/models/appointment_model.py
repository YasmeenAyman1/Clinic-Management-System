class Appointment:
    def __init__(self,id, appointment_time,status, date,follow_up_date,assistant_id,doctor_id,patient_id,created_at):
        self.id = id
        self.appointment_time=appointment_time
        self.status = status
        self.date = date
        self.follow_up_date = follow_up_date
        self.assistant_id=assistant_id
        self.patient_id=patient_id
        self.doctor_id=doctor_id
        self.created_at=created_at
