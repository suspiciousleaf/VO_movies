from os import getenv

from dotenv import load_dotenv
import mysql.connector

# take environment variables from .env.
load_dotenv()

# Read environment variables
DB_USER = getenv("db_user")
DB_PASSWORD = getenv("db_password")
DB_HOST = getenv("db_host")
DB_PORT = int(getenv("db_port"))
DB_NAME = getenv("db_name")


class DatabaseConnectionError(Exception):
    """Custom error that is raised when connecting to the database fails"""

    def __init__(self, value: str, message: str):
        self.value = value
        self.message = message
        super().__init__(message)


# Decorator function
def connect_to_database(original_func):
    """Decorator function to connect to the database, run the function, and then close the connection

    Args:
        original_func (function): Function to run on the database
    """

    def make_connection(*args, **kwargs):
        results = None
        try:
            db = mysql.connector.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                use_pure=True,
            )
            cursor = db.cursor()
            # kwargs for db and cursor to avoid conflicts with self
            results = original_func(db=db, cursor=cursor, *args, **kwargs)

        except Exception as e:
            raise DatabaseConnectionError(e)

        finally:
            if "cursor" in locals() and cursor:
                cursor.close()
            if "db" in locals() and db:
                db.close()
            return results

    return make_connection
