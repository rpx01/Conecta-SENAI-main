"""Configuração de logging estruturado para a aplicação Conecta SENAI."""
import os
import logging
import logging.config
from flask import g, has_request_context

try:
    from pythonjsonlogger import jsonlogger
except ImportError:  # pragma: no cover - fallback quando pacote opcional não está instalado
    jsonlogger = None  # type: ignore[assignment]

try:
    from opentelemetry import trace
except ImportError:  # pragma: no cover - módulo opcional
    trace = None  # type: ignore[assignment]

APP_ENV = os.getenv("APP_ENV", "dev")
APP_RELEASE = os.getenv("APP_RELEASE", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.env = APP_ENV
        record.release = APP_RELEASE
        record.request_id = (
            getattr(g, "request_id", None) if has_request_context() else None
        )
        if trace:
            span = trace.get_current_span()
            ctx = span.get_span_context()
            if ctx and ctx.is_valid:
                record.trace_id = format(ctx.trace_id, "032x")
                record.span_id = format(ctx.span_id, "016x")
            else:
                record.trace_id = None
                record.span_id = None
        else:
            record.trace_id = None
            record.span_id = None
        return True


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "context": {"()": ContextFilter},
    },
    "formatters": {
        "json": ({
            "()": jsonlogger.JsonFormatter,
            "fmt": (
                "%(asctime)s %(levelname)s %(name)s %(message)s "
                "%(route)s %(method)s %(status)s %(latency_ms)s %(user_id)s "
                "%(request_id)s %(trace_id)s %(span_id)s"
            ),
            "rename_fields": {
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
        } if jsonlogger else {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        })
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "json",
            "filters": ["context"],
            "stream": "ext://sys.stdout",
        },
        "gunicorn_error": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "json",
            "filters": ["context"],
            "stream": "ext://sys.stderr",
        },
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["default"],
    },
    "loggers": {
        "gunicorn.error": {
            "level": LOG_LEVEL,
            "handlers": ["gunicorn_error"],
            "propagate": False,
        }
    },
}


def setup_logging() -> None:
    """Aplica a configuração de logging, com fallback simples em ambientes locais."""

    if not jsonlogger:
        logging.basicConfig(level=LOG_LEVEL)
        return
    logging.config.dictConfig(LOGGING_CONFIG)
