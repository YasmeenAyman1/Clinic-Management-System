class MedicalRecord:
    def __init__(self, id=None, patient_id=None, doctor_id=None, diagnosis=None, 
                 treatment=None, uploaded_by_user_id=None, upload_date=None, 
                 follow_up_date=None, appointment_id=None, created_at=None):
        self.id = id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.diagnosis = diagnosis
        self.treatment = treatment
        self.uploaded_by_user_id = uploaded_by_user_id
        self.upload_date = upload_date
        self.follow_up_date = follow_up_date
        self.appointment_id = appointment_id
        self.created_at = created_at