"""Classes e utilidades centrais de configuração da aplicação."""
import logging
import os




def strtobool(val: str) -> int:
    """Converte uma string de booleano em ``1`` ou ``0``.

    Args:
        val: Valor textual a ser interpretado.

    Returns:
        ``1`` para valores verdadeiros e ``0`` para valores falsos.

    Raises:
        ValueError: Se ``val`` não representa um booleano conhecido.
    """

    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    if val in ("n", "no", "f", "false", "off", "0"):
        return 0
    raise ValueError(f"invalid truth value {val}")


def env_bool(name: str, default: bool = False) -> bool:
    """Lê uma variável de ambiente como booleano.

    Args:
        name: Nome da variável de ambiente.
        default: Valor padrão caso a variável não exista ou seja inválida.

    Returns:
        ``True`` ou ``False`` conforme o conteúdo da variável.
    """

    v = os.getenv(name, str(default))
    try:
        return bool(strtobool(str(v)))
    except Exception:
        return bool(default)


class BaseConfig:
    """Configuração base compartilhada entre todos os ambientes."""

    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = logging.INFO

    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM = os.getenv("RESEND_FROM", "no-reply@example.com")
    RESEND_REPLY_TO = os.getenv("RESEND_REPLY_TO")

    SECURITY_PASSWORD_SALT = os.environ.get(
        "SECURITY_PASSWORD_SALT", "change-me"
    )
    FRONTEND_BASE_URL = os.getenv(
        "FRONTEND_BASE_URL", "http://localhost:5000"
    )
    APP_BASE_URL = os.getenv(
        "APP_BASE_URL", "https://conecta-senai.up.railway.app"
    )

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI", f"redis://{REDIS_HOST}:{REDIS_PORT}"
    )
