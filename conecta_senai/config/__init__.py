"""Módulo de configuração centralizado da aplicação Conecta SENAI."""
from .base import BaseConfig, env_bool, strtobool
from .dev import DevConfig
from .prod import ProdConfig
from .test import TestConfig

__all__ = [
    "BaseConfig",
    "DevConfig",
    "ProdConfig",
    "TestConfig",
    "env_bool",
    "strtobool",
]
