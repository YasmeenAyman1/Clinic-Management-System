from typing import Optional
from models.MedicalRecord_model import MedicalRecord
from repositories.BaseRepository import BaseRepository

class DoctorScheduleRepository(BaseRepository):
    def create_schedule(self, doctor_id: int, schedule: str) -> Optional[MedicalRecord]:
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT INTO doctor_schedule (doctor_id, schedule)
            VALUES (%s, %s)
            """,
            (doctor_id, schedule),
        )
        self.db.commit()
        cursor.close()
        return True
    
    def delete_schedule(self, doctor_id: int) -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "DELETE FROM doctor_schedule WHERE doctor_id = %s",
            (doctor_id,)
        )
        self.db.commit()
        cursor.close()
        return True

    def update_schedule(self, doctor_id: int, schedule: str) -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE doctor SET schedule = %s WHERE id = %s",
            (schedule, doctor_id)
        )
        self.db.commit()
        cursor.close()
        return True
    
    def get_schedule(self, doctor_id: int) -> Optional[str]:
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT schedule FROM doctor WHERE id = %s",
            (doctor_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else None