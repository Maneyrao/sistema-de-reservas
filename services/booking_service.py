from datetime import datetime, timedelta, time
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from models.booking import Booking, BookingStatus
from models.service import Service
from models.staff import Staff


BUSINESS_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


# --------------------
# Exceptions
# --------------------

class SlotNotAvailable(Exception):
    pass


class BookingNotFound(Exception):
    pass


class InvalidService(Exception):
    pass


# --------------------
# Utils
# --------------------

def _overlaps(start_a, end_a, start_b, end_b) -> bool:
    """
    Intervalos semiabiertos: [start, end)
    """
    return start_a < end_b and start_b < end_a


# --------------------
# Core booking logic
# --------------------

def _create_booking_internal(
    session: Session,
    *,
    business_id: int,
    staff_id: int,
    service_id: int,
    customer_id: int,
    start_datetime: datetime,
) -> Booking:
    # 1️⃣ Validar servicio (multi-tenant)
    service = session.execute(
        select(Service).where(
            Service.id == service_id,
            Service.business_id == business_id,
            Service.active.is_(True),
        )
    ).scalar_one_or_none()

    if not service:
        raise InvalidService("El servicio no existe o no pertenece al negocio")

    # 2️⃣ Validar staff (multi-tenant)
    staff = session.execute(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.business_id == business_id,
            Staff.active.is_(True),
        )
    ).scalar_one_or_none()

    if not staff:
        raise InvalidService("El staff no existe o no pertenece al negocio")

    # 3️⃣ Calcular duración
    duration = timedelta(minutes=service.duration_minutes)
    end_datetime = start_datetime + duration

    # 4️⃣ Lock de conflictos (concurrencia real)
    conflicting_bookings = session.execute(
        select(Booking)
        .where(
            and_(
                Booking.staff_id == staff_id,
                Booking.status == BookingStatus.confirmed,
                Booking.start_datetime < end_datetime,
                Booking.end_datetime > start_datetime,
            )
        )
        .with_for_update()
    ).scalars().all()

    for b in conflicting_bookings:
        if _overlaps(start_datetime, end_datetime, b.start_datetime, b.end_datetime):
            raise SlotNotAvailable("El horario ya no está disponible")

    # 5️⃣ Crear booking
    booking = Booking(
        business_id=business_id,
        staff_id=staff_id,
        service_id=service_id,
        customer_id=customer_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        status=BookingStatus.confirmed,
        public_token=uuid4().hex,
    )

    session.add(booking)
    return booking


# --------------------
# Public API
# --------------------

def create_booking(
    session: Session,
    *,
    business_id: int,
    staff_id: int,
    service_id: int,
    customer_id: int,
    start_datetime: datetime,
) -> Booking:
    """
    Crea una reserva.
    Asume que la transacción ya está abierta en el router.
    """
    return _create_booking_internal(
        session=session,
        business_id=business_id,
        staff_id=staff_id,
        service_id=service_id,
        customer_id=customer_id,
        start_datetime=start_datetime,
    )


def cancel_booking(
    session: Session,
    *,
    booking_id: int,
) -> Booking:
    """
    Cancela una reserva existente.
    """
    booking = session.execute(
        select(Booking).where(Booking.id == booking_id)
    ).scalar_one_or_none()

    if not booking:
        raise BookingNotFound("Booking no encontrado")

    if booking.status == BookingStatus.canceled:
        return booking  # idempotente

    booking.status = BookingStatus.canceled
    return booking


def reschedule_booking(
    session: Session,
    *,
    booking_id: int,
    new_start_datetime: datetime,
) -> Booking:
    """
    Reprograma una reserva:
    - Cancela la actual
    - Crea una nueva en la misma transacción
    """
    booking = session.execute(
        select(Booking).where(Booking.id == booking_id)
    ).scalar_one_or_none()

    if not booking:
        raise BookingNotFound("Booking no encontrado")

    # Cancelamos el booking actual (historial)
    booking.status = BookingStatus.canceled

    # Creamos el nuevo (misma transacción)
    return _create_booking_internal(
        session=session,
        business_id=booking.business_id,
        staff_id=booking.staff_id,
        service_id=booking.service_id,
        customer_id=booking.customer_id,
        start_datetime=new_start_datetime,
    )


def get_business_bookings_by_date(
    session: Session,
    *,
    business_id: int,
    day,
    staff_id: int | None = None,
):
    """
    Devuelve bookings confirmados de un negocio en un día específico.
    """
    day_start = datetime.combine(day, time.min, tzinfo=BUSINESS_TZ)
    day_end = datetime.combine(day, time.max, tzinfo=BUSINESS_TZ)

    conditions = [
        Booking.business_id == business_id,
        Booking.start_datetime >= day_start,
        Booking.start_datetime <= day_end,
        Booking.status == BookingStatus.confirmed,
    ]

    if staff_id is not None:
        conditions.append(Booking.staff_id == staff_id)

    return session.execute(
        select(Booking)
        .where(and_(*conditions))
        .order_by(Booking.start_datetime)
    ).scalars().all()
