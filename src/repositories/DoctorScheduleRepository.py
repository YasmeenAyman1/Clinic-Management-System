from typing import List, Optional
from models.doctorSchedule_model import DoctorSchedule
from repositories.BaseRepository import BaseRepository

class DoctorScheduleRepository(BaseRepository):
    def create_schedule(self, doctor_id: int, day_of_week: str, start_time: str, end_time: str) -> Optional[DoctorSchedule]:
        """Add a weekly schedule entry for a doctor"""
        cursor = self.db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO doctor_schedule (doctor_id, day_of_week, startTime, endTime)
                VALUES (%s, %s, %s, %s)
                """,
                (doctor_id, day_of_week, start_time, end_time),
            )
            self.db.commit()
            schedule_id = cursor.lastrowid
            return self.get_by_id(schedule_id)
        except Exception as e:
            self.db.rollback()
            print(f"Error creating schedule: {e}")
            return None
        finally:
            cursor.close()

    def get_by_id(self, schedule_id: int) -> Optional[DoctorSchedule]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, doctor_id, day_of_week, startTime, endTime, create_at AS created_at
            FROM doctor_schedule WHERE id = %s
            """,
            (schedule_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            row = self._format_schedule_row(row)
            return DoctorSchedule(**row)
        return None

    def get_schedule_by_doctor(self, doctor_id: int) -> List[DoctorSchedule]:
        """Get weekly schedule for a doctor"""
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, doctor_id, day_of_week, startTime, endTime, create_at AS created_at
            FROM doctor_schedule
            WHERE doctor_id = %s
            ORDER BY 
                CASE day_of_week
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                    WHEN 'Sunday' THEN 7
                    ELSE 8
                END
            """,
            (doctor_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        
        schedules = []
        for row in rows:
            row = self._format_schedule_row(row)
            schedules.append(DoctorSchedule(**row))
        return schedules

    def _format_schedule_row(self, row: dict) -> dict:
        """Convert database types to strings for DoctorSchedule model"""
        import datetime
        
        formatted = row.copy()
        
        # Convert time objects to strings
        if isinstance(formatted.get('startTime'), datetime.time):
            formatted['startTime'] = formatted['startTime'].strftime('%H:%M:%S')
        
        if isinstance(formatted.get('endTime'), datetime.time):
            formatted['endTime'] = formatted['endTime'].strftime('%H:%M:%S')
        
        # Convert datetime to string if needed
        if isinstance(formatted.get('created_at'), datetime.datetime):
            formatted['created_at'] = formatted['created_at'].isoformat(sep=' ', timespec='seconds')
        
        return formatted

    def delete_schedule(self, schedule_id: int) -> bool:
        cursor = self.db.cursor()
        try:
            cursor.execute("DELETE FROM doctor_schedule WHERE id = %s", (schedule_id,))
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting schedule: {e}")
            return False
        finally:
            cursor.close()

    def delete_schedule_by_doctor(self, doctor_id: int) -> bool:
        cursor = self.db.cursor()
        try:
            cursor.execute("DELETE FROM doctor_schedule WHERE doctor_id = %s", (doctor_id,))
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting doctor schedule: {e}")
            return False
        finally:
            cursor.close()

    def update_schedule(self, schedule_id: int, day_of_week: str, start_time: str, end_time: str) -> bool:
        cursor = self.db.cursor()
        try:
            cursor.execute(
                "UPDATE doctor_schedule SET day_of_week = %s, startTime = %s, endTime = %s WHERE id = %s",
                (day_of_week, start_time, end_time, schedule_id)
            )
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error updating schedule: {e}")
            return False
        finally:
            cursor.close()

    def get_schedule(self, doctor_id: int) -> Optional[str]:
        """Get schedule as formatted string (legacy method)"""
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT schedule FROM doctor WHERE id = %s",
            (doctor_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else None