import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        """
        Intercept a logging record from Python's built-in logging module and
        process it into Loguru's logging API.

        :param record: The logging record to process
        :type record: logging.LogRecord
        """
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(level, record.getMessage())


def safe_format(record):
    """
    Ensures the 'extra' dictionary in a logging record contains a 'name' key.

    If the 'name' key is not present in the 'extra' dictionary of the given logging
    record, it assigns the value of the record's 'name' attribute to it.
    This function  helps in maintaining consistency when formatting
    log records by ensuring that
    the 'extra' dictionary always contains a 'name' key.

    :param record: The logging record to process, containing an 'extra' dictionary.
    :type record: dict
    :return: The modified logging record with the 'extra' dictionary containing
    a 'name' key.
    :rtype: dict
    """

    extra = record["extra"]
    if "name" not in extra:
        extra["name"] = record["name"]
    return record


def setup_logging():
    """
    Setup Loguru logging to intercept Python's built-in logging module.

    This function adds a handler to Loguru to process logging records from
    Python's built-in logging module.
    """
    logger.remove()
    logger.add(
        sys.stdout,
        format="[<green>{time:YYYY-MM-DD HH:mm:ss}</green>] "
        "[<level>{level}</level>] "
        "[<cyan>{extra[name]!r}</cyan>] "
        "[<yellow>{module}:{function}:{line}</yellow>] "
        "{message}",
        level="INFO",
        backtrace=True,
        diagnose=True,
        filter=safe_format,
    )

    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.DEBUG)
    for name in ["fastapi-blueprint-generator"]:
        logging.getLogger(name).handlers = [InterceptHandler()]
        logging.getLogger(name).propagate = False
        logging.getLogger(name).setLevel(logging.DEBUG)
