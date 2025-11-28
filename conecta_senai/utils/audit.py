"""Funções de auditoria e registro de ações do sistema."""

from __future__ import annotations

from typing import Any
from conecta_senai.models import db
from conecta_senai.models.audit_log import AuditLog


def log_action(user_id: int | None, action: str, entity: str, entity_id: int, details: dict | None = None) -> None:
    """Grava um registro de auditoria de forma silenciosa."""
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=details or {},
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
