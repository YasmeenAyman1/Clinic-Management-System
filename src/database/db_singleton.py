import os
from typing import Optional

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


class DatabaseConnection:
    """MySQL singleton used across repositories/controllers."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        load_dotenv()
        self._config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),  # prefer env; default blank
            "database": os.getenv("DB_NAME", "clinic"),
            "auth_plugin": os.getenv("DB_AUTH_PLUGIN", "mysql_native_password"),
        }
        self.connection: Optional[mysql.connector.MySQLConnection] = None
        self._initialized = True
        self._connect()

    def _connect(self):
        try:
            self.connection = mysql.connector.connect(**self._config)
            if self.connection.is_connected():
                print("Connected to MySQL")
            else:
                print("Failed to establish MySQL connection.")
                self.connection = None
        except Error as e:
            print("ERROR connecting to MySQL:", e)
            self.connection = None

    def get_connection(self):
        if self.connection is None or not self.connection.is_connected():
            self._connect()
        return self.connection

    def get_cursor(self, dictionary: bool = False):
        conn = self.get_connection()
        if conn:
            return conn.cursor(dictionary=dictionary)
        return None

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
