"""
Servicio de métricas del negocio.

Proporciona agregaciones para el dashboard administrativo:
- Resumen del día (bookings, cancelaciones, ingresos estimados)
- Comparativa semana actual vs semana anterior
- Ocupación por staff
- Servicios más reservados
"""
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.booking import Booking, BookingStatus
from models.service import Service
from models.staff import Staff
from services.timezone_utils import get_business_tz, to_business_tz


def _day_range(target_date: date, tz) -> tuple[datetime, datetime]:
    return (
        datetime.combine(target_date, time.min, tzinfo=tz),
        datetime.combine(target_date, time.max, tzinfo=tz),
    )


def get_daily_summary(
    session: Session,
    *,
    business_id: int,
    target_date: date | None = None,
) -> dict[str, Any]:
    """Métricas del día: total, confirmadas, canceladas, completadas, ingresos."""
    tz = get_business_tz(session, business_id)
    day = target_date or datetime.now(tz).date()
    day_start, day_end = _day_range(day, tz)

    rows = session.execute(
        select(Booking.status, func.count(Booking.id))
        .where(
            Booking.business_id == business_id,
            Booking.start_datetime >= day_start,
            Booking.start_datetime <= day_end,
        )
        .group_by(Booking.status)
    ).all()

    counts: dict[str, int] = {}
    for row_status, count in rows:
        counts[row_status.value] = count

    total = sum(counts.values())
    confirmed = counts.get("confirmed", 0)
    canceled = counts.get("canceled", 0)
    completed = counts.get("completed", 0)
    pending = counts.get("pending", 0)

    # Ingresos estimados: bookings activos (confirmed + completed) x precio del servicio
    revenue_rows = session.execute(
        select(func.coalesce(func.sum(Service.price_amount), 0))
        .join(Booking, Booking.service_id == Service.id)
        .where(
            Booking.business_id == business_id,
            Booking.start_datetime >= day_start,
            Booking.start_datetime <= day_end,
            Booking.status.in_([BookingStatus.confirmed, BookingStatus.completed]),
        )
    ).scalar_one()

    return {
        "date": day.isoformat(),
        "total": total,
        "confirmed": confirmed,
        "pending": pending,
        "canceled": canceled,
        "completed": completed,
        "estimated_revenue": int(revenue_rows or 0),
    }


def get_weekly_comparison(
    session: Session,
    *,
    business_id: int,
    reference_date: date | None = None,
) -> dict[str, Any]:
    """
    Compara la semana actual con la semana anterior.
    Devuelve totales por semana y variación porcentual.
    """
    tz = get_business_tz(session, business_id)
    today = reference_date or datetime.now(tz).date()

    # Semana actual: lunes hasta hoy
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # Semana anterior
    prev_week_start = week_start - timedelta(days=7)
    prev_week_end = week_start - timedelta(days=1)

    def _count_for_range(start: date, end: date) -> int:
        d_start, _ = _day_range(start, tz)
        _, d_end = _day_range(end, tz)
        return session.execute(
            select(func.count(Booking.id)).where(
                Booking.business_id == business_id,
                Booking.start_datetime >= d_start,
                Booking.start_datetime <= d_end,
                Booking.status.in_([BookingStatus.confirmed, BookingStatus.completed]),
            )
        ).scalar_one()

    current_count = _count_for_range(week_start, week_end)
    prev_count = _count_for_range(prev_week_start, prev_week_end)

    change_pct: float | None = None
    if prev_count > 0:
        change_pct = round(((current_count - prev_count) / prev_count) * 100, 1)

    return {
        "current_week": {
            "start": week_start.isoformat(),
            "end": week_end.isoformat(),
            "bookings": current_count,
        },
        "previous_week": {
            "start": prev_week_start.isoformat(),
            "end": prev_week_end.isoformat(),
            "bookings": prev_count,
        },
        "change_pct": change_pct,
    }


def get_staff_occupancy(
    session: Session,
    *,
    business_id: int,
    target_date: date | None = None,
) -> list[dict[str, Any]]:
    """Ocupación por staff para el día dado (número de bookings activos)."""
    tz = get_business_tz(session, business_id)
    day = target_date or datetime.now(tz).date()
    day_start, day_end = _day_range(day, tz)

    rows = session.execute(
        select(Staff.id, Staff.name, Staff.slug, func.count(Booking.id))
        .outerjoin(
            Booking,
            (Booking.staff_id == Staff.id)
            & (Booking.start_datetime >= day_start)
            & (Booking.start_datetime <= day_end)
            & (Booking.status.in_([BookingStatus.confirmed, BookingStatus.completed])),
        )
        .where(Staff.business_id == business_id, Staff.active.is_(True))
        .group_by(Staff.id, Staff.name, Staff.slug)
        .order_by(func.count(Booking.id).desc())
    ).all()

    return [
        {"staff_id": staff_id, "staff_name": name, "staff_slug": slug, "bookings": count}
        for staff_id, name, slug, count in rows
    ]


def get_top_services(
    session: Session,
    *,
    business_id: int,
    days: int = 30,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Servicios más reservados en los últimos N días."""
    tz = get_business_tz(session, business_id)
    today = datetime.now(tz).date()
    period_start, _ = _day_range(today - timedelta(days=days - 1), tz)
    _, period_end = _day_range(today, tz)

    rows = session.execute(
        select(Service.id, Service.name, Service.slug, func.count(Booking.id))
        .join(Booking, Booking.service_id == Service.id)
        .where(
            Service.business_id == business_id,
            Booking.start_datetime >= period_start,
            Booking.start_datetime <= period_end,
            Booking.status.in_([BookingStatus.confirmed, BookingStatus.completed]),
        )
        .group_by(Service.id, Service.name, Service.slug)
        .order_by(func.count(Booking.id).desc())
        .limit(limit)
    ).all()

    return [
        {"service_id": svc_id, "service_name": name, "service_slug": slug, "bookings": count}
        for svc_id, name, slug, count in rows
    ]
