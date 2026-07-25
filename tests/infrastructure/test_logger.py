import logging

from sentinel.infrastructure.logger import Logger


def test_logger_creation() -> None:
    logger = Logger()
    assert isinstance(logger.instance, logging.Logger)


def test_logger_name() -> None:
    logger = Logger()
    assert logger.instance.name == "sentinel"


def test_logger_methods() -> None:
    logger = Logger().instance

    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")