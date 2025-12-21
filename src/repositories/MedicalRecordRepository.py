from typing import List, Optional
from models.MedicalRecord_model import MedicalRecord
from repositories.BaseRepository import BaseRepository

class MedicalRecordRepository(BaseRepository):
    def create_record(
        self, 
        patient_id: int, 
        doctor_id: int, 
        diagnosis: str, 
        treatment: str, 
        follow_up_date: Optional[str] = None, 
        appointment_id: Optional[int] = None, 
        uploaded_by_user_id: Optional[int] = None
    ) -> Optional[MedicalRecord]:
        cursor = self.db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO MedicalRecord (diagnosis, treatment, uploaded_by_user_id, upload_date, follow_up_date, doctor_id, patient_id, appointment_id)
                VALUES (%s, %s, %s, CURDATE(), %s, %s, %s, %s)
                """,
                (diagnosis, treatment, uploaded_by_user_id, follow_up_date, doctor_id, patient_id, appointment_id),
            )
            self.db.commit()
            new_id = cursor.lastrowid
            return self.get_by_id(new_id)
        except Exception as e:
            self.db.rollback()
            print(f"Error creating medical record: {e}")
            return None
        finally:
            cursor.close()

    def get_records_by_patient(self, patient_id: int) -> List[MedicalRecord]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, patient_id, doctor_id, diagnosis, treatment, upload_date, follow_up_date, appointment_id, uploaded_by_user_id, create_at AS created_at
            FROM MedicalRecord
            WHERE patient_id = %s
            ORDER BY upload_date DESC
            """,
            (patient_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        
        records = []
        for row in rows:
            try:
                # Create MedicalRecord using dictionary unpacking
                record_data = {
                    'id': row.get("id"),
                    'patient_id': row.get("patient_id"),
                    'doctor_id': row.get("doctor_id"),
                    'diagnosis': row.get("diagnosis"),  # Use 'diagnosis' not 'diagnoisis'
                    'treatment': row.get("treatment"),
                    'uploaded_by_user_id': row.get("uploaded_by_user_id"),
                    'upload_date': row.get("upload_date"),
                    'follow_up_date': row.get("follow_up_date"),
                    'appointment_id': row.get("appointment_id"),
                    'created_at': row.get("created_at"),
                }
                records.append(MedicalRecord(**record_data))
            except Exception as e:
                print(f"Error creating MedicalRecord object: {e}")
                print(f"Row data: {row}")
                continue
        return records

    def get_by_id(self, record_id: int) -> Optional[MedicalRecord]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, patient_id, doctor_id, diagnosis, treatment, upload_date, follow_up_date, appointment_id, uploaded_by_user_id, create_at AS created_at
            FROM MedicalRecord
            WHERE id = %s
            """,
            (record_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return None
        
        try:
            record_data = {
                'id': row.get("id"),
                'patient_id': row.get("patient_id"),
                'doctor_id': row.get("doctor_id"),
                'diagnosis': row.get("diagnosis"),  # Use 'diagnosis' not 'diagnoisis'
                'treatment': row.get("treatment"),
                'uploaded_by_user_id': row.get("uploaded_by_user_id"),
                'upload_date': row.get("upload_date"),
                'follow_up_date': row.get("follow_up_date"),
                'appointment_id': row.get("appointment_id"),
                'created_at': row.get("created_at"),
            }
            return MedicalRecord(**record_data)
        except Exception as e:
            print(f"Error creating MedicalRecord object: {e}")
            print(f"Row data: {row}")
            return None

    def get_patient_records_count(self, patient_id: int) -> int:
        """
        Get the count of medical records for a specific patient
        
        Args:
            patient_id: Patient ID
        
        Returns:
            Number of medical records for the patient
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT COUNT(*) as count 
                FROM MedicalRecord 
                WHERE patient_id = %s
                """,
                (patient_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error getting patient records count: {e}")
            return 0

    def get_last_visit(self, patient_id: int) -> Optional[str]:
        """
        Get the last visit date for a patient
        
        Args:
            patient_id: Patient ID
        
        Returns:
            Last visit date as string (YYYY-MM-DD) or None
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT MAX(upload_date) as last_visit 
                FROM MedicalRecord 
                WHERE patient_id = %s
                """,
                (patient_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            
            if result and result['last_visit']:
                # Handle both string and datetime objects
                last_visit = result['last_visit']
                if hasattr(last_visit, 'strftime'):
                    return last_visit.strftime('%Y-%m-%d')
                else:
                    return str(last_visit)
            return None
        except Exception as e:
            print(f"Error getting last visit: {e}")
            return None