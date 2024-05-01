from db_utilities import connect_to_database

TABLE_NAME = "cinemas"


class CinemaManager:
    def __init__(self):
        self.cinemas = self.retrieve_cinemas()

    @staticmethod
    @connect_to_database
    def retrieve_cinemas(db, cursor) -> list[str]:
        """Retrieve cinema_id values for all cinemas in database"""
        try:
            query = f"SELECT cinema_id FROM {TABLE_NAME};"
            cursor.execute(query)
            results = cursor.fetchall()

            return [result[0] for result in results]

        except Exception as e:
            print(f"ShowingsManager.retrieve_showings: An error occurred: {str(e)}")
