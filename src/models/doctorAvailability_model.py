class DoctorAvailability:
    def __init__(self, id, doctor_id, date, start_time, end_time, create_at):
        self.id = id
        self.doctor_id = doctor_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.create_at = create_at

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "date": self.date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "create_at": self.create_at,
        }