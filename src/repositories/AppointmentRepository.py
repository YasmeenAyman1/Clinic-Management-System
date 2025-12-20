from typing import List, Optional
from models.appointment_model import Appointment
from repositories.BaseRepository import BaseRepository

class AppointmentRepository(BaseRepository):
    def create_appointment(
        self,
        patient_id: int,
        doctor_id: int,
        date: str,
        appointment_time: str,
        assistant_id: Optional[int] = None,
        status: str = "PENDING"
    ) -> Optional[Appointment]:
        cursor = self.db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO Appointment (patient_id, doctor_id, date, appointment_time, assistant_id, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (patient_id, doctor_id, date, appointment_time, assistant_id, status),
            )
            self.db.commit()
            return self.get_by_id(cursor.lastrowid)
        except Exception as e:
            self.db.rollback()
            print(f"Error creating appointment: {e}")
            return None
        finally:
            cursor.close()

    def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, appointment_time, status, date, follow_up_date, assistant_id, doctor_id, patient_id, create_at AS created_at
            FROM Appointment
            WHERE id = %s
            """,
            (appointment_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return Appointment(**row) if row else None

    def get_by_patient_id(self, patient_id: int) -> List[Appointment]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, appointment_time, status, date, follow_up_date, assistant_id, doctor_id, patient_id, create_at AS created_at
            FROM Appointment
            WHERE patient_id = %s
            ORDER BY date DESC, appointment_time DESC
            """,
            (patient_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [Appointment(**row) for row in rows] if rows else []

    def get_by_doctor_id(self, doctor_id: int, date: Optional[str] = None) -> List[Appointment]:
        cursor = self.db.cursor(dictionary=True)
        if date:
            cursor.execute(
                """
                SELECT id, appointment_time, status, date, follow_up_date, assistant_id, doctor_id, patient_id, create_at AS created_at
                FROM Appointment
                WHERE doctor_id = %s AND date = %s
                ORDER BY appointment_time ASC
                """,
                (doctor_id, date),
            )
        else:
            cursor.execute(
                """
                SELECT id, appointment_time, status, date, follow_up_date, assistant_id, doctor_id, patient_id, create_at AS created_at
                FROM Appointment
                WHERE doctor_id = %s
                ORDER BY date DESC, appointment_time DESC
                """,
                (doctor_id,),
            )
        rows = cursor.fetchall()
        cursor.close()
        return [Appointment(**row) for row in rows] if rows else []

    def get_available_slots(self, doctor_id: int, date: str) -> List[str]:
        """Get available time slots for a doctor on a specific date."""
        import datetime

        cursor = self.db.cursor()
        # Get booked/pending times
        cursor.execute(
            """
            SELECT appointment_time FROM Appointment
            WHERE doctor_id = %s AND date = %s AND status IN ('BOOKED', 'PENDING')
            """,
            (doctor_id, date),
        )
        booked_times = [row[0].strftime("%H:%M") if hasattr(row[0], 'strftime') else str(row[0]) for row in cursor.fetchall()]

        # Get explicit availability for this date
        cursor.execute(
            "SELECT start_time, end_time FROM doctor_availability WHERE doctor_id = %s AND date = %s",
            (doctor_id, date),
        )
        availability_rows = cursor.fetchall()

        slots = []
        if availability_rows:
            for row in availability_rows:
                start = row[0]
                end = row[1]
                # Normalize to time objects if strings
                if isinstance(start, str):
                    start = datetime.datetime.strptime(start, "%H:%M:%S" if ':' in start else "%H:%M").time()
                if isinstance(end, str):
                    end = datetime.datetime.strptime(end, "%H:%M:%S" if ':' in end else "%H:%M").time()

                # build slots between start (inclusive) and end (exclusive)
                current = datetime.datetime.combine(datetime.date.fromisoformat(date), start)
                end_dt = datetime.datetime.combine(datetime.date.fromisoformat(date), end)
                while current + datetime.timedelta(minutes=0) < end_dt:
                    time_str = current.strftime("%H:%M")
                    if time_str not in booked_times:
                        slots.append(time_str)
                    current += datetime.timedelta(minutes=30)
        else:
            # Fallback to business hours 09:00-17:00
            for hour in range(9, 17):
                for minute in [0, 30]:
                    time_str = f"{hour:02d}:{minute:02d}"
                    if time_str not in booked_times:
                        slots.append(time_str)

        cursor.close()
        return slots

    def cancel_appointment(self, appointment_id: int, patient_id: int) -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE Appointment SET status = 'CANCELLED' WHERE id = %s AND patient_id = %s",
            (appointment_id, patient_id)
        )
        self.db.commit()
        cursor.close()
        return True

    def approve_appointment(self, appointment_id: int, doctor_id: int) -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE Appointment SET status = 'BOOKED' WHERE id = %s AND doctor_id = %s AND status = 'PENDING'",
            (appointment_id, doctor_id)
        )
        self.db.commit()
        cursor.close()
        return True

    def reject_appointment(self, appointment_id: int, doctor_id: int) -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE Appointment SET status = 'REJECTED' WHERE id = %s AND doctor_id = %s AND status = 'PENDING'",
            (appointment_id, doctor_id)
        )
        self.db.commit()
        cursor.close()
        return True

    def list_pending_by_doctor(self, doctor_id: int) -> List[Appointment]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, appointment_time, status, date, follow_up_date, assistant_id, doctor_id, patient_id, create_at AS created_at FROM Appointment WHERE doctor_id = %s AND status = 'PENDING' ORDER BY date ASC, appointment_time ASC",
            (doctor_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return [Appointment(**row) for row in rows] if rows else []