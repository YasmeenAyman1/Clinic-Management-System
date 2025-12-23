from typing import List, Optional
from models.task_model import Task
from repositories.BaseRepository import BaseRepository

class TaskRepository(BaseRepository):
    def get_by_id(self, task_id: int) -> Optional[Task]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute("""
                SELECT id, title, description, status, priority, category, 
                       due_date, assigned_to, created_by, created_at
                FROM tasks 
                WHERE id = %s
            """, (task_id,))
            row = cursor.fetchone()
            return Task(**row) if row else None
        finally:
            cursor.close()

    def get_assistant_tasks(self, assistant_id: int) -> List[Task]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute("""
                SELECT id, title, description, status, priority, category, 
                       due_date, assigned_to, created_by, created_at
                FROM tasks 
                WHERE assigned_to = %s 
                OR (assigned_to IS NULL AND created_by IN (
                    SELECT user_id FROM assistant WHERE id = %s
                ))
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                        ELSE 4 
                    END,
                    CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
                    due_date ASC
            """, (assistant_id, assistant_id))
            rows = cursor.fetchall()
            return [Task(**row) for row in rows] if rows else []
        finally:
            cursor.close()

    def create_task(self, title: str, description: Optional[str] = None, 
                   priority: str = 'medium', category: Optional[str] = None,
                   due_date: Optional[str] = None, status: str = 'pending',
                   assigned_to: Optional[int] = None, created_by: Optional[int] = None) -> Optional[Task]:
        cursor = self.db.cursor(buffered=True)
        try:
            cursor.execute("""
                INSERT INTO tasks 
                (title, description, priority, category, due_date, status, assigned_to, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, description, priority, category, due_date, status, assigned_to, created_by))
            self.db.commit()
            return self.get_by_id(cursor.lastrowid)
        except Exception as e:
            self.db.rollback()
            print(f"Error creating task: {e}")
            return None
        finally:
            cursor.close()

    def update_task(self, task_id: int, **kwargs) -> bool:
        cursor = self.db.cursor(buffered=True)
        try:
            allowed_fields = ['title', 'description', 'status', 'priority', 
                            'category', 'due_date', 'assigned_to']
            updates = []
            params = []
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    updates.append(f"{field} = %s")
                    params.append(value)
            
            if not updates:
                return False
                
            params.append(task_id)
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s"
            
            cursor.execute(query, tuple(params))
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            print(f"Error updating task: {e}")
            return False
        finally:
            cursor.close()

    def delete_task(self, task_id: int) -> bool:
        cursor = self.db.cursor(buffered=True)
        try:
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting task {task_id}: {e}")
            return False
        finally:
            cursor.close()

    def mark_task_complete(self, task_id: int) -> bool:
        return self.update_task(task_id, status='completed')

    def get_tasks_by_status(self, assistant_id: int, status: str) -> List[Task]:
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute("""
                SELECT id, title, description, status, priority, category, 
                       due_date, assigned_to, created_by, created_at
                FROM tasks 
                WHERE (assigned_to = %s OR (assigned_to IS NULL AND created_by IN (
                    SELECT user_id FROM assistant WHERE id = %s
                )))
                AND status = %s
                ORDER BY created_at DESC
            """, (assistant_id, assistant_id, status))
            rows = cursor.fetchall()
            return [Task(**row) for row in rows] if rows else []
        finally:
            cursor.close()