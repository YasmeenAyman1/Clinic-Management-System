from database.db_singleton import DatabaseConnection

class BaseRepository:# instead of repeating: db = DatabaseConnection().get_connection()
    def __init__(self, connection=None):
        self.db = connection or DatabaseConnection().get_connection()

