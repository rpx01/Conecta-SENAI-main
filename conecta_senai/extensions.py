"""Instâncias compartilhadas das extensões Flask usadas pela aplicação."""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


DEFAULT_REDIS_URI = os.getenv(
    "REDIS_URL",
    f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}",
)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", DEFAULT_REDIS_URI),
)
