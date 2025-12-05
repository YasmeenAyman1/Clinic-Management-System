# import mysql.connector
# from mysql.connector import Error

# class DatabaseConnection:
#     _instance = None
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(DatabaseConnection, cls).__new__(cls)
#             return cls._instance
#     def __init__(self):
#         if not hasattr(self, "connection") or self.connection is None:
#             try:
#                 self.connection = mysql.connector.connect(
#                 host="localhost",
#                 user="root",
#                 password="104206My!@#-", # Change if you set a password
#                 database="clinic"
#                 )
#                 print(" Connected to MySQL")
#             except Error as e:
#                 print(" ERROR connecting to MySQL:", e)
#                 self.connection = None

#     def get_connection(self):
#         return self.connection

# test_db = DatabaseConnection()




# import mysql.connector

# conn = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="104206My!@#-", # your MySQL root password
#     database="clinic"
#     )

# print(conn.is_connected()) # Should print True