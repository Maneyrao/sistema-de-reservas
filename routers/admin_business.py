from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.session import get_db
from dependencies.admin_auth import get_current_admin_user
from models.admin_user import AdminUser
from schemas.admin_activity import AdminActivityOut
from schemas.admin_business import AdminBusinessOut, AdminUpdateBusinessRequest
from services.admin_business_service import (
    AdminBusinessNotFoundError,
    get_business,
    list_recent_activity,
    update_business,
)
from services.audit_service import log_admin_action
from services.timezone_utils import get_business_tz, to_business_tz


router = APIRouter(prefix="/admin/business", tags=["Admin Business"])


def _serialize_business(business) -> AdminBusinessOut:
    return AdminBusinessOut(
        id=business.id,
        slug=business.slug,
        name=business.name,
        timezone=business.timezone,
        tagline=business.tagline,
        hero_title=business.hero_title,
        hero_description=business.hero_description,
        announcement=business.announcement,
        booking_note=business.booking_note,
        address=business.address,
        phone=business.phone,
        instagram_url=business.instagram_url,
        maps_url=business.maps_url,
    )


@router.get("", response_model=AdminBusinessOut, status_code=status.HTTP_200_OK)
def admin_get_business(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    try:
        business = get_business(db, business_id=current_admin.business_id)
        return _serialize_business(business)
    except AdminBusinessNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("", response_model=AdminBusinessOut, status_code=status.HTTP_200_OK)
def admin_update_business(
    payload: AdminUpdateBusinessRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes provided")

    try:
        business = update_business(db, business_id=current_admin.business_id, changes=changes)
        log_admin_action(
            db,
            business_id=current_admin.business_id,
            admin_user_id=current_admin.id,
            action="business_updated",
            entity_type="business",
            entity_id=business.id,
            payload=changes,
        )
        db.commit()
        return _serialize_business(business)
    except AdminBusinessNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/activity", response_model=list[AdminActivityOut], status_code=status.HTTP_200_OK)
def admin_list_activity(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    tz = get_business_tz(db, current_admin.business_id)
    rows = list_recent_activity(db, business_id=current_admin.business_id, limit=limit)
    return [
        AdminActivityOut(
            id=item.id,
            action=item.action,
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            admin_name=item.admin_user.full_name if item.admin_user else None,
            payload_json=item.payload_json,
            created_at=to_business_tz(item.created_at, tz).isoformat(),
        )
        for item in rows
    ]
