from typing import List, Optional
from models.appointment_model import Appointment
from repositories.BaseRepository import BaseRepository
import datetime

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
        cursor = self.db.cursor(buffered=True)
        try:
            # Optional: Check if slot already has non-cancelled appointment
            cursor.execute(
                """
                SELECT id FROM appointment 
                WHERE doctor_id = %s AND date = %s AND appointment_time = %s 
                AND status NOT IN ('CANCELLED', 'REJECTED')
                """,
                (doctor_id, date, appointment_time)
            )
            
            if cursor.fetchone():
                print(f"Slot already booked: {doctor_id}, {date}, {appointment_time}")
                cursor.close()
                return None
            
            cursor.execute(
                """
                INSERT INTO appointment (patient_id, doctor_id, date, appointment_time, assistant_id, status)
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
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT id, patient_id, doctor_id, date, appointment_time, status, 
                       follow_up_date, assistant_id, create_at AS created_at
                FROM appointment
                WHERE id = %s
                """,
                (appointment_id,),
            )
            row = cursor.fetchone()
            
            if row:
                try:
                    # Convert date/time objects to strings if needed
                    if row.get('date') and hasattr(row['date'], 'strftime'):
                        row['date'] = row['date'].strftime('%Y-%m-%d')
                    
                    if row.get('appointment_time') and hasattr(row['appointment_time'], 'strftime'):
                        row['appointment_time'] = row['appointment_time'].strftime('%H:%M')
                    
                    # Create Appointment object with all required parameters
                    appointment = Appointment(
                        id=row['id'],
                        patient_id=row['patient_id'],
                        doctor_id=row['doctor_id'],
                        date=row['date'],
                        appointment_time=row['appointment_time'],
                        status=row['status'],
                        follow_up_date=row.get('follow_up_date'),
                        assistant_id=row.get('assistant_id'),
                        created_at=row.get('created_at')
                    )
                    return appointment
                except Exception as e:
                    print(f"Error creating Appointment object in get_by_id: {e}")
                    print(f"Row data: {row}")
                    return None
            return None
        finally:
            cursor.close()

    def get_by_patient_id(self, patient_id: int) -> List[Appointment]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT 
                    a.id,
                    a.patient_id,
                    a.doctor_id,
                    a.date,
                    a.appointment_time,
                    a.status,
                    a.follow_up_date,
                    a.assistant_id,
                    a.create_at AS created_at,
                    d.firstName as doctor_first_name,
                    d.lastName as doctor_last_name,
                    d.specialization as doctor_specialization
                FROM appointment a
                LEFT JOIN doctor d ON a.doctor_id = d.id
                WHERE a.patient_id = %s
                ORDER BY a.date DESC, a.appointment_time DESC
                """,
                (patient_id,)
            )
            rows = cursor.fetchall()
            
            appointments = []
            for row in rows:
                try:
                    # Convert date/time objects to strings if needed
                    if row.get('date') and hasattr(row['date'], 'strftime'):
                        row['date'] = row['date'].strftime('%Y-%m-%d')
                    
                    if row.get('appointment_time') and hasattr(row['appointment_time'], 'strftime'):
                        row['appointment_time'] = row['appointment_time'].strftime('%H:%M')
                    
                    # Create Appointment object with all required parameters
                    appointment = Appointment(
                        id=row['id'],
                        patient_id=row['patient_id'],
                        doctor_id=row['doctor_id'],
                        date=row['date'],
                        appointment_time=row['appointment_time'],
                        status=row['status'],
                        follow_up_date=row.get('follow_up_date'),
                        assistant_id=row.get('assistant_id'),
                        created_at=row.get('created_at')
                    )
                    
                    # Add extra doctor info as attributes (optional)
                    appointment.doctor_name = None
                    appointment.doctor_specialization = None
                    
                    if row.get('doctor_first_name'):
                        appointment.doctor_name = f"Dr. {row['doctor_first_name']} {row['doctor_last_name']}"
                        appointment.doctor_specialization = row.get('doctor_specialization')
                    
                    appointments.append(appointment)
                    
                except Exception as e:
                    print(f"Error creating Appointment from row: {e}")
                    print(f"Row data: {row}")
                    continue
            
            # DEBUG: Print all appointments
            print(f"DEBUG get_by_patient_id: Found {len(appointments)} appointments for patient {patient_id}")
            for i, appt in enumerate(appointments):
                print(f"  Appointment {i+1}: ID={appt.id}, Date={appt.date}, Status='{appt.status}'")
            
            return appointments
            
        except Exception as e:
            print(f"Error getting appointments by patient_id: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            cursor.close()

    def update_appointment_status(self, appointment_id: int, status: str) -> bool:
        cursor = self.db.cursor(buffered=True)
        try:
            cursor.execute(
                "UPDATE appointment SET status = %s WHERE id = %s",
                (status, appointment_id)
            )
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error updating appointment status: {e}")
            return False
        finally:
            cursor.close()

    def get_upcoming_appointments(self, patient_id: int) -> List[Appointment]:
        """Get upcoming appointments for a patient"""
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT 
                    a.id,
                    a.patient_id,
                    a.doctor_id,
                    a.date,
                    a.appointment_time,
                    a.status,
                    a.follow_up_date,
                    a.assistant_id,
                    a.create_at AS created_at,
                    d.firstName as doctor_first_name,
                    d.lastName as doctor_last_name
                FROM appointment a
                LEFT JOIN doctor d ON a.doctor_id = d.id
                WHERE a.patient_id = %s 
                AND a.status IN ('PENDING', 'CONFIRMED', 'BOOKED')
                AND a.date >= CURDATE()
                ORDER BY a.date ASC, a.appointment_time ASC
                """,
                (patient_id,)
            )
            rows = cursor.fetchall()
            
            appointments = []
            for row in rows:
                try:
                    # Convert date/time objects
                    if row.get('date') and hasattr(row['date'], 'strftime'):
                        row['date'] = row['date'].strftime('%Y-%m-%d')
                    
                    if row.get('appointment_time') and hasattr(row['appointment_time'], 'strftime'):
                        row['appointment_time'] = row['appointment_time'].strftime('%H:%M')
                    
                    appointment = Appointment(
                        id=row['id'],
                        patient_id=row['patient_id'],
                        doctor_id=row['doctor_id'],
                        date=row['date'],
                        appointment_time=row['appointment_time'],
                        status=row['status'],
                        follow_up_date=row.get('follow_up_date'),
                        assistant_id=row.get('assistant_id'),
                        created_at=row.get('created_at')
                    )
                    
                    if row.get('doctor_first_name'):
                        appointment.doctor_name = f"Dr. {row['doctor_first_name']} {row['doctor_last_name']}"
                    
                    appointments.append(appointment)
                except Exception as e:
                    print(f"Error creating Appointment in get_upcoming_appointments: {e}")
                    continue
            
            return appointments
            
        except Exception as e:
            print(f"Error getting upcoming appointments: {e}")
            return []
        finally:
            cursor.close()

    def get_completed_appointments(self, patient_id: int) -> List[Appointment]:
        """Get completed appointments for a patient"""
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT 
                    a.id,
                    a.patient_id,
                    a.doctor_id,
                    a.date,
                    a.appointment_time,
                    a.status,
                    a.follow_up_date,
                    a.assistant_id,
                    a.create_at AS created_at,
                    d.firstName as doctor_first_name,
                    d.lastName as doctor_last_name
                FROM appointment a
                LEFT JOIN doctor d ON a.doctor_id = d.id
                WHERE a.patient_id = %s 
                AND a.status = 'COMPLETED'
                ORDER BY a.date DESC, a.appointment_time DESC
                """,
                (patient_id,)
            )
            rows = cursor.fetchall()
            
            appointments = []
            for row in rows:
                try:
                    # Convert date/time objects
                    if row.get('date') and hasattr(row['date'], 'strftime'):
                        row['date'] = row['date'].strftime('%Y-%m-%d')
                    
                    if row.get('appointment_time') and hasattr(row['appointment_time'], 'strftime'):
                        row['appointment_time'] = row['appointment_time'].strftime('%H:%M')
                    
                    appointment = Appointment(
                        id=row['id'],
                        patient_id=row['patient_id'],
                        doctor_id=row['doctor_id'],
                        date=row['date'],
                        appointment_time=row['appointment_time'],
                        status=row['status'],
                        follow_up_date=row.get('follow_up_date'),
                        assistant_id=row.get('assistant_id'),
                        created_at=row.get('created_at')
                    )
                    
                    if row.get('doctor_first_name'):
                        appointment.doctor_name = f"Dr. {row['doctor_first_name']} {row['doctor_last_name']}"
                    
                    appointments.append(appointment)
                except Exception as e:
                    print(f"Error creating Appointment in get_completed_appointments: {e}")
                    continue
            
            return appointments
            
        except Exception as e:
            print(f"Error getting completed appointments: {e}")
            return []
        finally:
            cursor.close()

    def get_by_doctor_id(self, doctor_id: int, date: Optional[str] = None) -> List[Appointment]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        if date:
            cursor.execute(
                """
                SELECT id, patient_id, doctor_id, date, appointment_time, status, 
                       follow_up_date, assistant_id, create_at AS created_at
                FROM appointment
                WHERE doctor_id = %s AND date = %s
                ORDER BY appointment_time ASC
                """,
                (doctor_id, date),
            )
        else:
            cursor.execute(
                """
                SELECT id, patient_id, doctor_id, date, appointment_time, status, 
                       follow_up_date, assistant_id, create_at AS created_at
                FROM appointment
                WHERE doctor_id = %s
                ORDER BY date DESC, appointment_time DESC
                """,
                (doctor_id,),
            )
        rows = cursor.fetchall()
        cursor.close()
        
        appointments = []
        for row in rows:
            try:
                # Convert time objects to strings if needed
                if row.get('appointment_time') and hasattr(row['appointment_time'], 'strftime'):
                    row['appointment_time'] = row['appointment_time'].strftime('%H:%M')
                
                appointments.append(Appointment(**row))
            except Exception as e:
                print(f"Error creating Appointment object: {e}")
                continue
        return appointments

    def get_available_slots(self, doctor_id: int, date: str) -> List[str]:
        """Get available time slots for a doctor on a specific date."""
        try:
            #print(f"\n🔍 DEBUG get_available_slots: doctor_id={doctor_id}, date={date}")
            
            cursor = self.db.cursor(buffered=True)
            
            # 1. Get availability
            cursor.execute(
                "SELECT start_time, end_time FROM doctor_availability WHERE doctor_id = %s AND date = %s",
                (doctor_id, date),
            )
            row = cursor.fetchone()
            
            if not row:
                #print("❌ No availability found in database")
                cursor.close()
                return []
            
            start_time = row[0]
            end_time = row[1]
            #print(f"✅ Found availability: {start_time} to {end_time}")
            #print(f"   Type start_time: {type(start_time)}, end_time: {type(end_time)}")
            
            # 2. CONVERT to datetime.time objects (FIXED FOR TIMEDELTA)
            from datetime import time, timedelta
            
            # Handle start_time
            if isinstance(start_time, timedelta):
                #print(f"   Converting timedelta to time: {start_time}")
                # Convert timedelta to seconds
                total_seconds = int(start_time.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                start_time_obj = time(hours, minutes, seconds)
            elif isinstance(start_time, str):
                #print(f"   Parsing start_time string: '{start_time}'")
                # Remove microseconds if present
                start_time = start_time.split('.')[0]
                # Parse HH:MM:SS
                if start_time.count(':') == 2:
                    h, m, s = map(int, start_time.split(':'))
                    start_time_obj = time(h, m, s)
                else:
                    h, m = map(int, start_time.split(':'))
                    start_time_obj = time(h, m, 0)
            elif hasattr(start_time, 'hour'):
                #print(f"   start_time is already time object")
                start_time_obj = start_time
            else:
                #print(f"❌ Unknown start_time type: {type(start_time)}")
                cursor.close()
                return []
            
            # Handle end_time
            if isinstance(end_time, timedelta):
                #print(f"   Converting timedelta to time: {end_time}")
                # Convert timedelta to seconds
                total_seconds = int(end_time.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                end_time_obj = time(hours, minutes, seconds)
            elif isinstance(end_time, str):
                #print(f"   Parsing end_time string: '{end_time}'")
                # Remove microseconds if present
                end_time = end_time.split('.')[0]
                # Parse HH:MM:SS
                if end_time.count(':') == 2:
                    h, m, s = map(int, end_time.split(':'))
                    end_time_obj = time(h, m, s)
                else:
                    h, m = map(int, end_time.split(':'))
                    end_time_obj = time(h, m, 0)
            elif hasattr(end_time, 'hour'):
                #print(f"   end_time is already time object")
                end_time_obj = end_time
            else:
                #print(f"❌ Unknown end_time type: {type(end_time)}")
                cursor.close()
                return []
            
            #print(f"✅ Converted: {start_time_obj} to {end_time_obj}")
            
            # 3. Generate slots (SIMPLIFIED - NO DATETIME COMPLEXITY)
            slots = []
            
            # Convert to minutes since midnight
            start_minutes = start_time_obj.hour * 60 + start_time_obj.minute
            end_minutes = end_time_obj.hour * 60 + end_time_obj.minute
            
            #print(f"   Start minutes: {start_minutes}, End minutes: {end_minutes}")
            
            # Generate every 30 minutes
            current = start_minutes
            while current < end_minutes:
                hour = current // 60
                minute = current % 60
                slot = f"{hour:02d}:{minute:02d}"
                slots.append(slot)
                current += 30
            
            #print(f"✅ Generated {len(slots)} raw slots")
            
            # 4. Get booked appointments
            cursor.execute(
                """
                SELECT appointment_time FROM appointment 
                WHERE doctor_id = %s AND date = %s 
                AND status NOT IN ('CANCELLED', 'REJECTED')
                """,
                (doctor_id, date),
            )
            
            booked_times = []
            for booked_row in cursor.fetchall():
                time_val = booked_row[0]
                if time_val:
                    if hasattr(time_val, 'strftime'):
                        booked_time = time_val.strftime("%H:%M")
                    elif isinstance(time_val, timedelta):
                        # Handle timedelta for booked times too
                        total_seconds = int(time_val.total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        booked_time = f"{hours:02d}:{minutes:02d}"
                    else:
                        time_str = str(time_val)
                        if ':' in time_str:
                            booked_time = time_str[:5]
                        else:
                            booked_time = time_str
                    booked_times.append(booked_time)
            
            #print(f"📅 Booked appointments: {booked_times}")
            
            # 5. Filter out booked slots
            available_slots = []
            for slot in slots:
                if slot not in booked_times:
                    available_slots.append(slot)
            
            #print(f"🎯 Final available slots ({len(available_slots)}): {available_slots}")
            #print(f"🔚 END DEBUG\n")
            
            cursor.close()
            return available_slots
            
        except Exception as e:
            #print(f"💥 ERROR in get_available_slots: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    def cancel_appointment(self, appointment_id: int, patient_id: int) -> bool:
        cursor = self.db.cursor(buffered=True)
        try:
            cursor.execute(
                """
                UPDATE appointment SET status = 'CANCELLED' 
                WHERE id = %s AND patient_id = %s
                """,
                (appointment_id, patient_id)
            )
            self.db.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows > 0
        except Exception as e:
            self.db.rollback()
            print(f"Error cancelling appointment: {e}")
            cursor.close()
            return False
    def get_pending_appointments(self, doctor_id: int):
            """Get all pending appointments for a doctor"""
            cursor = self.db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT a.*, p.firstName, p.lastName, p.phone, p.email 
                FROM appointment a
                LEFT JOIN patient p ON a.patient_id = p.id
                WHERE a.doctor_id = %s AND a.status = 'PENDING'
                ORDER BY a.date, a.appointment_time ASC
                """,
                (doctor_id,)
            )
            appointments = cursor.fetchall()
            cursor.close()
            return appointments 
    def approve_appointment(self, appointment_id: int, doctor_id: int) -> bool:
        cursor = self.db.cursor(buffered=True)
        try:
            cursor.execute(
                """
                UPDATE appointment SET status = 'BOOKED' 
                WHERE id = %s AND doctor_id = %s AND status = 'PENDING'
                """,
                (appointment_id, doctor_id)
            )
            self.db.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows > 0
        except Exception as e:
            self.db.rollback()
            print(f"Error approving appointment: {e}")
            cursor.close()
            return False

    def reject_appointment(self, appointment_id: int, doctor_id: int) -> bool:
        cursor = self.db.cursor(buffered=True)
        try:
            cursor.execute(
                """
                UPDATE appointment SET status = 'REJECTED' 
                WHERE id = %s AND doctor_id = %s AND status = 'PENDING'
                """,
                (appointment_id, doctor_id)
            )
            self.db.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows > 0
        except Exception as e:
            self.db.rollback()
            print(f"Error rejecting appointment: {e}")
            cursor.close()
            return False

    def list_pending_by_doctor(self, doctor_id: int) -> List[Appointment]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        cursor.execute(
            """
            SELECT id, patient_id, doctor_id, date, appointment_time, status, 
                   follow_up_date, assistant_id, create_at AS created_at
            FROM appointment 
            WHERE doctor_id = %s AND status = 'PENDING' 
            ORDER BY date ASC, appointment_time ASC
            """,
            (doctor_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        
        appointments = []
        for row in rows:
            try:
                # Convert time objects to strings if needed
                if row.get('appointment_time') and hasattr(row['appointment_time'], 'strftime'):
                    row['appointment_time'] = row['appointment_time'].strftime('%H:%M')
                
                appointments.append(Appointment(**row))
            except Exception as e:
                print(f"Error creating Appointment object: {e}")
                continue
        return appointments
    

    def get_appointments_by_patient_and_doctor(self, patient_id: int, doctor_id: int) -> List[Appointment]:
        """Get appointments for a specific patient with a specific doctor."""
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                SELECT id, patient_id, doctor_id, date, appointment_time, status, 
                    follow_up_date, assistant_id, create_at AS created_at
                FROM appointment
                WHERE patient_id = %s AND doctor_id = %s
                ORDER BY date DESC, appointment_time DESC
                """,
                (patient_id, doctor_id),
            )
            rows = cursor.fetchall()
            
            appointments = []
            for row in rows:
                try:
                    # Convert time objects to strings if needed
                    if row.get('appointment_time') and hasattr(row['appointment_time'], 'strftime'):
                        row['appointment_time'] = row['appointment_time'].strftime('%H:%M')
                    
                    appointments.append(Appointment(**row))
                except Exception as e:
                    print(f"Error creating Appointment object: {e}")
                    continue
            return appointments
        except Exception as e:
            print(f"Error getting appointments by patient and doctor: {e}")
            return []
        finally:
            cursor.close()