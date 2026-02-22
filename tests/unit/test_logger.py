import logging

import pytest

from src.utils.logger import setup_logger


pytestmark = [pytest.mark.unit]


def test_setup_logger_creates_stream_handler_once():
    logger = setup_logger("test_logger_once", level=logging.DEBUG)
    initial_handler_count = len(logger.handlers)

    logger_again = setup_logger("test_logger_once", level=logging.INFO)

    assert logger is logger_again
    assert len(logger_again.handlers) == initial_handler_count


def test_setup_logger_sets_requested_level():
    logger = setup_logger("test_logger_level", level=logging.WARNING)
    assert logger.level == logging.WARNING
