class Assistant:
    def __init__(self,id,firstName,lastName,phone,user_id,doctor_id,created_at):
        self.id=id
        self.firstName=firstName
        self.lastName=lastName
        self.phone=phone
        self.user_id=user_id
        self.doctor_id=doctor_id
        self.created_at=created_at
        self.doctor_name = None
        self.doctor_specialization = None
        self.patient_name = None
        self.patient_phone = None