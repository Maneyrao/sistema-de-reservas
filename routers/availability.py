from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.business import Business
from models.service import Service
from models.staff import Staff
from services.availability_service import get_available_slots

router = APIRouter(
    prefix="/v1/business",
    tags=["Availability"]
)

@router.get("/{business_slug}/availability/slots", status_code=status.HTTP_200_OK)
def get_slots(
    business_slug: str,
    service_slug: str = Query(..., description="Slug público del servicio"),
    date_from: date = Query(...),
    date_to: date = Query(...),
    staff_slug: str | None = Query(None, description="Slug público del staff (opcional)"),
    db: Session = Depends(get_db),
):
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

    # 3. Resolver Staff (opcional)
    if staff_slug:
        staff = db.query(Staff).filter(
            Staff.slug == staff_slug,
            Staff.business_id == business.id,
            Staff.active.is_(True)
        ).first()
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found or inactive")

    # 4. Delegar al service (FIRMA CORRECTA)
    return get_available_slots(
        session=db,
        business_id=business.id,
        service_slug=service.slug,
        staff_slug=staff_slug,
        date_from=date_from,
        date_to=date_to,
    )
