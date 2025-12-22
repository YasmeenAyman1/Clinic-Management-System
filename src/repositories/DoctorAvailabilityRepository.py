from typing import List, Optional
from models.doctorAvailability_model import DoctorAvailability
from repositories.BaseRepository import BaseRepository

class DoctorAvailabilityRepository(BaseRepository):
    def create_availability(self, doctor_id: int, date: str, start_time: str, end_time: str) -> Optional[DoctorAvailability]:
        cursor = self.db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO doctor_availability (doctor_id, date, start_time, end_time)
                VALUES (%s, %s, %s, %s)
                """,
                (doctor_id, date, start_time, end_time),
            )
            self.db.commit()
            return self.get_by_id(cursor.lastrowid)
        except Exception as e:
            self.db.rollback()
            print(f"Error creating availability: {e}")
            return None
        finally:
            cursor.close()

    def get_by_id(self, av_id: int) -> Optional[DoctorAvailability]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, doctor_id, date, start_time, end_time, create_at AS create_at FROM doctor_availability WHERE id = %s",
            (av_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            row = self._format_availability_row(row)
            return DoctorAvailability(**row)
        return None

    def list_by_doctor(self, doctor_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[DoctorAvailability]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        if start_date and end_date:
            cursor.execute(
                """SELECT id, doctor_id, date, start_time, end_time, create_at
                FROM doctor_availability 
                WHERE doctor_id = %s 
                AND date BETWEEN %s 
                AND %s ORDER BY date, start_time""",
                (doctor_id, start_date, end_date),
            )
        else:
            cursor.execute(
                "SELECT id, doctor_id, date, start_time, end_time, create_at AS create_at FROM doctor_availability WHERE doctor_id = %s ORDER BY date, start_time",
                (doctor_id,)
            )
        rows = cursor.fetchall()
        print(f"DEBUG list_by_doctor: Found {len(rows)} entries for doctor {doctor_id}")
        cursor.close()
        
        availabilities = []
        for row in rows:
            row = self._format_availability_row(row)
            availabilities.append(DoctorAvailability(**row))
        
        return availabilities

    def delete_availability(self, av_id: int) -> bool:
        cursor = self.db.cursor()
        try:
            cursor.execute("DELETE FROM doctor_availability WHERE id = %s", (av_id,))
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting availability: {e}")
            return False
        finally:
            cursor.close()

    def _format_availability_row(self, row: dict) -> dict:
        """Convert database types to strings for DoctorAvailability model"""
        import datetime
        from datetime import timedelta
        
        formatted = row.copy()
        
        # Convert date object to string
        if isinstance(formatted.get('date'), datetime.date):
            formatted['date'] = formatted['date'].isoformat()
        
        # Convert time/timedelta objects to strings
        start_time = formatted.get('start_time')
        end_time = formatted.get('end_time')
        
        # Handle start_time
        if isinstance(start_time, timedelta):
            total_seconds = int(start_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            formatted['start_time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        elif isinstance(start_time, datetime.time):
            formatted['start_time'] = start_time.strftime('%H:%M:%S')
        
        # Handle end_time
        if isinstance(end_time, timedelta):
            total_seconds = int(end_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            formatted['end_time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        elif isinstance(end_time, datetime.time):
            formatted['end_time'] = end_time.strftime('%H:%M:%S')
        
        # Convert datetime to string if needed
        if isinstance(formatted.get('create_at'), datetime.datetime):
            formatted['create_at'] = formatted['create_at'].isoformat(sep=' ', timespec='seconds')
        
        return formatted