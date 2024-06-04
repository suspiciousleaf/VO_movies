import time
from logging import getLogger

from scraper import ScraperManager
from logs.setup_logger import setup_logging


if __name__ == "__main__":
    try:
        t0 = time.perf_counter()

        logger = getLogger(__name__)
        setup_logging()

        start = 10
        end = 15

        try:
            scraper_man = ScraperManager(
                start=start,
                end=end,
                save_raw_json_data=False,
                logger=logger,
            )
            logger.info(
                f"Time taken: {time.perf_counter() - t0:.2f}s, days = {start}-{end}"
            )
        except Exception as e:
            logger.exception(e)

    except:
        pass
