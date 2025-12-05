from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


class Patient(db.Model, UserMixin):
    phoneNumber = db.Column(db.String(13), primary_key = True,unique=True, nullable=False)
    firstName = db.Column(db.String(150), nullable=False)
    lastName = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    Medical_records = db.relationship('Medical_records', backref='patient', lazy=True)
    Appointments = db.relationship('Appointment', backref='patient', lazy=True)
    UploadedFiles = db.relationship('UploadedFiles', backref='patient', lazy=True)

class Doctor(db.Model, UserMixin):
    phoneNumber = db.Column(db.String(13), primary_key = True,unique=True, nullable=False)
    firstName = db.Column(db.String(150), nullable=False)
    lastName = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    schedule = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(150), nullable=False)
    Medical_records = db.relationship('Medical_records', backref='doctor', lazy=True)
    Appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    Doctor_schedules = db.relationship('Doctor_schedule', backref='doctor', lazy=True)
    

class Assistant(db.Model, UserMixin):
    phoneNumber = db.Column(db.String(13), primary_key = True,unique=True, nullable=False)
    doctorPhoneNumber = db.Column(db.String(13), db.ForeignKey('doctor.phoneNumber'), nullable=False)
    firstName = db.Column(db.String(150), nullable=False)
    lastName = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    Appointments = db.relationship('Appointment', backref='assistant', lazy=True)

class Appointment(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    patientPhoneNumber = db.Column(db.String(13), db.ForeignKey('patient.phoneNumber'), nullable=False)
    doctorPhoneNumber = db.Column(db.String(13), db.ForeignKey('doctor.phoneNumber'), nullable=False)
    assistantPhoneNumber = db.Column(db.String(13), db.ForeignKey('assistant.phoneNumber'), nullable=True)
    appointmentDate = db.Column(db.String(150), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    folowUpDate = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(50), nullable=False)

class Doctor_schedule(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    doctorPhoneNumber = db.Column(db.String(13), db.ForeignKey('doctor.phoneNumber'), nullable=False)
    day = db.Column(db.String(50), nullable=False)
    startTime = db.Column(db.String(50), nullable=False)
    endTime = db.Column(db.String(50), nullable=False)

class Medical_records(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    patientPhoneNumber = db.Column(db.String(13), db.ForeignKey('patient.phoneNumber'), nullable=False)
    doctorPhoneNumber = db.Column(db.String(13), db.ForeignKey('doctor.phoneNumber'), nullable=False)
    AppointmentID = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    uploadBy = db.Column(db.String(50), nullable=False)  # could be doctor or assistant
    diagnosis = db.Column(db.String(500), nullable=False)
    treatment = db.Column(db.String(500), nullable=False)
    date = db.Column(db.String(150), nullable=False)
    UploadedFiles = db.relationship('UploadedFiles', backref='medical_record', lazy=True)   

class UploadedFiles(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    patientPhoneNumber = db.Column(db.String(13), db.ForeignKey('patient.phoneNumber'), nullable=False)
    recordID = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    appointmentID = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    fileType = db.Column(db.String(50), nullable=False)  # e.g., 'image', 'document'
    filePath = db.Column(db.String(200), nullable=False)  # path to the
    uploadDate = db.Column(db.String(150), nullable=False)
    uploadBy = db.Column(db.String(50), nullable=False)  # could be doctor or assistant
    Appointment = db.relationship('Appointment', backref='uploaded_files', lazy=True)



    # def __init__(self, id, username, password, email):
    #     self.id = id
    #     self.username = username
    #     self.password = password
    #     self.email = email
        
    # @staticmethod
    # def get_all():
    #     # mock data for testing
    #     return [
    #         User("mazen", "pass123", "mazen@example.com"),
    #         User("ali", "pass456", "ali@example.com"),
    #     ]

    # @staticmethod
    # def get_by_username(username):
    #     for user in User.get_all():
    #         if user.username == username:
    #             return user
    #     return None
    
    # def profilePage():
    #     ...
    # def signIn():
    #     ...

    # def logIn():
    #     ...
    