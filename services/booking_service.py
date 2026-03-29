from datetime import datetime, time, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from models.availability import AvailabilityRule
from models.booking import Booking, BookingStatus
from models.customer import Customer
from models.service import Service
from models.staff import Staff
from models.staff_service import StaffService
from services.time_block_service import has_time_block_overlap
from services.time_utils import STEP_MINUTES, is_step_aligned, overlaps, to_tz
from services.timezone_utils import get_business_tz


class SlotNotAvailable(Exception):
    pass


class BookingNotFound(Exception):
    pass


class InvalidService(Exception):
    pass


class InvalidBookingRequest(Exception):
    pass


def normalize_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not digits:
        return ""
    return f"+{digits}"


def build_email_fallback(normalized_phone: str) -> str:
    digits = "".join(ch for ch in normalized_phone if ch.isdigit())
    return f"tel_{digits}@booking.local"


def _overlaps_tz(
    start_a: datetime,
    end_a: datetime,
    start_b: datetime,
    end_b: datetime,
    tz: ZoneInfo,
) -> bool:
    """
    Compara intervalos semiabiertos normalizando al timezone del negocio primero.
    Usa overlaps() de time_utils internamente.
    """
    return overlaps(to_tz(start_a, tz), to_tz(end_a, tz), to_tz(start_b, tz), to_tz(end_b, tz))


def _is_inside_staff_availability(
    session: Session,
    *,
    business_id: int,
    staff_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
) -> bool:
    if start_datetime.date() != end_datetime.date():
        return False

    weekday = start_datetime.weekday()
    start_time = start_datetime.timetz().replace(tzinfo=None)
    end_time = end_datetime.timetz().replace(tzinfo=None)

    rules = session.execute(
        select(AvailabilityRule)
        .join(Staff, AvailabilityRule.staff_id == Staff.id)
        .where(
            AvailabilityRule.staff_id == staff_id,
            AvailabilityRule.weekday == weekday,
            Staff.business_id == business_id,
            Staff.active.is_(True),
        )
    ).scalars().all()

    return any(
        rule.start_time <= start_time and rule.end_time >= end_time
        for rule in rules
    )


def staff_offers_service(
    session: Session,
    *,
    staff_id: int,
    service_id: int,
) -> bool:
    assignment = session.execute(
        select(StaffService).where(
            StaffService.staff_id == staff_id,
            StaffService.service_id == service_id,
        )
    ).scalar_one_or_none()
    return assignment is not None


def resolve_customer(
    session: Session,
    *,
    first_name: str,
    last_name: str,
    phone: str,
    email: str | None = None,
) -> Customer:
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        raise InvalidBookingRequest("Customer phone is required.")

    clean_first_name = first_name.strip()
    clean_last_name = last_name.strip()
    if not clean_first_name or not clean_last_name:
        raise InvalidBookingRequest("Customer first_name and last_name are required.")

    full_name = f"{clean_first_name} {clean_last_name}".strip()
    normalized_email = email.lower().strip() if email else None
    resolved_email = normalized_email or build_email_fallback(normalized_phone)

    customer = session.execute(
        select(Customer).where(Customer.phone == normalized_phone)
    ).scalar_one_or_none()

    if customer is None:
        customer = session.execute(
            select(Customer).where(Customer.email == resolved_email)
        ).scalar_one_or_none()

    if customer is None:
        customer = Customer(
            name=full_name,
            email=resolved_email,
            phone=normalized_phone,
        )
        session.add(customer)
        session.flush()
        return customer

    customer.name = full_name
    customer.email = resolved_email
    customer.phone = normalized_phone
    session.add(customer)
    session.flush()
    return customer


def _create_booking_internal(
    session: Session,
    *,
    business_id: int,
    staff_id: int,
    service_id: int,
    customer_id: int,
    start_datetime: datetime,
    idempotency_key: str | None = None,
    notes: str | None = None,
    status: BookingStatus = BookingStatus.confirmed,
    rescheduled_from_booking_id: int | None = None,
) -> Booking:
    tz = get_business_tz(session, business_id)

    service = session.execute(
        select(Service).where(
            Service.id == service_id,
            Service.business_id == business_id,
            Service.active.is_(True),
        )
    ).scalar_one_or_none()
    if not service:
        raise InvalidService("El servicio no existe o no pertenece al negocio")

    staff = session.execute(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.business_id == business_id,
            Staff.active.is_(True),
        )
    ).scalar_one_or_none()
    if not staff:
        raise InvalidService("El staff no existe o no pertenece al negocio")

    if not staff_offers_service(
        session,
        staff_id=staff.id,
        service_id=service.id,
    ):
        raise InvalidBookingRequest("El staff seleccionado no ofrece ese servicio.")

    start_datetime = to_tz(start_datetime, tz)
    if not is_step_aligned(start_datetime):
        raise InvalidBookingRequest("El horario debe respetar bloques de 15 minutos exactos.")

    duration = timedelta(minutes=service.duration_minutes)
    end_datetime = start_datetime + duration

    if not _is_inside_staff_availability(
        session,
        business_id=business_id,
        staff_id=staff_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    ):
        raise InvalidBookingRequest("El horario elegido esta fuera de la disponibilidad del staff.")

    if has_time_block_overlap(
        session,
        business_id=business_id,
        staff_id=staff_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    ):
        raise InvalidBookingRequest("El horario elegido cae dentro de un bloqueo de agenda.")

    conflicting_bookings = session.execute(
        select(Booking)
        .where(
            and_(
                Booking.staff_id == staff_id,
                Booking.status.in_([BookingStatus.pending, BookingStatus.confirmed]),
                Booking.start_datetime < end_datetime,
                Booking.end_datetime > start_datetime,
            )
        )
        .with_for_update()
    ).scalars().all()

    for booking in conflicting_bookings:
        if _overlaps_tz(start_datetime, end_datetime, booking.start_datetime, booking.end_datetime, tz):
            raise SlotNotAvailable("El horario ya no esta disponible")

    booking = Booking(
        business_id=business_id,
        staff_id=staff_id,
        service_id=service_id,
        customer_id=customer_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        status=status,
        public_token=uuid4().hex,
        idempotency_key=idempotency_key,
        notes=notes,
        rescheduled_from_booking_id=rescheduled_from_booking_id,
    )
    session.add(booking)
    return booking


def create_booking(
    session: Session,
    *,
    business_id: int,
    staff_id: int,
    service_id: int,
    customer_id: int,
    start_datetime: datetime,
    idempotency_key: str | None = None,
    notes: str | None = None,
    status: BookingStatus = BookingStatus.confirmed,
    rescheduled_from_booking_id: int | None = None,
) -> Booking:
    """
    Crea una reserva.
    Asume que la transaccion ya esta abierta en el router.
    """
    return _create_booking_internal(
        session=session,
        business_id=business_id,
        staff_id=staff_id,
        service_id=service_id,
        customer_id=customer_id,
        start_datetime=start_datetime,
        idempotency_key=idempotency_key,
        notes=notes,
        status=status,
        rescheduled_from_booking_id=rescheduled_from_booking_id,
    )


def get_booking_by_idempotency_key(
    session: Session,
    *,
    business_id: int,
    idempotency_key: str,
) -> Booking | None:
    return session.execute(
        select(Booking).where(
            Booking.business_id == business_id,
            Booking.idempotency_key == idempotency_key,
        )
    ).scalar_one_or_none()


def cancel_booking(
    session: Session,
    *,
    booking_id: int,
    reason: str | None = None,
) -> Booking:
    booking = session.execute(
        select(Booking).where(Booking.id == booking_id)
    ).scalar_one_or_none()

    if not booking:
        raise BookingNotFound("Booking no encontrado")

    if booking.status == BookingStatus.canceled:
        return booking

    now = datetime.now(timezone.utc)
    booking.status = BookingStatus.canceled
    booking.canceled_reason = reason.strip() if reason else booking.canceled_reason
    booking.canceled_at = now
    booking.updated_at = now
    return booking


def reschedule_booking(
    session: Session,
    *,
    booking_id: int,
    new_start_datetime: datetime,
    reason: str | None = None,
) -> Booking:
    booking = session.execute(
        select(Booking).where(Booking.id == booking_id)
    ).scalar_one_or_none()

    if not booking:
        raise BookingNotFound("Booking no encontrado")

    now = datetime.now(timezone.utc)
    booking.status = BookingStatus.canceled
    booking.canceled_reason = reason.strip() if reason else "rescheduled"
    booking.canceled_at = now
    booking.updated_at = now

    return _create_booking_internal(
        session=session,
        business_id=booking.business_id,
        staff_id=booking.staff_id,
        service_id=booking.service_id,
        customer_id=booking.customer_id,
        start_datetime=new_start_datetime,
        notes=booking.notes,
        rescheduled_from_booking_id=booking.id,
    )


def get_business_bookings_by_date(
    session: Session,
    *,
    business_id: int,
    day,
    staff_id: int | None = None,
) -> list[Booking]:
    tz = get_business_tz(session, business_id)
    day_start = datetime.combine(day, time.min, tzinfo=tz)
    day_end = datetime.combine(day, time.max, tzinfo=tz)

    conditions = [
        Booking.business_id == business_id,
        Booking.start_datetime >= day_start,
        Booking.start_datetime <= day_end,
        Booking.status.in_([BookingStatus.pending, BookingStatus.confirmed]),
    ]

    if staff_id is not None:
        conditions.append(Booking.staff_id == staff_id)

    return session.execute(
        select(Booking)
        .where(and_(*conditions))
        .order_by(Booking.start_datetime)
    ).scalars().all()


def get_bookings_pending_reminder(
    session: Session,
    *,
    now: datetime | None = None,
    hours_ahead: int = 2,
    window_minutes: int = 1,
) -> list[tuple[Booking, str, str, str]]:
    reference_now = now or datetime.now(timezone.utc)
    target_start = (reference_now + timedelta(hours=hours_ahead)).replace(second=0, microsecond=0)
    target_end = target_start + timedelta(minutes=window_minutes)

    rows = session.execute(
        select(Booking, Customer.phone, Customer.name, Service.name)
        .join(Customer, Customer.id == Booking.customer_id)
        .join(Service, Service.id == Booking.service_id)
        .where(
            Booking.status == BookingStatus.confirmed,
            Booking.reminder_sent_at.is_(None),
            Booking.start_datetime >= target_start,
            Booking.start_datetime < target_end,
            Customer.phone.is_not(None),
            Customer.phone != "",
        )
        .order_by(Booking.start_datetime)
    ).all()

    return [
        (booking, phone, customer_name, service_name)
        for booking, phone, customer_name, service_name in rows
    ]


def mark_booking_reminder_sent(
    session: Session,
    *,
    booking: Booking,
    sent_at: datetime | None = None,
) -> None:
    now = datetime.now(timezone.utc)
    booking.reminder_sent_at = sent_at or now
    booking.updated_at = now
    session.add(booking)
