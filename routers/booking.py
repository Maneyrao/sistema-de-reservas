from fastapi import APIRouter, Depends, HTTPException, status,Query
from models.business import Business
from models.staff import Staff
from models.service import Service
from schemas.booking import BookingCreate
from services.booking_service import create_booking, SlotNotAvailable
from datetime import date
from sqlalchemy.orm import Session
from database.session import get_db
from services.booking_service import get_business_bookings_by_date
from services.validator import get_business_by_slug

router = APIRouter(
    prefix="/business",
    tags=["Bookings"]
)

@router.get("/{business_slug}/bookings")
def list_business_bookings(
    business_slug: str,
    date: date = Query(...),
    staff_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    business = get_business_by_slug(db, business_slug)

    bookings = get_business_bookings_by_date(
        session=db,
        business_id=business.id,
        day=date,
        staff_id=staff_id,
    )

    return {
        "business": {
            "slug": business.slug,
            "name": business.name,
        },
        "date": date,
        "total": len(bookings),
        "bookings": [
            {
                "id": b.id,
                "start": b.start_datetime,
                "end": b.end_datetime,
                "staff": b.staff.name,
                "service": b.service.name,
                "customer": b.customer.name,
            }
            for b in bookings
        ],
    }

@router.post("/{business_slug}/bookings", status_code=status.HTTP_201_CREATED)
def create_new_booking(
    business_slug: str,
    payload: BookingCreate,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(
        Business.slug == business_slug
    ).first()

    if not business:
        raise HTTPException(404, "Business not found")

    staff = db.query(Staff).filter(
        Staff.id == payload.staff_id,
        Staff.business_id == business.id
    ).first()

    if not staff:
        raise HTTPException(404, "Staff not found in this business")

    service = db.query(Service).filter(
        Service.id == payload.service_id,
        Service.business_id == business.id
    ).first()

    if not service:
        raise HTTPException(404, "Service not found in this business")

    try:
        return create_booking(
            session=db,
            business_id=business.id,
            staff_id=payload.staff_id,
            service_id=payload.service_id,
            customer_id=payload.customer_id,
            start_datetime=payload.start_datetime,
        )
    except SlotNotAvailable as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
