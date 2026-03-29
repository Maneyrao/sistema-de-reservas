from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.admin_user import AdminUser
from models.audit_log import AuditLog
from models.business import Business


class AdminBusinessError(Exception):
    pass


class AdminBusinessNotFoundError(AdminBusinessError):
    pass


def get_business(session: Session, *, business_id: int) -> Business:
    business = session.execute(
        select(Business).where(Business.id == business_id)
    ).scalar_one_or_none()
    if business is None:
        raise AdminBusinessNotFoundError("Business not found")
    return business


def update_business(session: Session, *, business_id: int, changes: dict[str, Any]) -> Business:
    business = get_business(session, business_id=business_id)
    for key, value in changes.items():
        setattr(business, key, value)
    session.add(business)
    session.flush()
    return business


def list_recent_activity(
    session: Session,
    *,
    business_id: int,
    limit: int = 20,
) -> list[AuditLog]:
    return session.execute(
        select(AuditLog)
        .where(AuditLog.business_id == business_id)
        .options(joinedload(AuditLog.admin_user))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).scalars().all()


def count_active_admins(session: Session, *, business_id: int) -> int:
    rows = session.execute(
        select(AdminUser).where(
            AdminUser.business_id == business_id,
            AdminUser.is_active.is_(True),
        )
    ).scalars().all()
    return len(rows)
