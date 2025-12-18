from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from models.availability import AvailabilityRule
from models.service import Service
from models.booking import Booking, BookingStatus


STEP_MINUTES = 15
BUSINESS_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def _overlaps(start_a, end_a, start_b, end_b) -> bool:
    """
    Intervalos semiabiertos: [start, end)
    """
    return start_a < end_b and start_b < end_a


def get_available_slots(
    session: Session,
    staff_id: int,
    service_id: int,
    date_from: date,
    date_to: date,
) -> list[dict]:
    """
    Devuelve una lista de slots disponibles para un staff y servicio
    en un rango de fechas.
    """

    service = session.execute(
        select(Service).where(Service.id == service_id)
    ).scalar_one()

    duration = timedelta(minutes=service.duration_minutes)
    step = timedelta(minutes=STEP_MINUTES)

    # Usamos set para evitar duplicados (rules superpuestas)
    slots_set: set[tuple[datetime, datetime]] = set()

    current_date = date_from
    while current_date <= date_to:
        weekday = current_date.weekday()  # 0 = lunes

        rules = session.execute(
            select(AvailabilityRule).where(
                and_(
                    AvailabilityRule.staff_id == staff_id,
                    AvailabilityRule.weekday == weekday,
                )
            )
        ).scalars().all()

        if not rules:
            current_date += timedelta(days=1)
            continue

        day_start = datetime.combine(
            current_date, time.min, tzinfo=BUSINESS_TZ
        )
        day_end = datetime.combine(
            current_date, time.max, tzinfo=BUSINESS_TZ
        )

        bookings = session.execute(
            select(Booking).where(
                and_(
                    Booking.staff_id == staff_id,
                    Booking.status == BookingStatus.confirmed,
                    Booking.start_datetime < day_end,
                    Booking.end_datetime > day_start,
                )
            )
        ).scalars().all()

        for rule in rules:
            window_start = datetime.combine(
                current_date, rule.start_time, tzinfo=BUSINESS_TZ
            )
            window_end = datetime.combine(
                current_date, rule.end_time, tzinfo=BUSINESS_TZ
            )

            # Optimización: si el servicio no entra, skip
            if window_end - window_start < duration:
                continue

            t = window_start
            while t + duration <= window_end:
                candidate_start = t
                candidate_end = t + duration

                conflict = False
                for booking in bookings:
                    if _overlaps(
                        candidate_start,
                        candidate_end,
                        booking.start_datetime,
                        booking.end_datetime,
                    ):
                        conflict = True
                        break

                if not conflict:
                    slots_set.add((candidate_start, candidate_end))

                t += step

        current_date += timedelta(days=1)

    # Normalizamos salida ordenada
    return [
        {"start": start, "end": end}
        for start, end in sorted(slots_set)
    ]
