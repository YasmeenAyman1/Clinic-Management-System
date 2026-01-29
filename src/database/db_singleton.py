import os
import time
import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


class DatabaseConnection:
    """Singleton MySQL connection used across the application."""

    _instance = None
    _connection = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if DatabaseConnection._initialized:
            return

        load_dotenv()

        self._config = {
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT")),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
        }

        # If running tests, avoid attempting a real DB connection
        self._testing = os.getenv('TESTING') == '1'
        
        DatabaseConnection._initialized = True
        
        # DO NOT CONNECT HERE! Let it be lazy-loaded

    def _connect_with_retry(self, max_retries=5, retry_delay=5):
        """Attempt to connect with retries"""
        for attempt in range(max_retries):
            try:
                DatabaseConnection._connection = mysql.connector.connect(**self._config)
                print(f"✅ Database connected successfully (attempt {attempt + 1}/{max_retries})")
                return True
            except Error as e:
                print(f"⚠️  Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ Failed to connect after {max_retries} attempts")
                    return False
        return False

    def get_connection(self, max_retries=5, retry_delay=5):
        """Lazy-load connection with retry logic"""
        # During tests, return None
        if self._testing:
            return None
            
        # If already connected, return connection
        if (DatabaseConnection._connection is not None and 
            DatabaseConnection._connection.is_connected()):
            return DatabaseConnection._connection
        
        # Try to connect
        if self._connect_with_retry(max_retries, retry_delay):
            return DatabaseConnection._connection
        
        # Connection failed - return None but don't crash
        print("⚠️  Database connection unavailable, but continuing...")
        return None

    def get_cursor(self, dictionary=False):
        """Get cursor, but handle connection failures gracefully"""
        conn = self.get_connection()
        if conn:
            return conn.cursor(dictionary=dictionary)
        else:
            # Return a dummy cursor or raise a more specific error
            raise RuntimeError("Database connection not available")

    def close(self):
        """Close database connection"""
        if (DatabaseConnection._connection and 
            DatabaseConnection._connection.is_connected()):
            DatabaseConnection._connection.close()
            DatabaseConnection._connection = None

    def is_connected(self):
        """Check if database is connected"""
        if self._testing:
            return True  # Assume connected for tests
        return (DatabaseConnection._connection is not None and 
                DatabaseConnection._connection.is_connected())