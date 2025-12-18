import os
import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


class DatabaseConnection:
    """Singleton MySQL connection used across the application."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        load_dotenv()

        self._config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD","104206My!@#-"),
            "database": os.getenv("DB_NAME", "clinic"),
        }

        # If running tests, avoid attempting a real DB connection; allow tests to mock repositories
        if os.getenv('TESTING') == '1':
            self.connection = None
            self._initialized = True
            self._testing = True
            return

        self.connection = None
        self._initialized = True
        self._connect()

    def _connect(self):#Avoid reconnecting if already connected
        try:
            self.connection = mysql.connector.connect(**self._config)
        except Error as e:
            raise RuntimeError(f"Database connection failed: {e}")

    def get_connection(self):
        # During tests, we avoid establishing a real DB connection
        if getattr(self, '_testing', False):
            return None
        if not self.connection or not self.connection.is_connected():
            self._connect()
        return self.connection

    def get_cursor(self, dictionary=False):#Useful for Flask templates.
        return self.get_connection().cursor(dictionary=dictionary)

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
