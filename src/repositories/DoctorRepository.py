from typing import List, Optional
from models.doctor_model import Doctor
from repositories.BaseRepository import BaseRepository


#--------------------------------->>>DoctorRepository<<<---------------------------------
class DoctorRepository(BaseRepository):
    def get_by_user_id(self, user_id: int) -> Optional[Doctor]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, firstName, lastName, phone, schedule, user_id, specialization, create_at AS created_at
            FROM doctor
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return Doctor(**row) if row else None

    def get_by_id(self, doctor_id: int) -> Optional[Doctor]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, firstName, lastName, phone, schedule, user_id, specialization, create_at AS created_at
            FROM doctor
            WHERE id = %s
            """,
            (doctor_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return Doctor(**row) if row else None

    def list_all(self) -> List[Doctor]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, firstName, lastName, phone, schedule, user_id, specialization, create_at AS created_at
            FROM doctor
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return [Doctor(**row) for row in rows] if rows else []

    def list_by_specialization(self, specialization: str) -> List[Doctor]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, firstName, lastName, phone, schedule, user_id, specialization, create_at AS created_at
            FROM doctor
            WHERE specialization = %s
            """,
            (specialization,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [Doctor(**row) for row in rows] if rows else []

    def update_doctor(self, doctor_id: int, first_name: str, last_name: str, phone: str, specialization: str) -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE doctor SET firstName = %s, lastName = %s, phone = %s, specialization = %s WHERE id = %s",
            (first_name, last_name, phone, specialization, doctor_id)
        )
        self.db.commit()
        cursor.close()
        return True

    def create_doctor(self, first_name: str, last_name: str, phone: str, user_id: Optional[int], specialization: str = "General", schedule: Optional[str] = None) -> Optional[Doctor]:
        cursor = self.db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO doctor (firstName, lastName, phone, schedule, user_id, specialization)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (first_name, last_name, phone, schedule, user_id, specialization),
            )
            self.db.commit()
            return self.get_by_id(cursor.lastrowid)
        except Exception as e:
            self.db.rollback()
            print(f"Error creating doctor: {e}")
            return None
        finally:
            cursor.close()
