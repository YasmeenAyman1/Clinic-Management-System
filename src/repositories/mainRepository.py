from typing import List, Optional

from database.db_singleton import DatabaseConnection
from models.appointment_model import Appointment
from models.assistant_model import Assistant
from models.doctor_model import Doctor
from models.patient_model import Patient
from models.user_model import User
from models.upload_model import UploadedFile
from models.MedicalRecord_model import MedicalRecord
from models.contact_model import Contact
from models.doctorAvailability_model import DoctorAvailability
from models.adminAudit_model import AdminAudit

class BaseRepository:# instead of repeating: db = DatabaseConnection().get_connection()
    def __init__(self, connection=None):
        self.db = connection or DatabaseConnection().get_connection()


class UserRepository(BaseRepository):
    def create_user(self, username: str, password_hash: str, role: str = "patient", status: str = "active") -> Optional[User]:
        #Cursor = tool to run SQL
        cursor = self.db.cursor()

        #%s prevents SQL Injection, MySQL safely inserts values, Correct & secure
        cursor.execute(
            """
            INSERT INTO user (username, password, role, status)
            VALUES (%s, %s, %s, %s)
            """,
            (username, password_hash, role, status),
        )

        #REQUIRED for INSERT / UPDATE / DELETE, Without this → data not saved
        self.db.commit()
        return self.get_by_id(cursor.lastrowid)
    
    def delete_user(self, user_id: int) -> bool:
        try:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
            self.db.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def get_by_username(self, username: str) -> Optional[User]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, password, role, status, update_at AS updated_at, create_at AS created_at FROM user WHERE username = %s",
            (username,),
        ) 
        row = cursor.fetchone()
        cursor.close()
        return User(**row) if row else None

    def get_by_id(self, user_id: int) -> Optional[User]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, password, role, status, update_at AS updated_at, create_at AS created_at FROM user WHERE id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return User(**row) if row else None

    def list_users(self) -> List[User]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, password, role, status, update_at AS updated_at, create_at AS created_at FROM user"
        )
        rows = cursor.fetchall()
        cursor.close()
        return [User(**row) for row in rows] if rows else []

    def list_pending_users(self, role: Optional[str] = None) -> List[User]:
        cursor = self.db.cursor(dictionary=True)
        if role:
            cursor.execute(
                "SELECT id, username, password, role, status, update_at AS updated_at, create_at AS created_at FROM user WHERE role = %s AND status = 'pending'",
                (role,)
            )
        else:
            cursor.execute(
                "SELECT id, username, password, role, status, update_at AS updated_at, create_at AS created_at FROM user WHERE status = 'pending'"
            )
        rows = cursor.fetchall()
        cursor.close()
        return [User(**row) for row in rows] if rows else []

    def update_username(self, user_id: int, new_username: str) -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE user SET username = %s WHERE id = %s",
            (new_username, user_id)
        )
        self.db.commit()
        cursor.close()
        return True
#=============================================================================
#=============================================================================
#=============================================================================   
class PatientRepository(BaseRepository):
    def create_patient(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        user_id: Optional[int],
        gender: str = "other",
        birth_date: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Optional[Patient]:
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT INTO patient (firstName, lastName, gender, phone, user_id, birth_date, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (first_name, last_name, gender, phone, user_id, birth_date, address),
        )
        self.db.commit()
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, patient_id: int) -> Optional[Patient]:#I fell this is may be an error, because it should be id not patient_id.
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, firstName, lastName, gender, phone, birth_date, address, user_id, create_at AS created_at
            FROM patient
            WHERE id = %s
            """,
            (patient_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return Patient(**row) if row else None

    def get_by_user_id(self, user_id: int) -> Optional[Patient]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, firstName, lastName, gender, phone, birth_date, address, user_id, create_at AS created_at
            FROM patient
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return Patient(**row) if row else None

    def update_patient(self, patient_id: int, first_name: str, last_name: str, phone: str, birth_date: str, address: str) -> bool:#I fell this is may be an error, because it should be id not patient_id.
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE patient SET firstName = %s, lastName = %s, phone = %s, birth_date = %s, address = %s WHERE id = %s",
            (first_name, last_name, phone, birth_date, address, patient_id)
        )#I fell this is may be an error, because it should be id not patient_id.
        self.db.commit()
        cursor.close()
        return True
#=============================================================================
#=============================================================================
#=============================================================================
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
            cursor.close()#=============================================================================
#=============================================================================
#=============================================================================   
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
    
    def get_schedule_by_user_id(self, user_id: int) -> Optional[str]:
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT d.schedule
            FROM doctor d
            JOIN user u ON d.user_id = u.id
            WHERE u.id = %s
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else None
    
    def list_schedules(self) -> List[dict]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, firstName, lastName, schedule
            FROM doctor
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows if rows else []


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
            "SELECT id, doctor_id, date, start_time, end_time, create_at AS created_at FROM doctor_availability WHERE id = %s",
            (av_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return DoctorAvailability(**row) if row else None

    def list_by_doctor(self, doctor_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[DoctorAvailability]:
        cursor = self.db.cursor(dictionary=True)
        if start_date and end_date:
            cursor.execute(
                "SELECT id, doctor_id, date, start_time, end_time, create_at AS created_at FROM doctor_availability WHERE doctor_id = %s AND date BETWEEN %s AND %s ORDER BY date, start_time",
                (doctor_id, start_date, end_date),
            )
        else:
            cursor.execute(
                "SELECT id, doctor_id, date, start_time, end_time, create_at AS created_at FROM doctor_availability WHERE doctor_id = %s ORDER BY date, start_time",
                (doctor_id,)
            )
        rows = cursor.fetchall()
        cursor.close()
        return [DoctorAvailability(**r) for r in rows] if rows else []

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
#=============================================================================
#=============================================================================
#=============================================================================
class AssistantRepository(BaseRepository):
    def get_by_user_id(self, user_id: int) -> Optional[Assistant]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, firstName, lastName, phone, user_id, doctor_id, create_at AS created_at
            FROM assistant
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return Assistant(**row) if row else None

    def get_by_id(self, assistant_id: int) -> Optional[Assistant]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, firstName, lastName, phone, user_id, doctor_id, create_at AS created_at
            FROM assistant
            WHERE id = %s
            """,
            (assistant_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return Assistant(**row) if row else None

    def create_assistant(self, first_name: str, last_name: str, phone: str, user_id: Optional[int], doctor_id: Optional[int] = None) -> Optional[Assistant]:
        cursor = self.db.cursor()
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
            cursor.close()#=============================================================================
#=============================================================================
#=============================================================================
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
        """Get available time slots for a doctor on a specific date.
        Uses explicit doctor_availability entries when present; otherwise falls back to default business hours.
        Excludes times already BOOKED or PENDING.
        """
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
#=============================================================================
#=============================================================================
#=============================================================================
class ContactRepository(BaseRepository):
    def save_message(self, name: str, email: str, message: str) -> Optional[Contact]:
        cursor = self.db.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                INSERT INTO Contact (name, email, message)
                VALUES (%s, %s, %s)
                """,
                (name, email, message),
            )
            self.db.commit()
            new_id = cursor.lastrowid
            cursor.execute(
                "SELECT id, name, email, message, create_at AS created_at FROM Contact WHERE id = %s",
                (new_id,),
            )
            row = cursor.fetchone()
            return Contact(**row) if row else None
        except Exception as e:
            self.db.rollback()
            print(f"Error saving contact message: {e}")
            return None
        finally:
            cursor.close()
#=============================================================================
#=============================================================================
#=============================================================================   
class MedicalRecordRepository(BaseRepository):
    def create_record(self, patient_id: int, doctor_id: int, diagnosis: str, treatment: str, follow_up_date: Optional[str] = None, appointment_id: Optional[int] = None, uploaded_by_user_id: Optional[int] = None) -> Optional[MedicalRecord]:
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
        return [
            MedicalRecord(
                id=row.get("id"),
                diagnoisis=row.get("diagnosis"),
                treatment=row.get("treatment"),
                uploaded_by_user_id=row.get("uploaded_by_user_id"),
                upload_date=row.get("upload_date"),
                follow_up_date=row.get("follow_up_date"),
                doctor_id=row.get("doctor_id"),
                patient_id=row.get("patient_id"),
                appointment_id=row.get("appointment_id"),
                created_at=row.get("created_at"),
            ) for row in rows
        ] if rows else []
    def get_records_by_doctor(self, doctor_id: int) -> List[MedicalRecord]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, patient_id, doctor_id, diagnosis, treatment, upload_date, follow_up_date, appointment_id, uploaded_by_user_id, create_at AS created_at
            FROM MedicalRecord
            WHERE doctor_id = %s
            ORDER BY upload_date DESC
            """,
            (doctor_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [
            MedicalRecord(
                id=row.get("id"),
                diagnoisis=row.get("diagnosis"),
                treatment=row.get("treatment"),
                uploaded_by_user_id=row.get("uploaded_by_user_id"),
                upload_date=row.get("upload_date"),
                follow_up_date=row.get("follow_up_date"),
                doctor_id=row.get("doctor_id"),
                patient_id=row.get("patient_id"),
                appointment_id=row.get("appointment_id"),
                created_at=row.get("created_at"),
            ) for row in rows
        ] if rows else []
    def delete_record(self, record_id: int) -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "DELETE FROM MedicalRecord WHERE id = %s",
            (record_id,)
        )
        self.db.commit()
        cursor.close()
        return True
    def update_record(self, record_id: int, description: str, date: str) -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE MedicalRecord SET description = %s, date = %s WHERE id = %s",
            (description, date, record_id)
        )
        self.db.commit()
        cursor.close()
        return True
    def get_by_id(self, record_id: int) -> Optional[MedicalRecord]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, patient_id, doctor_id, diagnosis, treatment, upload_date, follow_up_date, create_at AS created_at
            FROM MedicalRecord
            WHERE id = %s
            """,
            (record_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        return MedicalRecord(
            id=row.get("id"),
            diagnoisis=row.get("diagnosis"),
            treatment=row.get("treatment"),
            uploaded_by_user_id=row.get("uploaded_by_user_id"),
            upload_date=row.get("upload_date"),
            follow_up_date=row.get("follow_up_date"),
            doctor_id=row.get("doctor_id"),
            patient_id=row.get("patient_id"),
            appointment_id=row.get("appointment_id"),
            created_at=row.get("created_at"),
        )
    def list_all(self) -> List[MedicalRecord]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, patient_id, doctor_id, description, date, create_at AS created_at
            FROM MedicalRecord
            ORDER BY date DESC
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return [
            MedicalRecord(
                id=row.get("id"),
                diagnoisis=row.get("diagnosis"),
                treatment=row.get("treatment"),
                uploaded_by_user_id=row.get("uploaded_by_user_id"),
                upload_date=row.get("upload_date"),
                follow_up_date=row.get("follow_up_date"),
                doctor_id=row.get("doctor_id"),
                patient_id=row.get("patient_id"),
                appointment_id=row.get("appointment_id"),
                created_at=row.get("created_at"),
            ) for row in rows
        ] if rows else []
#=============================================================================
#=============================================================================
#=============================================================================
class UploadedFileRepository(BaseRepository):
    def save_file(self, filename: str, filepath: str, uploaded_by: int, record_id: Optional[int] = None, patient_id: Optional[int] = None, appointment_id: Optional[int] = None, file_type: Optional[str] = None) -> Optional[UploadedFile]:
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


# ------------------ Admin Audit Repository ------------------
class AdminAuditRepository(BaseRepository):
    def create_entry(self, admin_user_id: int, action: str, target_user_id: Optional[int] = None, target_type: Optional[str] = None, details: Optional[str] = None):
        cursor = self.db.cursor()
        try:
            cursor.execute(
                "INSERT INTO admin_audit (admin_user_id, action, target_user_id, target_type, details) VALUES (%s, %s, %s, %s, %s)",
                (admin_user_id, action, target_user_id, target_type, details),
            )
            self.db.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT id, admin_user_id, action, target_user_id, target_type, details, create_at AS created_at FROM admin_audit WHERE id = %s", (new_id,))
            row = cursor.fetchone()
            return row
        except Exception as e:
            self.db.rollback()
            print(f"Error creating audit entry: {e}")
            return None
        finally:
            cursor.close()

    def list_recent(self, limit: int = 20):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, admin_user_id, action, target_user_id, target_type, details, create_at AS created_at FROM admin_audit ORDER BY create_at DESC LIMIT %s",
            (limit,)
        )
        rows = cursor.fetchall()
        cursor.close()
        from models.adminAudit_model import AdminAudit
        return [AdminAudit(id=r.get('id'), admin_user_id=r.get('admin_user_id'), action=r.get('action'), target_user_id=r.get('target_user_id'), target_type=r.get('target_type'), details=r.get('details'), created_at=r.get('created_at')) for r in rows] if rows else []

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
    
    def get_files_by_user(self, user_id: int) -> List[UploadedFile]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, file_path, file_type, uploaded_by_user_id, upload_date AS upload_date, record_id, patient_id, appointment_id, create_at AS created_at
            FROM UploadedFile
            WHERE uploaded_by_user_id = %s
            ORDER BY upload_date DESC
            """,
            (user_id,),
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
    
    def delete_file(self, file_id: int) -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "DELETE FROM UploadedFile WHERE id = %s",
            (file_id,)
        )
        self.db.commit()
        cursor.close()
        return True
    
    def list_all(self) -> List[UploadedFile]:
        cursor = self.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, file_path, file_type, uploaded_by_user_id, upload_date AS upload_date, record_id, patient_id, appointment_id, create_at AS created_at
            FROM UploadedFile
            ORDER BY upload_date DESC
            """
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
    
    def update_file(self, file_id: int, file_path: str, file_type: str) -> bool:
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE UploadedFile SET file_path = %s, file_type = %s WHERE id = %s",
            (file_path, file_type, file_id)
        )
        self.db.commit()
        cursor.close()
        return True
