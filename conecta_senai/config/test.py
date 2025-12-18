import logging

from .base import BaseConfig


class TestConfig(BaseConfig):
    TESTING = True
    LOG_LEVEL = logging.WARNING
