from typing import List, Optional
from models.upload_model import UploadedFile
from repositories.BaseRepository import BaseRepository
class UploadedFileRepository(BaseRepository):
    def save_file(
        self, 
        filename: str, 
        filepath: str, 
        uploaded_by: int, 
        record_id: Optional[int] = None, 
        patient_id: Optional[int] = None, 
        appointment_id: Optional[int] = None, 
        file_type: Optional[str] = None
    ) -> Optional[UploadedFile]:
        """Save uploaded file metadata to the DB and return UploadedFile model."""
        cursor = self.db.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                INSERT INTO UploadedFile (file_path, file_type, uploaded_by_user_id, upload_date, record_id, patient_id, appointment_id)
                VALUES (%s, %s, %s, CURDATE(), %s, %s, %s)
                """,
                (filepath, file_type or filename, uploaded_by, record_id, patient_id, appointment_id),
            )
            self.db.commit()
            new_id = cursor.lastrowid
            return self.get_by_id(new_id)
        except Exception as e:
            self.db.rollback()
            print(f"Error saving file: {e}")
            return None
        finally:
            cursor.close()
    
    def get_by_id(self, file_id: int) -> Optional[UploadedFile]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, file_path, file_type, uploaded_by_user_id, upload_date AS upload_date, record_id, patient_id, appointment_id, create_at AS created_at
            FROM UploadedFile
            WHERE id = %s
            """,
            (file_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        return UploadedFile(
            id=row.get("id"),
            file_path=row.get("file_path"),
            file_type=row.get("file_type"),
            uploaded_by_user_id=row.get("uploaded_by_user_id"),
            upload_date=row.get("upload_date"),
            record_id=row.get("record_id"),
            patient_id=row.get("patient_id"),
            appointment_id=row.get("appointment_id"),
            created_at=row.get("created_at"),
        )
    
    def get_files_by_record(self, record_id: int) -> List[UploadedFile]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, file_path, file_type, uploaded_by_user_id, upload_date AS upload_date, record_id, patient_id, appointment_id, create_at AS created_at
            FROM UploadedFile
            WHERE record_id = %s
            ORDER BY upload_date DESC
            """,
            (record_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [
            UploadedFile(
                id=row.get("id"),
                file_path=row.get("file_path"),
                file_type=row.get("file_type"),
                uploaded_by_user_id=row.get("uploaded_by_user_id"),
                upload_date=row.get("upload_date"),
                record_id=row.get("record_id"),
                patient_id=row.get("patient_id"),
                appointment_id=row.get("appointment_id"),
                created_at=row.get("created_at"),
            ) for row in rows
        ] if rows else []
