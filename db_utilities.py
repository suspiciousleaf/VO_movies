import mysql.connector

from creds import DB_PORT, DB_USER, DB_PASSWORD, DB_HOST, DB_NAME

# Check of environment variables are loaded, and if not load them from .env. Also check if running locally or not, which changes some of the information.


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
                    # kwargs for db and cursor to avoid conflicts with 'self'
                    results = original_func(db=db, cursor=cursor, *args, **kwargs)

        except mysql.connector.Error as e:
            raise DatabaseConnectionError(f"Database connection error: {e}")

        except Exception as e:
            raise DatabaseConnectionError(f"An unexpected error occurred: {e}")

        if results is None:
            results = ["Database connection failed"]
        return results

    return make_connection


@connect_to_database
def test_db_connection(db, cursor, logger):
    """Test the connection to the database and verify the active database."""
    try:
        query = "SELECT DATABASE();"
        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            current_db = results[0][0]
            if DB_NAME == current_db:
                logger.info("Database connection successful")
                return "Database connection successful"
            else:
                logger.warning(
                    f"Database connection validation failed, expected: {DB_NAME}, got: {current_db}"
                )
                return f"Database connection validation failed, expected: {DB_NAME}, got: {current_db}"

        else:
            logger.error("No results returned from database query")
            return "No results returned from database query"

    except Exception as e:
        logger.error(f"Exception during database connection test: {e}", exc_info=True)
        return f"Exception during database connection test: {e}"
