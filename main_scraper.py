import time
from logging import getLogger

from scraper import ScraperManager
from logs.setup_logger import setup_logging


if __name__ == "__main__":
    t0 = time.perf_counter()

    logger = getLogger(__name__)
    setup_logging()
    # logger.setLevel("DEBUG")

    try:
        scraper_man = ScraperManager(
            1,
            14,
            save_raw_json_data=False,
            local_data_filename="raw_data_2024-05-12_16-57-25.json",
            logger=logger,
        )
    except Exception as e:
        logger.exception(e)

    print(f"Time taken: {time.perf_counter() - t0:.2f}s")
