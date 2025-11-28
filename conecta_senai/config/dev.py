"""Configurações específicas do ambiente de desenvolvimento."""
import logging

from .base import BaseConfig


class DevConfig(BaseConfig):
    """Aplicação configurada para desenvolvimento local."""

    DEBUG = True
    LOG_LEVEL = logging.DEBUG
