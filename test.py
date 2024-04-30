import hashlib


# Hash function to create a single data point for each showing that can be compared with newly scraped showings, to identify showings not yet in the database
def calculate_hash(movie_id, cinema_id, start_time):
    # Create a single string
    data = f"{movie_id}{cinema_id}{start_time}"
    print(data)
    # Calculate the SHA-256 hash
    hash_value = hashlib.sha256(data.encode()).hexdigest()

    return hash_value


print(calculate_hash("TW92aWU6MjY5MTIy", "P8110", "2024-05-01 18:30:00"))
# ddbbc9ba948d1e9c37b611314117efa48ef0be3408fd5a8dd165445a9e630063
# ddbbc9ba948d1e9c37b611314117efa48ef0be3408fd5a8dd165445a9e630063
