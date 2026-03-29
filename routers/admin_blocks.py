from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.session import get_db
from dependencies.admin_auth import get_current_admin_user
from models.admin_user import AdminUser
from models.staff import Staff
from schemas.admin_block import AdminCreateTimeBlockRequest, AdminTimeBlockOut
from services.audit_service import log_admin_action
from services.time_block_service import (
    TimeBlockConflictError,
    TimeBlockError,
    TimeBlockNotFoundError,
    create_time_block,
    delete_time_block,
    list_time_blocks,
)
from services.timezone_utils import get_business_tz, to_business_tz


router = APIRouter(prefix="/admin/blocks", tags=["Admin Blocks"])


def _to_out(block: object, staff_slug: str | None, tz: ZoneInfo) -> AdminTimeBlockOut:
    return AdminTimeBlockOut(
        id=block.id,
        staff_id=block.staff_id,
        staff_slug=staff_slug,
        start_datetime=to_business_tz(block.start_datetime, tz).isoformat(),
        end_datetime=to_business_tz(block.end_datetime, tz).isoformat(),
        reason=block.reason,
        notes=block.notes,
        created_by_admin_id=block.created_by_admin_id,
        created_at=to_business_tz(block.created_at, tz).isoformat(),
    )


def _resolve_staff_id(
    db: Session,
    *,
    business_id: int,
    staff_slug: str | None,
) -> int | None:
    if not staff_slug:
        return None

    normalized = staff_slug.strip().lower()
    staff = db.query(Staff).filter(
        Staff.business_id == business_id,
        Staff.slug == normalized,
        Staff.active.is_(True),
    ).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    return staff.id


@router.get("", response_model=list[AdminTimeBlockOut], status_code=status.HTTP_200_OK)
def admin_list_blocks(
    date_from: date = Query(...),
    date_to: date = Query(...),
    staff_slug: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    if date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_to must be greater than or equal to date_from",
        )

    tz = get_business_tz(db, current_admin.business_id)
    staff_id = _resolve_staff_id(
        db,
        business_id=current_admin.business_id,
        staff_slug=staff_slug,
    )
    start = datetime.combine(date_from, time.min, tzinfo=tz)
    end = datetime.combine(date_to, time.max, tzinfo=tz)

    blocks = list_time_blocks(
        db,
        business_id=current_admin.business_id,
        date_from=start,
        date_to=end,
        staff_id=staff_id,
    )
    staff_ids = {block.staff_id for block in blocks if block.staff_id is not None}
    staff_map = {}
    if staff_ids:
        rows = db.query(Staff).filter(Staff.id.in_(staff_ids)).all()
        staff_map = {row.id: row.slug for row in rows}

    return [_to_out(block, staff_map.get(block.staff_id), tz) for block in blocks]


@router.post("", response_model=AdminTimeBlockOut, status_code=status.HTTP_201_CREATED)
def admin_create_block(
    payload: AdminCreateTimeBlockRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    tz = get_business_tz(db, current_admin.business_id)
    try:
        staff_id = _resolve_staff_id(
            db,
            business_id=current_admin.business_id,
            staff_slug=payload.staff_slug,
        )

        block = create_time_block(
            db,
            business_id=current_admin.business_id,
            staff_id=staff_id,
            start_datetime=payload.start_datetime,
            end_datetime=payload.end_datetime,
            reason=payload.reason,
            notes=payload.notes,
            created_by_admin_id=current_admin.id,
        )
        db.flush()
        log_admin_action(
            db,
            business_id=current_admin.business_id,
            admin_user_id=current_admin.id,
            action="time_block_created",
            entity_type="time_block",
            entity_id=block.id,
            payload={
                "staff_id": block.staff_id,
                "start_datetime": to_business_tz(block.start_datetime, tz).isoformat(),
                "end_datetime": to_business_tz(block.end_datetime, tz).isoformat(),
                "reason": block.reason,
            },
        )
        db.commit()
    except TimeBlockConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TimeBlockError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _to_out(block, payload.staff_slug.lower().strip() if payload.staff_slug else None, tz)


@router.delete("/{block_id}", status_code=status.HTTP_200_OK)
def admin_delete_block(
    block_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    tz = get_business_tz(db, current_admin.business_id)
    try:
        block = delete_time_block(
            db,
            business_id=current_admin.business_id,
            block_id=block_id,
        )
        log_admin_action(
            db,
            business_id=current_admin.business_id,
            admin_user_id=current_admin.id,
            action="time_block_deleted",
            entity_type="time_block",
            entity_id=block_id,
            payload={
                "staff_id": block.staff_id,
                "start_datetime": to_business_tz(block.start_datetime, tz).isoformat(),
                "end_datetime": to_business_tz(block.end_datetime, tz).isoformat(),
                "reason": block.reason,
            },
        )
        db.commit()
    except TimeBlockNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return {"deleted": True, "id": block_id}
