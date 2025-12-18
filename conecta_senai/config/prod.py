import logging

from .base import BaseConfig


class ProdConfig(BaseConfig):
    LOG_LEVEL = logging.INFO
