from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.session import get_db
from models.business import Business
from models.staff import Staff
from models.service import Service
from services.availability_service import get_available_slots

router = APIRouter(
    prefix="/business",
    tags=["Availability"]
)


@router.get("/{business_slug}/availability/slots")
def availability_slots(
    business_slug: str,
    staff_id: int = Query(...),
    service_id: int = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(
        Business.slug == business_slug
    ).first()

    if not business:
        raise HTTPException(404, "Business not found")

    staff = db.query(Staff).filter(
        Staff.id == staff_id,
        Staff.business_id == business.id
    ).first()

    if not staff:
        raise HTTPException(404, "Staff not found in this business")

    service = db.query(Service).filter(
        Service.id == service_id,
        Service.business_id == business.id
    ).first()

    if not service:
        raise HTTPException(404, "Service not found in this business")

    return get_available_slots(
        session=db,
        staff_id=staff_id,
        service_id=service_id,
        date_from=date_from,
        date_to=date_to,
    )
