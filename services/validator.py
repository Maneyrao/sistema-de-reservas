from sqlalchemy.orm import Session
from sqlalchemy import select

from models.business import Business
from models.staff import Staff
from models.service import Service
from models.booking import Booking


class NotFoundError(Exception):
    pass


def get_business_by_slug(
    session: Session,
    business_slug: str,
) -> Business:
    business = session.execute(
        select(Business).where(Business.slug == business_slug)
    ).scalar_one_or_none()

    if not business:
        raise NotFoundError("Business not found")

    return business


def validate_staff_belongs_to_business(
    session: Session,
    staff_id: int,
    business_id: int,
) -> Staff:
    staff = session.execute(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.business_id == business_id,
            Staff.active.is_(True),
        )
    ).scalar_one_or_none()

    if not staff:
        raise NotFoundError("Staff not found in this business")

    return staff


def validate_service_belongs_to_business(
    session: Session,
    service_id: int,
    business_id: int,
) -> Service:
    service = session.execute(
        select(Service).where(
            Service.id == service_id,
            Service.business_id == business_id,
            Service.active.is_(True),
        )
    ).scalar_one_or_none()

    if not service:
        raise NotFoundError("Service not found in this business")

    return service


def validate_booking_belongs_to_business(
    session: Session,
    booking_id: int,
    business_id: int,
) -> Booking:
    booking = session.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.business_id == business_id,
        )
    ).scalar_one_or_none()

    if not booking:
        raise NotFoundError("Booking not found in this business")

    return booking
