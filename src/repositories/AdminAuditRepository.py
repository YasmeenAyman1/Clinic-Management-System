from typing import Optional, List
from models.adminAudit_model import AdminAudit
from repositories.BaseRepository import BaseRepository

class AdminAuditRepository(BaseRepository):
    def create_entry(
        self, 
        admin_user_id: int, 
        action: str, 
        target_user_id: Optional[int] = None, 
        target_type: Optional[str] = None, 
        details: Optional[str] = None
    ):
        cursor = self.db.cursor()
        try:
            cursor.execute(
                "INSERT INTO admin_audit (admin_user_id, action, target_user_id, target_type, details) VALUES (%s, %s, %s, %s, %s)",
                (admin_user_id, action, target_user_id, target_type, details),
            )
            self.db.commit()
            new_id = cursor.lastrowid
            cursor.execute(
                "SELECT id, admin_user_id, action, target_user_id, target_type, details, create_at AS created_at FROM admin_audit WHERE id = %s", 
                (new_id,)
            )
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
        return [
            AdminAudit(
                id=r.get('id'), 
                admin_user_id=r.get('admin_user_id'), 
                action=r.get('action'), 
                target_user_id=r.get('target_user_id'), 
                target_type=r.get('target_type'), 
                details=r.get('details'), 
                created_at=r.get('created_at')
            ) for r in rows
        ] if rows else []
