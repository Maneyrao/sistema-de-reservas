import json
from typing import Any

from sqlalchemy.orm import Session

from models.audit_log import AuditLog


def log_admin_action(
    session: Session,
    *,
    business_id: int,
    admin_user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: str | int,
    payload: dict[str, Any] | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        business_id=business_id,
        admin_user_id=admin_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        payload_json=json.dumps(payload, ensure_ascii=False) if payload is not None else None,
    )
    session.add(audit_log)
    return audit_log
