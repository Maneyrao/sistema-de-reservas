from datetime import date, datetime, time, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.booking import Booking, BookingStatus
from models.customer import Customer
from models.service import Service
from models.staff import Staff
from services.audit_service import log_admin_action
from services.booking_service import (
    BookingNotFound,
    InvalidService,
    InvalidBookingRequest,
    SlotNotAvailable,
    create_booking,
    resolve_customer,
)
from services.timezone_utils import get_business_tz, to_business_tz


class AdminBookingError(Exception):
    pass


class AdminBookingConflictError(AdminBookingError):
    pass


def list_bookings_for_range(
    session: Session,
    *,
    business_id: int,
    date_from: date,
    date_to: date,
    statuses: list[BookingStatus] | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """
    Retorna bookings paginados para el rango dado.
    Siempre devuelve: {items, total, page, page_size, total_pages}
    """
    import math

    tz = get_business_tz(session, business_id)
    start_dt = datetime.combine(date_from, time.min, tzinfo=tz)
    end_dt = datetime.combine(date_to, time.max, tzinfo=tz)

    base_where = [
        Booking.business_id == business_id,
        Booking.start_datetime >= start_dt,
        Booking.start_datetime <= end_dt,
    ]
    if statuses:
        base_where.append(Booking.status.in_(statuses))

    total: int = session.execute(
        select(func.count(Booking.id))
        .join(Customer, Customer.id == Booking.customer_id)
        .join(Service, Service.id == Booking.service_id)
        .join(Staff, Staff.id == Booking.staff_id)
        .where(*base_where)
    ).scalar_one()

    stmt = (
        select(
            Booking,
            Customer.name,
            Customer.phone,
            Customer.email,
            Service.name,
            Service.slug,
            Staff.name,
            Staff.slug,
        )
        .join(Customer, Customer.id == Booking.customer_id)
        .join(Service, Service.id == Booking.service_id)
        .join(Staff, Staff.id == Booking.staff_id)
        .where(*base_where)
        .order_by(Booking.start_datetime)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    rows = session.execute(stmt).all()
    items: list[dict] = []
    for booking, customer_name, customer_phone, customer_email, service_name, service_slug, staff_name, staff_slug in rows:
        start = to_business_tz(booking.start_datetime, tz)
        end = to_business_tz(booking.end_datetime, tz)
        items.append(
            {
                "id": booking.id,
                "status": booking.status.value,
                "start_datetime": start.isoformat(),
                "end_datetime": end.isoformat(),
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "service_name": service_name,
                "service_slug": service_slug,
                "staff_name": staff_name,
                "staff_slug": staff_slug,
                "notes": booking.notes,
                "canceled_reason": booking.canceled_reason,
                "created_at": to_business_tz(booking.created_at, tz).isoformat(),
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if page_size > 0 else 0,
    }


def get_booking_detail(
    session: Session,
    *,
    business_id: int,
    booking_id: int,
) -> dict | None:
    tz = get_business_tz(session, business_id)

    rows = session.execute(
        select(
            Booking,
            Customer.name,
            Customer.phone,
            Customer.email,
            Service.name,
            Service.slug,
            Staff.name,
            Staff.slug,
        )
        .join(Customer, Customer.id == Booking.customer_id)
        .join(Service, Service.id == Booking.service_id)
        .join(Staff, Staff.id == Booking.staff_id)
        .where(
            Booking.business_id == business_id,
            Booking.id == booking_id,
        )
    ).all()
    if not rows:
        return None
    booking, customer_name, customer_phone, customer_email, service_name, service_slug, staff_name, staff_slug = rows[0]
    return {
        "id": booking.id,
        "status": booking.status.value,
        "start_datetime": to_business_tz(booking.start_datetime, tz).isoformat(),
        "end_datetime": to_business_tz(booking.end_datetime, tz).isoformat(),
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "customer_email": customer_email,
        "service_name": service_name,
        "service_slug": service_slug,
        "staff_name": staff_name,
        "staff_slug": staff_slug,
        "notes": booking.notes,
        "canceled_reason": booking.canceled_reason,
        "created_at": to_business_tz(booking.created_at, tz).isoformat(),
    }


def create_booking_by_admin(
    session: Session,
    *,
    business_id: int,
    staff_slug: str,
    service_slug: str,
    first_name: str,
    last_name: str,
    phone: str,
    email: str | None,
    start_datetime: datetime,
    admin_user_id: int,
    notes: str | None = None,
    status: BookingStatus = BookingStatus.confirmed,
) -> Booking:
    tz = get_business_tz(session, business_id)

    staff = session.execute(
        select(Staff).where(
            Staff.business_id == business_id,
            Staff.slug == staff_slug.strip().lower(),
            Staff.active.is_(True),
        )
    ).scalar_one_or_none()
    if not staff:
        raise AdminBookingError("Staff not found")

    service = session.execute(
        select(Service).where(
            Service.business_id == business_id,
            Service.slug == service_slug.strip().lower(),
            Service.active.is_(True),
        )
    ).scalar_one_or_none()
    if not service:
        raise AdminBookingError("Service not found")

    customer = resolve_customer(
        session,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
    )

    try:
        booking = create_booking(
            session=session,
            business_id=business_id,
            staff_id=staff.id,
            service_id=service.id,
            customer_id=customer.id,
            start_datetime=start_datetime,
            notes=notes,
            status=status,
        )
    except (SlotNotAvailable, InvalidBookingRequest, InvalidService) as exc:
        raise AdminBookingConflictError(str(exc)) from exc

    session.flush()
    log_admin_action(
        session,
        business_id=business_id,
        admin_user_id=admin_user_id,
        action="booking_created",
        entity_type="booking",
        entity_id=booking.id,
        payload={
            "staff_slug": staff.slug,
            "service_slug": service.slug,
            "customer_name": customer.name,
            "customer_phone": customer.phone,
            "start_datetime": to_business_tz(booking.start_datetime, tz).isoformat(),
            "status": booking.status.value,
        },
    )
    return booking


def cancel_booking_by_admin(
    session: Session,
    *,
    business_id: int,
    booking_id: int,
    reason: str | None,
    admin_user_id: int,
) -> Booking:
    booking = session.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.business_id == business_id,
        )
    ).scalar_one_or_none()
    if not booking:
        raise BookingNotFound("Booking not found")

    if booking.status in {BookingStatus.completed, BookingStatus.no_show}:
        raise AdminBookingError("Completed/no_show bookings cannot be canceled")

    if booking.status == BookingStatus.canceled:
        return booking

    previous_status = booking.status
    now = datetime.now(timezone.utc)
    booking.status = BookingStatus.canceled
    booking.canceled_reason = reason.strip() if reason else None
    booking.canceled_at = now
    booking.updated_at = now
    session.add(booking)

    log_admin_action(
        session,
        business_id=business_id,
        admin_user_id=admin_user_id,
        action="booking_cancelled",
        entity_type="booking",
        entity_id=booking.id,
        payload={
            "reason": booking.canceled_reason,
            "previous_status": previous_status.value,
        },
    )
    return booking


def reschedule_booking_by_admin(
    session: Session,
    *,
    business_id: int,
    booking_id: int,
    new_start_datetime: datetime,
    reason: str | None,
    admin_user_id: int,
) -> Booking:
    tz = get_business_tz(session, business_id)

    booking = session.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.business_id == business_id,
        )
    ).scalar_one_or_none()
    if not booking:
        raise BookingNotFound("Booking not found")

    if booking.status in {BookingStatus.canceled, BookingStatus.completed, BookingStatus.no_show}:
        raise AdminBookingError("Booking cannot be rescheduled from its current status")

    new_start_datetime = to_business_tz(new_start_datetime, tz)
    now = datetime.now(timezone.utc)

    booking.status = BookingStatus.canceled
    booking.canceled_reason = reason.strip() if reason else "rescheduled_by_admin"
    booking.canceled_at = now
    booking.updated_at = now
    session.add(booking)

    try:
        new_booking = create_booking(
            session=session,
            business_id=booking.business_id,
            staff_id=booking.staff_id,
            service_id=booking.service_id,
            customer_id=booking.customer_id,
            start_datetime=new_start_datetime,
            notes=booking.notes,
            rescheduled_from_booking_id=booking.id,
        )
    except (SlotNotAvailable, InvalidBookingRequest) as exc:
        raise AdminBookingConflictError(str(exc)) from exc

    new_booking.updated_at = now
    session.add(new_booking)
    session.flush()

    log_admin_action(
        session,
        business_id=business_id,
        admin_user_id=admin_user_id,
        action="booking_rescheduled",
        entity_type="booking",
        entity_id=booking.id,
        payload={
            "from_booking_id": booking.id,
            "to_booking_id": new_booking.id,
            "new_start_datetime": new_start_datetime.isoformat(),
            "reason": reason,
        },
    )

    log_admin_action(
        session,
        business_id=business_id,
        admin_user_id=admin_user_id,
        action="booking_created_from_reschedule",
        entity_type="booking",
        entity_id=new_booking.id,
        payload={
            "from_booking_id": booking.id,
            "new_start_datetime": new_start_datetime.isoformat(),
        },
    )
    return new_booking


def update_booking_status_by_admin(
    session: Session,
    *,
    business_id: int,
    booking_id: int,
    new_status: BookingStatus,
    admin_user_id: int,
    reason: str | None = None,
) -> Booking:
    booking = session.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.business_id == business_id,
        )
    ).scalar_one_or_none()
    if not booking:
        raise BookingNotFound("Booking not found")

    current_status = booking.status
    if current_status == new_status:
        return booking

    now = datetime.now(timezone.utc)
    booking.status = new_status
    booking.updated_at = now

    if new_status == BookingStatus.canceled:
        booking.canceled_reason = reason.strip() if reason else "cancelled_by_admin"
        booking.canceled_at = now

    session.add(booking)
    log_admin_action(
        session,
        business_id=business_id,
        admin_user_id=admin_user_id,
        action="booking_status_updated",
        entity_type="booking",
        entity_id=booking.id,
        payload={
            "previous_status": current_status.value,
            "new_status": new_status.value,
            "reason": reason,
        },
    )
    return booking
