import logging
import os
from logging import handlers
from config import LOG_DIR, LOG_SIZE, LOG_DATEFMT, LOG_LEVEL, LOG_FORMAT, BACKUP_COUNT


def custom_log(fname):
    """Create a custom logger. Provide an absolute path for a file name, e.g. using __file__"""

    global LOG_DIR, LOG_SIZE, LOG_DATEFMT, LOG_LEVEL, LOG_FORMAT, BACKUP_COUNT

    lg = logging.getLogger(os.path.basename(fname))
    lg.setLevel(getattr(logging, LOG_LEVEL))

    LOG_SIZE *= 1000000  # convert megabytes to bytes

    if not os.path.exists(LOG_DIR):
        os.mkdir(LOG_DIR)
    log_file_name = f"{LOG_DIR}/{os.path.basename(fname)}.log"

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = handlers.RotatingFileHandler(filename=log_file_name, maxBytes=LOG_SIZE, backupCount=BACKUP_COUNT)

    # Create formatters and add it to handlers
    c_format = logging.Formatter(LOG_FORMAT, LOG_DATEFMT)
    f_format = logging.Formatter(LOG_FORMAT, LOG_DATEFMT)
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    lg.addHandler(c_handler)
    lg.addHandler(f_handler)

    return lg


if __name__ == "__main__":
    log = custom_log(__file__)
    log.info("The logger does work!")
