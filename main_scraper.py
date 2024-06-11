import time
import datetime
from logging import getLogger

from scraper import ScraperManager
from logs.setup_logger import setup_logging


if __name__ == "__main__":
    try:
        t0 = time.perf_counter()

        logger = getLogger(__name__)
        setup_logging()

        start = 11
        end = 15

        # Calculate the dates
        today = datetime.date.today()
        start_date = today + datetime.timedelta(days=start)
        end_date = today + datetime.timedelta(days=end)

        # Format the dates
        start_date_str = start_date.strftime("%d-%m-%Y")
        end_date_str = end_date.strftime("%d-%m-%Y")

        try:
            scraper_man = ScraperManager(
                start_day=start,
                end_day=end,
                logger=logger,
            )
            logger.info(
                f"Ran scraper. Time taken: {time.perf_counter() - t0:.2f}s, dates: {start_date_str} - {end_date_str}"
            )
        except Exception as e:
            logger.exception(e)

    except:
        pass
