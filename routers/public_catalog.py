from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.business import Business
from models.service import Service
from models.staff import Staff
from models.staff_service import StaffService
from schemas.public_catalog import PublicCatalogResponse


router = APIRouter(
    prefix="/v1/business",
    tags=["Public Catalog"],
)

MAX_ADVANCE_DAYS = 30
SLOT_STEP_MINUTES = 15


@router.get(
    "/{business_slug}/catalog",
    response_model=PublicCatalogResponse,
    status_code=status.HTTP_200_OK,
)
def get_public_catalog(
    business_slug: str,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(Business.slug == business_slug).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    public_staff = (
        db.query(Staff)
        .filter(
            Staff.business_id == business.id,
            Staff.active.is_(True),
        )
        .order_by(Staff.name.asc())
        .all()
    )

    services = (
        db.query(Service)
        .filter(
            Service.business_id == business.id,
            Service.active.is_(True),
        )
        .order_by(Service.name.asc())
        .all()
    )

    staff_service_rows = (
        db.query(StaffService.staff_id, Service.slug)
        .join(Service, Service.id == StaffService.service_id)
        .filter(
            Service.business_id == business.id,
            Service.active.is_(True),
            StaffService.staff_id.in_([staff.id for staff in public_staff]) if public_staff else False,
        )
        .all()
    )

    services_by_staff_id: dict[int, list[str]] = {staff.id: [] for staff in public_staff}
    for staff_id, service_slug in staff_service_rows:
        services_by_staff_id.setdefault(staff_id, []).append(service_slug)

    public_staff = [
        staff for staff in public_staff
        if services_by_staff_id.get(staff.id)
    ]

    return {
        "business": {
            "slug": business.slug,
            "name": business.name,
            "timezone": business.timezone,
            "tagline": business.tagline,
            "hero_title": business.hero_title,
            "hero_description": business.hero_description,
            "announcement": business.announcement,
            "booking_note": business.booking_note,
            "address": business.address,
            "phone": business.phone,
            "instagram_url": business.instagram_url,
            "maps_url": business.maps_url,
        },
        "staff": [
            {
                "slug": staff.slug,
                "name": staff.name,
                "title": staff.title,
                "bio": staff.bio,
                "avatar_url": staff.avatar_url,
                "service_slugs": services_by_staff_id.get(staff.id, []),
            }
            for staff in public_staff
        ],
        "services": [
            {
                "slug": service.slug,
                "name": service.name,
                "duration_minutes": service.duration_minutes,
                "price_amount": service.price_amount,
                "price_currency": service.price_currency,
            }
            for service in services
        ],
        "booking_rules": {
            "slot_step_minutes": SLOT_STEP_MINUTES,
            "max_advance_days": MAX_ADVANCE_DAYS,
            "default_staff_slug": public_staff[0].slug if public_staff else "",
        },
    }
