from typing import List, Optional
from models.assistant_model import Assistant
from repositories.BaseRepository import BaseRepository

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
            cursor.close()