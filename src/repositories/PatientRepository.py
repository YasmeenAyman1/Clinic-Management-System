from typing import List, Optional
from models.patient_model import Patient
from repositories.BaseRepository import BaseRepository

#--------------------------------->>>PatientRepository<<<--------------------------------- 
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
        cursor = None
        try:
            print(f"DEBUG create_patient: firstName={first_name}, lastName={last_name}, gender={gender}, birth_date={birth_date}, phone={phone}, address={address}, user_id={user_id}")
            
            # Clean phone number - ensure it has + prefix
            phone_clean = phone.strip()
            if phone_clean and not phone_clean.startswith('+'):
                # Check if it starts with country code
                if phone_clean.startswith('20') and len(phone_clean) >= 11:
                    phone_clean = f"+{phone_clean}"
                else:
                    # Assume it's a local number, add +20 for Egypt
                    digits = ''.join(filter(str.isdigit, phone_clean))
                    if len(digits) == 10:
                        phone_clean = f"+20{digits}"
                    elif digits:
                        phone_clean = f"+{digits}"
            
            print(f"DEBUG: Using phone: {phone_clean}")
            
            cursor = self.db.cursor(buffered=True)
            cursor.execute(
                """
                INSERT INTO patient (firstName, lastName, gender, phone, birth_date, address, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (first_name, last_name, gender, phone_clean, birth_date, address, user_id),
            )
            self.db.commit()
            
            patient_id = cursor.lastrowid
            print(f"DEBUG: Patient inserted with ID: {patient_id}")
            
            cursor.close()
            cursor = None
            
            # Get the created patient
            created_patient = self.get_by_id(patient_id)
            if created_patient:
                print(f"DEBUG: Successfully retrieved patient {patient_id}")
            else:
                print(f"DEBUG: Could not retrieve patient {patient_id} after creation")
            
            return created_patient
            
        except Exception as e:
            print(f"ERROR in create_patient: {type(e).__name__}: {e}")
            import mysql.connector
            if isinstance(e, mysql.connector.Error):
                print(f"MySQL Error {e.errno}: {e.msg}")
                print(f"SQL State: {e.sqlstate}")
            # Re-raise the exception so the calling code can handle it
            raise e
        finally:
            if cursor is not None:
                cursor.close()
    
    def search_patients(self, search_term: str) -> List[Patient]:
        """
        Search patients by name, phone, or ID
        
        Args:
            search_term: Search term to look for
        
        Returns:
            List of Patient objects matching the search
        """
        cursor = None
        try:
            cursor = self.db.cursor(dictionary=True, buffered=True)
            
            search_pattern = f"%{search_term}%"
            
            query = """
                SELECT DISTINCT
                    id,
                    firstName,
                    lastName,
                    gender,
                    phone,
                    birth_date,
                    address,
                    user_id,
                    create_at AS created_at
                FROM patient
                WHERE
                    CAST(id AS CHAR) LIKE %s
                    OR phone LIKE %s
                    OR firstName LIKE %s
                    OR lastName LIKE %s
                    OR CONCAT(firstName, ' ', lastName) LIKE %s
                    OR CONCAT(lastName, ' ', firstName) LIKE %s
                ORDER BY firstName, lastName
            """
            
            cursor.execute(query, (
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
            ))
            
            rows = cursor.fetchall()
            cursor.close()
            cursor = None
            
            patients = []
            for row in rows:
                try:
                    # Create patient
                    patient = Patient(**row)
                    # Calculate age
                    patient.age = self.calculate_age_from_birthdate(patient.birth_date)
                    patients.append(patient)
                except Exception as e:
                    print(f"Error creating Patient object from row: {e}")
                    continue
            
            return patients
            
        except Exception as e:
            print(f"Error searching patients: {e}")
            return []
        finally:
            if cursor is not None:
                cursor.close()
    
    def get_by_id(self, patient_id: int) -> Optional[Patient]:
        cursor = None
        try:
            cursor = self.db.cursor(dictionary=True, buffered=True)
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
            cursor = None
            
            if row:
                try:
                    patient = Patient(**row)
                    # Calculate age
                    patient.age = self.calculate_age_from_birthdate(patient.birth_date)
                    return patient
                except Exception as e:
                    print(f"Error creating Patient object in get_by_id: {e}")
                    print(f"Row data: {row}")
                    return None
            return None
        finally:
            if cursor is not None:
                cursor.close()

    def get_by_user_id(self, user_id: int) -> Optional[Patient]:
        cursor = None
        try:
            cursor = self.db.cursor(dictionary=True, buffered=True)
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
            cursor = None
            
            if row:
                try:
                    patient = Patient(**row)
                    # Calculate age
                    patient.age = self.calculate_age_from_birthdate(patient.birth_date)
                    return patient
                except Exception as e:
                    print(f"Error creating Patient object in get_by_user_id: {e}")
                    return None
            return None
        finally:
            if cursor is not None:
                cursor.close()

    def update_patient(self, patient_id: int, first_name: str, last_name: str, gender: str, phone: str, birth_date: str, address: str) -> bool:
        cursor = None
        try:
            cursor = self.db.cursor(buffered=True)
            cursor.execute(
                "UPDATE patient SET firstName = %s, lastName = %s, gender = %s, phone = %s, birth_date = %s, address = %s WHERE id = %s",
                (first_name, last_name, gender, phone, birth_date, address, patient_id)
            )
            self.db.commit()
            cursor.close()
            cursor = None
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error updating patient: {e}")
            return False
        finally:
            if cursor is not None:
                cursor.close()
            
    def get_all_patients(self) -> List[Patient]:
        cursor = None
        try:
            cursor = self.db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT 
                    id, 
                    firstName, 
                    lastName, 
                    gender, 
                    phone, 
                    birth_date, 
                    address, 
                    user_id, 
                    create_at AS created_at
                FROM patient
                ORDER BY create_at DESC
                """
            )
            rows = cursor.fetchall()
            cursor.close()
            cursor = None
            
            patients = []
            for row in rows:
                try:
                    patient = Patient(**row)
                    # Calculate age
                    patient.age = self.calculate_age_from_birthdate(patient.birth_date)
                    patients.append(patient)
                except Exception as e:
                    print(f"Error creating Patient object: {e}")
                    continue
            return patients
        except Exception as e:
            print(f"Error getting all patients: {e}")
            return []
        finally:
            if cursor is not None:
                cursor.close()
        
    def get_new_patients_this_month(self) -> int:
        """
        Get count of new patients registered in the current month
        
        Returns:
            Number of new patients this month
        """
        cursor = None
        try:
            cursor = self.db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT COUNT(*) as count 
                FROM patient 
                WHERE MONTH(create_at) = MONTH(CURRENT_DATE()) 
                AND YEAR(create_at) = YEAR(CURRENT_DATE())
                """
            )
            result = cursor.fetchone()
            cursor.close()
            cursor = None
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error getting new patients this month: {e}")
            return 0
        finally:
            if cursor is not None:
                cursor.close()
    
    def get_patient_records_count(self, patient_id: int) -> int:
        """
        Get count of medical records for a patient
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Number of medical records
        """
        cursor = None
        try:
            cursor = self.db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT COUNT(*) as count 
                FROM medical_record 
                WHERE patient_id = %s
                """,
                (patient_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            cursor = None
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error getting patient records count: {e}")
            return 0
        finally:
            if cursor is not None:
                cursor.close()
    
    def get_last_visit(self, patient_id: int):
        """
        Get last visit date for a patient
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Last visit date or None
        """
        cursor = None
        try:
            cursor = self.db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT MAX(appointment_date) as last_visit
                FROM appointment 
                WHERE patient_id = %s AND status = 'completed'
                """,
                (patient_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            cursor = None
            return result['last_visit'] if result and result['last_visit'] else None
        except Exception as e:
            print(f"Error getting last visit: {e}")
            return None
        finally:
            if cursor is not None:
                cursor.close()
        
    def calculate_age_from_birthdate(self, birth_date):
        """Calculate age from birth date in Python."""
        if not birth_date:
            return None
        
        try:
            from datetime import datetime
            
            if isinstance(birth_date, str):
                # Convert string to date
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            elif isinstance(birth_date, datetime):
                birth_date = birth_date.date()
            
            today = datetime.today().date()
            age = today.year - birth_date.year
            
            # Adjust if birthday hasn't occurred this year
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1
                
            return age
        except Exception:
            return None