
import mysql.connector
from db_config import get_connection

try:
    connection = get_connection()

    print("MySQL connected successfully!")
    print("Database: student_attendance_db")

    connection.close()

except mysql.connector.Error as error:
    print("Database connection failed:", error)
