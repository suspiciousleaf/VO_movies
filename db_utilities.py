import mysql.connector
from creds import *


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
                user=db_user,
                password=db_password,
                host=db_host,
                port=3333,
                database=database,
                use_pure=True,
            )
            cursor = db.cursor()
            results = original_func(db, cursor, *args, **kwargs)

        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            if "cursor" in locals() and cursor:
                cursor.close()
            if "db" in locals() and db:
                db.close()
            return results

    return make_connection


@connect_to_database
def retrieve_showings(db, cursor):
    try:
        cursor = db.cursor(dictionary=True)

        table_name = "showtimes"

        query = f"SELECT movie_id, cinema_id, start_time FROM {table_name};"

        cursor.execute(query)

        results = cursor.fetchall()

        return results

    except Exception as e:
        print(f"An error occurred: {str(e)}")


cinemas = retrieve_showings()
print(cinemas[1])
