from datetime import timedelta
from uuid import uuid4
from datetime import datetime, time
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from models.booking import Booking, BookingStatus
from models.service import Service


class SlotNotAvailable(Exception):
    pass


class BookingNotFound(Exception):
    pass


class InvalidService(Exception):
    pass


def _overlaps(start_a, end_a, start_b, end_b) -> bool:
    return start_a < end_b and start_b < end_a


def _create_booking_internal(
    session: Session,
    *,
    business_id: int,
    staff_id: int,
    service_id: int,
    customer_id: int,
    start_datetime,
) -> Booking:
    # 1) Validar que el servicio exista y pertenezca al business
    service = session.execute(
        select(Service).where(
            and_(
                Service.id == service_id,
                Service.business_id == business_id,
            )
        )
    ).scalar_one_or_none()

    if not service:
        raise InvalidService("El servicio no existe o no pertenece al negocio")

    duration = timedelta(minutes=service.duration_minutes)
    end_datetime = start_datetime + duration

    # 2) Lock de posibles conflictos (concurrencia real)
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


def create_booking(
    session: Session,
    *,
    business_id: int,
    staff_id: int,
    service_id: int,
    customer_id: int,
    start_datetime,
) -> Booking:
    with session.begin():
        return _create_booking_internal(
            session,
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
    with session.begin():
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
    new_start_datetime,
) -> Booking:
    with session.begin():
        booking = session.execute(
            select(Booking).where(Booking.id == booking_id)
        ).scalar_one_or_none()

        if not booking:
            raise BookingNotFound("Booking no encontrado")

        # Cancelamos el booking actual (historial)
        booking.status = BookingStatus.canceled

        # Creamos el nuevo dentro de LA MISMA transacción
        new_booking = _create_booking_internal(
            session=session,
            business_id=booking.business_id,
            staff_id=booking.staff_id,
            service_id=booking.service_id,
            customer_id=booking.customer_id,
            start_datetime=new_start_datetime,
        )

        return new_booking
    
def get_business_bookings_by_date(
    session: Session,
    *,
    business_id: int,
    day,
    staff_id: int | None = None,
):
    day_start = datetime.combine(day, time.min)
    day_end = datetime.combine(day, time.max)

    conditions = [
        Booking.business_id == business_id,
        Booking.start_datetime >= day_start,
        Booking.start_datetime <= day_end,
        Booking.status == BookingStatus.confirmed,
    ]

    if staff_id is not None:
        conditions.append(Booking.staff_id == staff_id)

    bookings = session.execute(
        select(Booking)
        .where(and_(*conditions))
        .order_by(Booking.start_datetime)
    ).scalars().all()

    return bookings
