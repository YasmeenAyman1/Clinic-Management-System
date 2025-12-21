from typing import Optional
from models.contact_model import Contact
from repositories.BaseRepository import BaseRepository

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
            self.db.commit()  # confirm changes
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