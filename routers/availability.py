from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.business import Business
from models.service import Service
from models.staff import Staff
from models.staff_service import StaffService
from services.availability_service import get_available_slots

router = APIRouter(
    prefix="/v1/business",
    tags=["Availability"]
)


@router.get("/{business_slug}/availability/slots", status_code=status.HTTP_200_OK)
def get_slots(
    business_slug: str,
    service_slug: str = Query(..., description="Slug publico del servicio"),
    date_from: date = Query(...),
    date_to: date = Query(...),
    staff_slug: str | None = Query(None, description="Slug publico del staff (opcional)"),
    db: Session = Depends(get_db),
):
    if date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_to must be greater than or equal to date_from.",
        )

    if (date_to - date_from).days > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 30 days.",
        )

    # 1. Resolver Business
    business = db.query(Business).filter(Business.slug == business_slug).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # 2. Resolver Service (validar ownership)
    service = db.query(Service).filter(
        Service.slug == service_slug,
        Service.business_id == business.id,
        Service.active.is_(True)
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found or inactive")

    if not staff_slug or not staff_slug.strip():
        first_staff = (
            db.query(Staff)
            .join(StaffService, StaffService.staff_id == Staff.id)
            .filter(
                Staff.business_id == business.id,
                Staff.active.is_(True),
                StaffService.service_id == service.id,
            )
            .order_by(Staff.name.asc())
            .first()
        )
        normalized_staff_slug = first_staff.slug if first_staff else ""
    else:
        normalized_staff_slug = staff_slug.strip().lower()

    staff = db.query(Staff).filter(
        Staff.slug == normalized_staff_slug,
        Staff.business_id == business.id,
        Staff.active.is_(True)
    ).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found or inactive")

    # 4. Delegar al service
    try:
        return get_available_slots(
            session=db,
            business_id=business.id,
            service_slug=service.slug,
            staff_slug=staff.slug,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as exc:
        detail = str(exc)
        if detail in {"Service not found in this business", "Staff not found in this business"}:
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc
