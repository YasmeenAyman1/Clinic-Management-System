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
            
            cursor = self.db.cursor()
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
    
    def search_patients(self, search_term: str) -> List[Patient]:
        """
        Search patients by name, phone, or ID
        
        Args:
            search_term: Search term to look for
        
        Returns:
            List of Patient objects matching the search
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            
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
            
            patients = []
            for row in rows:
                try:
                    # Convert row keys to match Patient model parameter names
                    patient_data = {
                        'id': row['id'],
                        'firstName': row['firstName'],
                        'lastName': row['lastName'],
                        'gender': row['gender'],
                        'phone': row['phone'],
                        'birth_date': row['birth_date'],
                        'address': row['address'],
                        'user_id': row['user_id'],
                        'created_at': row['created_at']
                    }
                    patients.append(Patient(**patient_data))
                except Exception as e:
                    print(f"Error creating Patient object from row: {e}")
                    continue
            
            return patients
            
        except Exception as e:
            print(f"Error searching patients: {e}")
            return []
        
    def get_by_id(self, patient_id: int) -> Optional[Patient]:
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
        
        if row:
            try:
                # The SQL query order MUST match Patient model constructor parameter order
                return Patient(**row)
            except Exception as e:
                print(f"Error creating Patient object in get_by_id: {e}")
                print(f"Row data: {row}")
                return None
        return None

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
        
        if row:
            try:
                return Patient(**row)
            except Exception as e:
                print(f"Error creating Patient object in get_by_user_id: {e}")
                return None
        return None

    def update_patient(self, patient_id: int, first_name: str, last_name: str, phone: str, birth_date: str, address: str) -> bool:
        cursor = self.db.cursor()
        try:
            cursor.execute(
                "UPDATE patient SET firstName = %s, lastName = %s, phone = %s, birth_date = %s, address = %s WHERE id = %s",
                (first_name, last_name, phone, birth_date, address, patient_id)
            )
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error updating patient: {e}")
            return False
        finally:
            cursor.close()
            
    def get_all_patients(self) -> List[Patient]:
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, firstName, lastName, gender, phone, birth_date, address, user_id, create_at AS created_at
                FROM patient
                ORDER BY create_at DESC
                """
            )
            rows = cursor.fetchall()
            cursor.close()
            
            patients = []
            for row in rows:
                try:
                    patients.append(Patient(**row))
                except Exception as e:
                    print(f"Error creating Patient object: {e}")
                    continue
            return patients
        except Exception as e:
            print(f"Error getting all patients: {e}")
            return []
        
    def get_new_patients_this_month(self) -> int:
        """
        Get count of new patients registered in the current month
        
        Returns:
            Number of new patients this month
        """
        try:
            cursor = self.db.cursor(dictionary=True)
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
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error getting new patients this month: {e}")
            return 0
    
    # ADD THESE MISSING METHODS:
    
    def get_patient_records_count(self, patient_id: int) -> int:
        """
        Get count of medical records for a patient
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Number of medical records
        """
        try:
            # You need to import MedicalRecordRepository or use direct SQL
            cursor = self.db.cursor(dictionary=True)
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
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error getting patient records count: {e}")
            return 0
    
    def get_last_visit(self, patient_id: int):
        """
        Get last visit date for a patient
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Last visit date or None
        """
        try:
            cursor = self.db.cursor(dictionary=True)
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
            return result['last_visit'] if result and result['last_visit'] else None
        except Exception as e:
            print(f"Error getting last visit: {e}")
            return None