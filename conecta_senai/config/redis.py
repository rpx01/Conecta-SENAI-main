"""Inicializa a conexão com o Redis usada pela aplicação."""

import os
from redis import Redis


class DummyRedis:
    """Implementação simplificada usada durante testes quando o Redis não está disponível."""

    def ping(self):
        return True

    def setex(self, *args, **kwargs):
        return True

    def get(self, *args, **kwargs):
        return None


def init_redis(app=None):
    """Cria o cliente Redis e o registra opcionalmente no app."""
    url = (
        app.config.get("REDIS_URL")
        if app is not None
        else os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )

    if os.getenv("DISABLE_REDIS") == "1":
        client = DummyRedis()
    else:
        try:
            client = Redis.from_url(url)
            client.ping()
        except Exception as e:  # pragma: no cover - fallback quando redis indisponível
            if app is not None:
                app.logger.warning("Redis indisponível: %s", str(e))
            client = DummyRedis()

    if app is not None:
        app.redis_conn = client
    global redis_conn
    redis_conn = client
    return client


redis_conn = DummyRedis()

