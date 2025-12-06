class UploadedFile:
    def __init__(self,id,file_path,file_type,uploaded_by_user_id,upload_date,record_id,patient_id,appointment_id,created_at):
        self.id=id
        self.file_path=file_path
        self.file_type=file_type
        self.uploaded_by_user_id=uploaded_by_user_id
        self.upload_date=upload_date
        self.record_id=record_id
        self.patient_id=patient_id
        self.appointment_id=appointment_id
        self.created_by=created_at
