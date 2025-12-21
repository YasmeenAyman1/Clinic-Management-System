from typing import List, Optional
from models.user_model import User
from repositories.BaseRepository import BaseRepository

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
            "SELECT id, username, password, role, status, update_at AS updated_at, create_at AS created_at FROM `user` WHERE username = %s",
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
    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        cursor = self.db.cursor()
        try:
            cursor.execute(
                "UPDATE user SET password = %s WHERE id = %s",
                (new_password_hash, user_id)
            )
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error updating password: {e}")
            return False
        finally:
            cursor.close()