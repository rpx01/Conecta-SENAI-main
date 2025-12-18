import logging

from .base import BaseConfig


class DevConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
