from datetime import date, datetime, time, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from models.availability import AvailabilityRule
from models.booking import Booking, BookingStatus
from models.service import Service
from models.staff import Staff
from models.time_block import TimeBlock
from services.booking_service import staff_offers_service
from services.time_utils import STEP_MINUTES, overlaps
from services.timezone_utils import get_business_tz, to_business_tz


def get_available_slots(
    session: Session,
    business_id: int,
    service_slug: str,
    date_from: date,
    date_to: date,
    staff_slug: str | None = None,
) -> list[dict]:
    """
    Devuelve slots disponibles para un negocio y servicio.
    Si staff_slug es None, devuelve disponibilidad general.
    """

    tz = get_business_tz(session, business_id)

    # 1️⃣ Resolver servicio (boundary multi-tenant)
    service = session.execute(
        select(Service).where(
            Service.slug == service_slug,
            Service.business_id == business_id,
            Service.active.is_(True),
        )
    ).scalar_one_or_none()

    if not service:
        raise ValueError("Service not found in this business")

    duration = timedelta(minutes=service.duration_minutes)
    step = timedelta(minutes=STEP_MINUTES)

    # 2️⃣ Resolver staff opcional
    staff: Staff | None = None
    if staff_slug:
        staff = session.execute(
            select(Staff).where(
                Staff.slug == staff_slug,
                Staff.business_id == business_id,
                Staff.active.is_(True),
            )
        ).scalar_one_or_none()

        if not staff:
            raise ValueError("Staff not found in this business")
        if not staff_offers_service(
            session,
            staff_id=staff.id,
            service_id=service.id,
        ):
            raise ValueError("Staff does not offer this service")

    # 3️⃣ Obtener reglas de disponibilidad
    # AvailabilityRule NO tiene business_id → se filtra vía Staff
    rules_stmt = (
        select(AvailabilityRule)
        .join(Staff, AvailabilityRule.staff_id == Staff.id)
        .where(Staff.business_id == business_id)
    )

    if staff:
        rules_stmt = rules_stmt.where(AvailabilityRule.staff_id == staff.id)

    rules = session.execute(rules_stmt).scalars().all()

    if not rules:
        return []

    slots_set: set[tuple[datetime, datetime]] = set()

    current_date = date_from
    while current_date <= date_to:
        weekday = current_date.weekday()
        day_rules = [r for r in rules if r.weekday == weekday]

        if not day_rules:
            current_date += timedelta(days=1)
            continue

        day_start = datetime.combine(current_date, time.min, tzinfo=tz)
        day_end = datetime.combine(current_date, time.max, tzinfo=tz)

        # 4️⃣ Bookings activos del dia
        bookings_stmt = select(Booking).where(
            Booking.business_id == business_id,
            Booking.status.in_([BookingStatus.pending, BookingStatus.confirmed]),
            Booking.start_datetime < day_end,
            Booking.end_datetime > day_start,
        )

        if staff:
            bookings_stmt = bookings_stmt.where(Booking.staff_id == staff.id)

        bookings = session.execute(bookings_stmt).scalars().all()

        blocks_stmt = select(TimeBlock).where(
            TimeBlock.business_id == business_id,
            TimeBlock.start_datetime < day_end,
            TimeBlock.end_datetime > day_start,
        )
        if staff:
            blocks_stmt = blocks_stmt.where(
                or_(TimeBlock.staff_id.is_(None), TimeBlock.staff_id == staff.id)
            )
        blocks = session.execute(blocks_stmt).scalars().all()

        # 5️⃣ Generación de slots
        for rule in day_rules:
            window_start = datetime.combine(
                current_date, rule.start_time, tzinfo=tz
            )
            window_end = datetime.combine(
                current_date, rule.end_time, tzinfo=tz
            )

            if window_end - window_start < duration:
                continue

            t = window_start
            while t + duration <= window_end:
                candidate_start = t
                candidate_end = t + duration

                if any(
                    overlaps(
                        candidate_start,
                        candidate_end,
                        to_business_tz(b.start_datetime, tz),
                        to_business_tz(b.end_datetime, tz),
                    )
                    for b in bookings
                ):
                    t += step
                    continue

                if any(
                    overlaps(
                        candidate_start,
                        candidate_end,
                        to_business_tz(block.start_datetime, tz),
                        to_business_tz(block.end_datetime, tz),
                    )
                    for block in blocks
                ):
                    t += step
                    continue

                slots_set.add((candidate_start, candidate_end))
                t += step

        current_date += timedelta(days=1)

    return [
        {"start": start, "end": end}
        for start, end in sorted(slots_set)
    ]
