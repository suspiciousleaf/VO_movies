from pprint import pprint

from db_utilities import connect_to_database


@connect_to_database
def search_showings(db, cursor, towns=[]):
    cursor = db.cursor(dictionary=True)
    columns_required = "start_time, original_title, french_title, image_poster, runtime, synopsis, cast, languages, genres, release_date, name, town"
    search_query = f"SELECT {columns_required} FROM showtimes LEFT JOIN movies ON showtimes.movie_id = movies.movie_id LEFT JOIN cinemas ON showtimes.cinema_id = cinemas.cinema_id WHERE start_time > DATE(NOW())"

    if towns:
        placeholders = ", ".join(f"%s" for _ in towns)
        search_query += f" AND town IN ({placeholders})"

    print("\n", search_query, "\n")

    cursor.execute(search_query, towns)
    results = cursor.fetchall()
    return results


results = search_showings(towns=["Lavelanet", "Quillan", "Carcassonne"])
print(len(results))
