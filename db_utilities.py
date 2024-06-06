from os import getenv
import mysql.connector

# Check of environment variables are loaded, and if not load them from .env. Also check if running locally or not, which changes the port number required.

if getenv("DB_USER") is None:

    from dotenv import load_dotenv

    load_dotenv()
    DB_PORT = 3333
else:
    DB_PORT = int(getenv("DB_PORT"))

# Read environment variables
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_HOST = getenv("DB_HOST")
DB_NAME = getenv("DB_NAME")


class DatabaseConnectionError(Exception):
    """Custom error that is raised when connecting to the database fails"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# Decorator function
def connect_to_database(original_func):
    """Decorator function to connect to the database and run the function.

    Args:
        original_func (function): Function to run on the database
    """

    def make_connection(*args, **kwargs):
        results = None
        try:
            with mysql.connector.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                use_pure=True,
            ) as db:
                with db.cursor() as cursor:
                    # kwargs for db and cursor to avoid conflicts with self
                    results = original_func(db=db, cursor=cursor, *args, **kwargs)

        except Exception as e:
            # raise DatabaseConnectionError(e)
            return e

        if results is None:
            results = ["Database connection failed"]
        return results

    return make_connection
