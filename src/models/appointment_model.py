class Appointment:
    def __init__(self,id, patient_name, doctor_name, date, time):
        self.id = id
        self.patient_name = patient_name
        self.doctor_name = doctor_name
        self.date = date
        self.time = time

    @staticmethod
    def selectTime():
        ...
    @staticmethod
    def changeTime():
        ...
    @staticmethod
    def cancelAppointment():
        ...
    @staticmethod
    def bookAppointment():
        ...