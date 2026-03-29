from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from dependencies.admin_auth import get_current_admin_user
from models.admin_user import AdminUser
from schemas.admin_service import (
    AdminCreateServiceRequest,
    AdminServiceOut,
    AdminUpdateServiceRequest,
)
from services.admin_catalog_service import (
    AdminCatalogConflictError,
    AdminCatalogNotFoundError,
    create_service,
    deactivate_service,
    list_services,
    update_service,
)
from services.audit_service import log_admin_action


router = APIRouter(prefix="/admin/services", tags=["Admin Services"])


def _serialize_service(service) -> AdminServiceOut:
    return AdminServiceOut(
        id=service.id,
        name=service.name,
        slug=service.slug,
        duration_minutes=service.duration_minutes,
        price_amount=service.price_amount,
        price_currency=service.price_currency,
        active=service.active,
    )


@router.get("", response_model=list[AdminServiceOut], status_code=status.HTTP_200_OK)
def admin_list_services(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    services = list_services(db, business_id=current_admin.business_id)
    return [_serialize_service(service) for service in services]


@router.post("", response_model=AdminServiceOut, status_code=status.HTTP_201_CREATED)
def admin_create_service(
    payload: AdminCreateServiceRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    try:
        service = create_service(
            db,
            business_id=current_admin.business_id,
            name=payload.name,
            slug=payload.slug,
            duration_minutes=payload.duration_minutes,
            price_amount=payload.price_amount,
            price_currency=payload.price_currency,
            active=payload.active,
        )
        log_admin_action(
            db,
            business_id=current_admin.business_id,
            admin_user_id=current_admin.id,
            action="service_created",
            entity_type="service",
            entity_id=service.id,
            payload={
                "slug": service.slug,
                "name": service.name,
                "duration_minutes": service.duration_minutes,
                "price_amount": service.price_amount,
                "price_currency": service.price_currency,
                "active": service.active,
            },
        )
        db.commit()
        return _serialize_service(service)
    except AdminCatalogConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{service_id}", response_model=AdminServiceOut, status_code=status.HTTP_200_OK)
def admin_update_service(
    service_id: int,
    payload: AdminUpdateServiceRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes provided")

    try:
        service = update_service(
            db,
            business_id=current_admin.business_id,
            service_id=service_id,
            changes=changes,
        )
        log_admin_action(
            db,
            business_id=current_admin.business_id,
            admin_user_id=current_admin.id,
            action="service_updated",
            entity_type="service",
            entity_id=service.id,
            payload=changes,
        )
        db.commit()
        return _serialize_service(service)
    except AdminCatalogConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AdminCatalogNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{service_id}", response_model=AdminServiceOut, status_code=status.HTTP_200_OK)
def admin_delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    try:
        service = deactivate_service(
            db,
            business_id=current_admin.business_id,
            service_id=service_id,
        )
        log_admin_action(
            db,
            business_id=current_admin.business_id,
            admin_user_id=current_admin.id,
            action="service_deactivated",
            entity_type="service",
            entity_id=service.id,
            payload={"active": False},
        )
        db.commit()
        return _serialize_service(service)
    except AdminCatalogNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
