class DoctorAvailability:
    def __init__(self, id: int, doctor_id: int, date: str, start_time: str, end_time: str, created_at=None):
        self.id = id
        self.doctor_id = doctor_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.created_at = created_at

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "date": self.date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "created_at": self.created_at,
        }
    