import logging
import uuid
from flask import jsonify

logger = logging.getLogger(__name__)


def handle_internal_error(error: Exception):
    correlation_id = str(uuid.uuid4())
    logger.exception("Correlation ID %s: %s", correlation_id, error)
    return (
        jsonify(
            {
                "erro": "Ocorreu um erro interno do servidor",
                "correlation_id": correlation_id,
            }
        ),
        500,
    )
