# import os
# from typing import Optional

# import mysql.connector
# from dotenv import load_dotenv
# from mysql.connector import Error


# class DatabaseConnection:
#     """MySQL singleton used across repositories/controllers."""

#     _instance = None

#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(DatabaseConnection, cls).__new__(cls)
#         return cls._instance

#     def __init__(self):
#         if getattr(self, "_initialized", False):
#             return

#         load_dotenv()
#         self._config = {
#             "host": os.getenv("DB_HOST", "localhost"),
#             "port": int(os.getenv("DB_PORT", "3306")),
#             "user": os.getenv("DB_USER", "root"),
#             "password": os.getenv("DB_PASSWORD", "104206My!@#-"),
#             "database": os.getenv("DB_NAME", "clinic"),
#             "auth_plugin": os.getenv("DB_AUTH_PLUGIN", "mysql_native_password"),
#             "connection_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
#         }
#         self.connection: Optional[mysql.connector.MySQLConnection] = None
#         self._connecting = False
#         self._initialized = True
#         self._connect()

#     def _connect(self):
#         """Establish connection to MySQL database."""
#         # Prevent multiple simultaneous connection attempts
#         if hasattr(self, "_connecting") and self._connecting:
#             return
#         if self.connection is not None and self.connection.is_connected():
#             return
        
#         self._connecting = True
#         try:
#             if self.connection is not None:
#                 try:
#                     self.connection.close()
#                 except:
#                     pass
#             self.connection = mysql.connector.connect(**self._config)
#             if self.connection.is_connected():
#                 print("Connected to MySQL")
#             else:
#                 print("Failed to establish MySQL connection.")
#                 self.connection = None
#         except Error as e:
#             print("ERROR connecting to MySQL:", e)
#             self.connection = None
#         finally:
#             self._connecting = False

#     def get_connection(self):
#         """Get active database connection, reconnect if needed."""
#         if self.connection is None or not self.connection.is_connected():
#             self._connect()
#         return self.connection

#     def get_cursor(self, dictionary: bool = False):
#         """Get cursor from connection."""
#         conn = self.get_connection()
#         if conn:
#             return conn.cursor(dictionary=dictionary)
#         return None

#     def close(self):
#         """Close database connection."""
#         if self.connection and self.connection.is_connected():
#             self.connection.close()
#             self.connection = None

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
