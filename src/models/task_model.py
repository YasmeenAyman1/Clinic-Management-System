from datetime import datetime
from typing import Optional

class Task:
    def __init__(self, id: int, title: str, description: Optional[str], 
                 status: str, priority: str, category: Optional[str], 
                 due_date: Optional[str], assigned_to: Optional[int], 
                 created_by: Optional[int], created_at: datetime):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.category = category
        self.due_date = due_date
        self.assigned_to = assigned_to
        self.created_by = created_by
        self.created_at = created_at
        
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"