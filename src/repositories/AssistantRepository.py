from typing import List, Optional, Dict, Any
from models.assistant_model import Assistant
from repositories.BaseRepository import BaseRepository

class AssistantRepository(BaseRepository):
    def get_by_user_id(self, user_id: int) -> Optional[Assistant]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT id, firstName, lastName, phone, user_id, doctor_id, create_at AS created_at
                FROM assistant
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            return Assistant(**row) if row else None
        finally:
            cursor.close()

    def get_by_id(self, assistant_id: int) -> Optional[Assistant]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT id, firstName, lastName, phone, user_id, doctor_id, create_at AS created_at
                FROM assistant
                WHERE id = %s
                """,
                (assistant_id,),
            )
            row = cursor.fetchone()
            return Assistant(**row) if row else None
        finally:
            cursor.close()

    def create_assistant(self, first_name: str, last_name: str, phone: str, user_id: Optional[int], doctor_id: Optional[int] = None) -> Optional[Assistant]:
        cursor = self.db.cursor(buffered=True)
        try:
            cursor.execute(
                """
                INSERT INTO assistant (firstName, lastName, phone, user_id, doctor_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (first_name, last_name, phone, user_id, doctor_id),
            )
            self.db.commit()
            return self.get_by_id(cursor.lastrowid)
        except Exception as e:
            self.db.rollback()
            print(f"Error creating assistant: {e}")
            return None
        finally:
            cursor.close()

    def get_today_appointments(self, today_date: str):
        """Get today's appointments (should be in AppointmentRepository, but added here for convenience)"""
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT 
                    a.id, 
                    TIME_FORMAT(a.appointment_time, '%%H:%%i') as appointment_time,
                    a.status, 
                    a.date, 
                    a.doctor_id, 
                    a.patient_id,
                    CONCAT(d.firstName, ' ', d.lastName) as doctor_name,
                    CONCAT(p.firstName, ' ', p.lastName) as patient_name, 
                    p.phone
                FROM appointment a
                LEFT JOIN doctor d ON a.doctor_id = d.id
                LEFT JOIN patient p ON a.patient_id = p.id
                WHERE a.date = %s
                ORDER BY a.appointment_time ASC
                """,
                (today_date,)
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def get_appointment_stats(self, today_date: str) -> Dict[str, int]:
        """Get appointment statistics for today"""
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN ('BOOKED', 'CONFIRMED', 'PENDING') THEN 1 ELSE 0 END) as booked,
                    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed
                FROM appointment 
                WHERE date = %s
                """,
                (today_date,)
            )
            result = cursor.fetchone()
            return {
                'total_appointments': result['total'] if result else 0,
                'booked_appointments': result['booked'] if result else 0,
                'completed_appointments': result['completed'] if result else 0
            }
        finally:
            cursor.close()

    def search_assistants(self, search_query: str) -> List[Assistant]:
        """Search assistants by name or phone"""
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            search_pattern = f"%{search_query}%"
            cursor.execute(
                """
                SELECT id, firstName, lastName, phone, user_id, doctor_id, create_at AS created_at
                FROM assistant
                WHERE firstName LIKE %s 
                OR lastName LIKE %s 
                OR CONCAT(firstName, ' ', lastName) LIKE %s
                OR phone LIKE %s
                ORDER BY lastName, firstName
                """,
                (search_pattern, search_pattern, search_pattern, search_pattern),
            )
            rows = cursor.fetchall()
            return [Assistant(**row) for row in rows] if rows else []
        finally:
            cursor.close()

    def update_assistant(self, assistant_id: int, first_name: str, last_name: str, 
                        phone: str, doctor_id: Optional[int] = None) -> bool:
        """Update assistant information"""
        cursor = self.db.cursor(buffered=True)
        try:
            cursor.execute(
                """
                UPDATE assistant 
                SET firstName = %s, lastName = %s, phone = %s, doctor_id = %s
                WHERE id = %s
                """,
                (first_name, last_name, phone, doctor_id, assistant_id)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            print(f"Error updating assistant: {e}")
            return False
        finally:
            cursor.close()

    def delete_assistant(self, assistant_id: int) -> bool:
        """Delete an assistant by ID"""
        cursor = self.db.cursor(buffered=True)
        try:
            cursor.execute("DELETE FROM assistant WHERE id = %s", (assistant_id,))
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting assistant {assistant_id}: {e}")
            return False
        finally:
            cursor.close()

    def get_assistants_by_doctor(self, doctor_id: int) -> List[Assistant]:
        """Get all assistants assigned to a specific doctor"""
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT id, firstName, lastName, phone, user_id, doctor_id, create_at AS created_at
                FROM assistant
                WHERE doctor_id = %s
                ORDER BY lastName, firstName
                """,
                (doctor_id,)
            )
            rows = cursor.fetchall()
            return [Assistant(**row) for row in rows] if rows else []
        finally:
            cursor.close()

    def get_total_count(self) -> int:
        """Get total number of assistants"""
        cursor = self.db.cursor(buffered=True)
        try:
            cursor.execute("SELECT COUNT(*) as count FROM assistant")
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Error getting assistant count: {e}")
            return 0
        finally:
            cursor.close()

    def get_assistant_with_user_info(self, assistant_id: int) -> Optional[Dict[str, Any]]:
        """Get assistant information with user details"""
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT 
                    a.id, a.firstName, a.lastName, a.phone, a.doctor_id, a.create_at AS created_at,
                    u.id as user_id, u.username, u.email, u.role
                FROM assistant a
                LEFT JOIN user u ON a.user_id = u.id
                WHERE a.id = %s
                """,
                (assistant_id,)
            )
            return cursor.fetchone()
        finally:
            cursor.close()