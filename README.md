# V.O.Flix
## Lost in Translation? Not with V.O.Flix !
V.O.Flix is your one stop shop to find English language cinema showings of movies in the south of France, that are not dubbed into French. 

<br>
<!-- TABLE OF CONTENTS -->
  <summary><h3 style="display: inline-block">Table of Contents</h2></summary>
  <details open="open">
  <ol>
    <li>
      <a href="#about-the-project">About the project</a>
    </li>
    <li>
      <a href="#details">Details</a>
    </li>
    <li>
      <a href="#installation-and-setup-instructions">Installation and setup instructions</a>
    </li>
    <li><a href="#license">License</a></li>
  </ol>
</details>
<br>

## About the project

### Webscraper and REST API that finds showings of movies in cinemas shown in their original language with subtitles (filtered for English language) in an area of the south of France. Consumed by the front end [here](https://www.voflix.org).

This project was built because I like going to the movies, and I don't like watching everything dubbed into French. 
<br><br>

## Details:
* Deployed using [Docker compose](https://docs.docker.com/compose/)
* [FastAPI](https://fastapi.tiangolo.com/) is used for the API, and has endpoints to check if the service is running, initiate the scraper (if not using CRON job), and `routers` for more detailed functionality.
* `Cinema router` allows cinemas included by the scraper to be retrieved, added, and deleted. Cinemas to be added are validated using [Pydantic](https://docs.pydantic.dev/latest/).
* `Search router` allows showings to be retrieved with optional csv location filter.
* `Database router` allows the database connection to be tested, and can create and populate tables for a new deployment.
* Webscraping is done synchronously using [requests](https://pypi.org/project/requests/) as it uses [ScrapingAnt](https://scrapingant.com/)'s free tier, which does not permit concurrency. 
* Each new movie and showing is validated using [Pydantic](https://docs.pydantic.dev/latest/) before being inserted into the database. Additional movie details are retrieved from [The Movie Database API](https://www.themoviedb.org/).
* The date range for scraping can be selected, with the option to save the raw data, or to load raw data from a json file for testing.
* `MySQL` is used for the database, with [mysql-connector](https://www.mysql.com/products/connector/) and SQL syntax for queries.
<br><br>

## Installation and setup instructions:

You'll need to:
* Install [Docker](https://docs.docker.com/get-docker/) and [docker compose](https://docs.docker.com/compose/install/linux/)
* Obtain a [ScrapingAnt API key](https://app.scrapingant.com/signup)
* Obtain a [TMDB API key](https://developer.themoviedb.org/v4/reference/intro/getting-started)
* Get a base prefix URL for scraping, send me a message for this
* Creat a `.env` file with these variables added, along with port numbers

To build the API image, pull the MySQL image, and start up the two containers, run:

`docker compose up --build`

The API can be accessed through the browser on `localhost` port 8000. You'll need to run the scraper in order to populate the database with movies and showing data. 

To run on a VPS, in `docker-compose.yaml` in voflix service info, update the "ports" from

`127.0.0.1:8000:8000` to `80:8000`
<br><br>

## License
MIT © [suspiciousleaf](https://github.com/suspiciousleaf)