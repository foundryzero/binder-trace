"""binder-trace loggers."""

import logging
import logging.handlers

LOG = "log"
PARSING_LOG = "parsing_log"


def configure():
    """Set up a general logger."""
    log_formatter = logging.Formatter("%(asctime)s: %(levelname)s %(message)s")
    log_handler = logging.handlers.RotatingFileHandler("binder_trace-log.txt", maxBytes=1000000, backupCount=5)
    log_handler.setFormatter(log_formatter)

    log = logging.getLogger(LOG)
    log.setLevel(logging.DEBUG)
    log.addHandler(log_handler)
    log.propagate = False

    # Set up a logger specifically for parsing errors.
    parsing_log_formatter = logging.Formatter("%(asctime)s: %(levelname)s %(message)s")
    parsing_log_handler = logging.handlers.RotatingFileHandler(
        "binder_trace-parse-log.txt", maxBytes=1000000, backupCount=5
    )
    parsing_log_handler.setFormatter(parsing_log_formatter)

    parsing_log = logging.getLogger(PARSING_LOG)
    parsing_log.setLevel(logging.INFO)
    parsing_log.addHandler(parsing_log_handler)
    parsing_log.propagate = False
