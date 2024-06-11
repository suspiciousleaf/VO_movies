import logging.config
import json
import atexit
from os import getenv


def setup_logging():
    with open("logs/logging_config.json", "r") as f:
        config = json.load(f)
    config["handlers"]["syslog"]["address"] = (
        getenv("PT_HOST"),
        int(getenv("PT_PORT")),
    )
    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)
