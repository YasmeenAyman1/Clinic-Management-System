from repositories.UserRepository import UserRepository
from repositories.PatientRepository import PatientRepository
from repositories.DoctorRepository import DoctorRepository
from repositories.AssistantRepository import AssistantRepository
from repositories.AppointmentRepository import AppointmentRepository
from repositories.ContactRepository import ContactRepository
from repositories.MedicalRecordRepository import MedicalRecordRepository
from repositories.UploadedFileRepository import UploadedFileRepository
from repositories.DoctorScheduleRepository import DoctorScheduleRepository
from repositories.DoctorAvailabilityRepository import DoctorAvailabilityRepository
from repositories.AdminAuditRepository import AdminAuditRepository
from repositories.TaskRepository import TaskRepository

class RepositoryFactory:
    @staticmethod
    def get_repository(entity_type: str):
        if entity_type == "user":
            return UserRepository()
        if entity_type == "patient":
            return PatientRepository()
        if entity_type == "doctor":
            return DoctorRepository()
        if entity_type == "assistant":
            return AssistantRepository()
        if entity_type == "appointment":
            return AppointmentRepository()
        if entity_type == "contact":
            return ContactRepository()
        if entity_type == "medical_record":
            return MedicalRecordRepository()
        if entity_type == "uploaded_file":
            return UploadedFileRepository()
        if entity_type == "doctor_schedule":
            return DoctorScheduleRepository()
        if entity_type == "doctor_availability":
            return DoctorAvailabilityRepository()
        if entity_type == "admin_audit":
            return AdminAuditRepository()
        if entity_type == "task":
             return TaskRepository()
        raise ValueError(f"Unknown repository type: {entity_type}")
