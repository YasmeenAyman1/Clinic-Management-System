from typing import List, Optional
from models.doctor_model import Doctor
from repositories.BaseRepository import BaseRepository


#--------------------------------->>>DoctorRepository<<<---------------------------------
class DoctorRepository(BaseRepository):
    def get_by_user_id(self, user_id: int) -> Optional[Doctor]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        cursor.execute(
            """
            SELECT id, firstName, lastName, phone, schedule, user_id, specialization, create_at AS create_at
            FROM doctor
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return Doctor(**row) if row else None

    def get_by_id(self, doctor_id: int) -> Optional[Doctor]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT id, firstName, lastName, phone, schedule, user_id, specialization, create_at AS create_at
                FROM doctor
                WHERE id = %s
                """,
                (doctor_id,),
            )
            row = cursor.fetchone()
            return Doctor(**row) if row else None
        finally:
            cursor.close()

    def list_all(self) -> List[Doctor]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT id, firstName, lastName, phone, schedule, user_id, specialization, create_at AS create_at
                FROM doctor
                ORDER BY lastName, firstName
                """
            )
            rows = cursor.fetchall()
            return [Doctor(**row) for row in rows] if rows else []
        finally:
            cursor.close()

    def list_by_specialization(self, specialization: str) -> List[Doctor]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        cursor.execute(
            """
            SELECT id, firstName, lastName, phone, schedule, user_id, specialization, create_at AS create_at
            FROM doctor
            WHERE specialization = %s
            """,
            (specialization,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [Doctor(**row) for row in rows] if rows else []

    def update_doctor(self, doctor_id: int, first_name: str, last_name: str, phone: str, specialization: str) -> bool:
        cursor = self.db.cursor(buffered=True)
        cursor.execute(
            "UPDATE doctor SET firstName = %s, lastName = %s, phone = %s, specialization = %s WHERE id = %s",
            (first_name, last_name, phone, specialization, doctor_id)
        )
        self.db.commit()
        cursor.close()
        return True

    def create_doctor(self, first_name: str, last_name: str, phone: str, user_id: Optional[int], specialization: str = "General", schedule: Optional[str] = None) -> Optional[Doctor]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
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
            
    def search_doctors(self, search_query: str) -> List[Doctor]:
        """Search doctors by name, phone, or specialization."""
        cursor = None
        try:
            cursor = self.db.cursor(dictionary=True, buffered=True)
            search_pattern = f"%{search_query}%"
            cursor.execute(
                """
                SELECT id, firstName, lastName, phone, schedule, user_id, specialization, create_at AS create_at
                FROM doctor
                WHERE firstName LIKE %s 
                OR lastName LIKE %s 
                OR CONCAT(firstName, ' ', lastName) LIKE %s
                OR phone LIKE %s
                OR specialization LIKE %s
                ORDER BY lastName, firstName
                """,
                (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern),
            )
            rows = cursor.fetchall()
            return [Doctor(**row) for row in rows] if rows else []
        except Exception as e:
            print(f"Error searching doctors: {e}")
            return []
        finally:
            if cursor:
                cursor.close()


    def delete_doctor(self, doctor_id: int) -> bool:
        """Delete a doctor by ID."""
        cursor = None
        try:
            cursor = self.db.cursor(buffered=True)
            cursor.execute("DELETE FROM doctor WHERE id = %s", (doctor_id,))
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting doctor {doctor_id}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    def get_total_count(self) -> int:
        """Get total number of doctors."""
        cursor = None
        try:
            cursor = self.db.cursor(buffered=True)
            cursor.execute("SELECT COUNT(*) FROM doctor")
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting doctor count: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()

    def get_counts_by_specialization(self) -> dict:
        """Get count of doctors by specialization."""
        cursor = None
        try:
            cursor = self.db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT specialization, COUNT(*) as count
                FROM doctor
                GROUP BY specialization
                ORDER BY count DESC
                """
            )
            return {row['specialization']: row['count'] for row in cursor.fetchall()}
        except Exception as e:
            print(f"Error getting specialization counts: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()