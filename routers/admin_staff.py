from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from dependencies.admin_auth import get_current_admin_user
from models.admin_user import AdminUser
from schemas.admin_staff import (
    AdminAssignedServiceOut,
    AdminAvailabilityRuleOut,
    AdminCreateStaffRequest,
    AdminStaffOut,
    AdminUpdateStaffRequest,
)
from services.admin_catalog_service import (
    AdminCatalogConflictError,
    AdminCatalogError,
    AdminCatalogNotFoundError,
    create_staff,
    deactivate_staff,
    list_staff,
    update_staff,
)
from services.audit_service import log_admin_action


router = APIRouter(prefix="/admin/staff", tags=["Admin Staff"])


def _serialize_staff(staff) -> AdminStaffOut:
    services = sorted(
        [
            AdminAssignedServiceOut(
                id=item.service.id,
                name=item.service.name,
                slug=item.service.slug,
                duration_minutes=item.service.duration_minutes,
                price_amount=item.service.price_amount,
                price_currency=item.service.price_currency,
                active=item.service.active,
            )
            for item in staff.staff_services
            if item.service is not None
        ],
        key=lambda item: item.name.lower(),
    )
    availability_rules = sorted(
        [
            AdminAvailabilityRuleOut(
                id=item.id,
                weekday=item.weekday,
                start_time=item.start_time,
                end_time=item.end_time,
            )
            for item in staff.availability_rules
        ],
        key=lambda item: (item.weekday, item.start_time),
    )

    return AdminStaffOut(
        id=staff.id,
        name=staff.name,
        slug=staff.slug,
        title=staff.title,
        bio=staff.bio,
        avatar_url=staff.avatar_url,
        active=staff.active,
        services=services,
        availability_rules=availability_rules,
    )


@router.get("", response_model=list[AdminStaffOut], status_code=status.HTTP_200_OK)
def admin_list_staff(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    staff_rows = list_staff(db, business_id=current_admin.business_id)
    return [_serialize_staff(item) for item in staff_rows]


@router.post("", response_model=AdminStaffOut, status_code=status.HTTP_201_CREATED)
def admin_create_staff(
    payload: AdminCreateStaffRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    try:
        staff = create_staff(
            db,
            business_id=current_admin.business_id,
            name=payload.name,
            slug=payload.slug,
            title=payload.title,
            bio=payload.bio,
            avatar_url=payload.avatar_url,
            active=payload.active,
            service_ids=payload.service_ids,
            availability_rules=[item.model_dump() for item in payload.availability_rules],
        )
        log_admin_action(
            db,
            business_id=current_admin.business_id,
            admin_user_id=current_admin.id,
            action="staff_created",
            entity_type="staff",
            entity_id=staff.id,
            payload={
                "slug": staff.slug,
                "name": staff.name,
                "title": staff.title,
                "bio": staff.bio,
                "avatar_url": staff.avatar_url,
                "active": staff.active,
                "service_ids": payload.service_ids,
                "availability_rules": [item.model_dump(mode="json") for item in payload.availability_rules],
            },
        )
        db.commit()
        return _serialize_staff(staff)
    except AdminCatalogConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (AdminCatalogError, AdminCatalogNotFoundError) as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{staff_id}", response_model=AdminStaffOut, status_code=status.HTTP_200_OK)
def admin_update_staff(
    staff_id: int,
    payload: AdminUpdateStaffRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes provided")

    serialized_changes = {
        key: value
        for key, value in changes.items()
        if key not in {"availability_rules"}
    }
    if "availability_rules" in changes:
        serialized_changes["availability_rules"] = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in payload.availability_rules or []
        ]

    try:
        staff = update_staff(
            db,
            business_id=current_admin.business_id,
            staff_id=staff_id,
            changes={
                **changes,
                **(
                    {
                        "availability_rules": [
                            item.model_dump() if hasattr(item, "model_dump") else item
                            for item in payload.availability_rules or []
                        ]
                    }
                    if "availability_rules" in changes
                    else {}
                ),
            },
        )
        log_admin_action(
            db,
            business_id=current_admin.business_id,
            admin_user_id=current_admin.id,
            action="staff_updated",
            entity_type="staff",
            entity_id=staff.id,
            payload=serialized_changes,
        )
        db.commit()
        return _serialize_staff(staff)
    except AdminCatalogConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AdminCatalogNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AdminCatalogError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{staff_id}", response_model=AdminStaffOut, status_code=status.HTTP_200_OK)
def admin_delete_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    try:
        staff = deactivate_staff(
            db,
            business_id=current_admin.business_id,
            staff_id=staff_id,
        )
        log_admin_action(
            db,
            business_id=current_admin.business_id,
            admin_user_id=current_admin.id,
            action="staff_deactivated",
            entity_type="staff",
            entity_id=staff.id,
            payload={"active": False},
        )
        db.commit()
        return _serialize_staff(staff)
    except AdminCatalogNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
