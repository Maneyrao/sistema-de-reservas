from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from models.booking import Booking, BookingStatus
from models.staff import Staff
from models.time_block import TimeBlock
from services.timezone_utils import get_business_tz, to_business_tz


class TimeBlockError(Exception):
    pass


class TimeBlockConflictError(TimeBlockError):
    pass


class TimeBlockNotFoundError(TimeBlockError):
    pass


def has_time_block_overlap(
    session: Session,
    *,
    business_id: int,
    staff_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
    exclude_block_id: int | None = None,
) -> bool:
    tz = get_business_tz(session, business_id)
    start_datetime = to_business_tz(start_datetime, tz)
    end_datetime = to_business_tz(end_datetime, tz)

    stmt = select(TimeBlock).where(
        TimeBlock.business_id == business_id,
        TimeBlock.start_datetime < end_datetime,
        TimeBlock.end_datetime > start_datetime,
        or_(TimeBlock.staff_id.is_(None), TimeBlock.staff_id == staff_id),
    )
    if exclude_block_id is not None:
        stmt = stmt.where(TimeBlock.id != exclude_block_id)

    return session.execute(stmt).scalar_one_or_none() is not None


def list_time_blocks(
    session: Session,
    *,
    business_id: int,
    date_from: datetime,
    date_to: datetime,
    staff_id: int | None = None,
) -> list[TimeBlock]:
    tz = get_business_tz(session, business_id)
    date_from = to_business_tz(date_from, tz)
    date_to = to_business_tz(date_to, tz)

    stmt = select(TimeBlock).where(
        TimeBlock.business_id == business_id,
        TimeBlock.start_datetime < date_to,
        TimeBlock.end_datetime > date_from,
    )

    if staff_id is not None:
        stmt = stmt.where(or_(TimeBlock.staff_id.is_(None), TimeBlock.staff_id == staff_id))

    return session.execute(stmt.order_by(TimeBlock.start_datetime)).scalars().all()


def create_time_block(
    session: Session,
    *,
    business_id: int,
    staff_id: int | None,
    start_datetime: datetime,
    end_datetime: datetime,
    reason: str | None,
    notes: str | None,
    created_by_admin_id: int,
) -> TimeBlock:
    tz = get_business_tz(session, business_id)
    start_datetime = to_business_tz(start_datetime, tz)
    end_datetime = to_business_tz(end_datetime, tz)

    if end_datetime <= start_datetime:
        raise TimeBlockError("Block end_datetime must be greater than start_datetime")

    if staff_id is not None:
        staff = session.execute(
            select(Staff).where(
                Staff.id == staff_id,
                Staff.business_id == business_id,
                Staff.active.is_(True),
            )
        ).scalar_one_or_none()
        if not staff:
            raise TimeBlockError("Staff not found in this business")

    booking_stmt = select(Booking).where(
        Booking.business_id == business_id,
        Booking.status.in_([BookingStatus.pending, BookingStatus.confirmed]),
        Booking.start_datetime < end_datetime,
        Booking.end_datetime > start_datetime,
    )
    if staff_id is not None:
        booking_stmt = booking_stmt.where(Booking.staff_id == staff_id)

    booking_conflict = session.execute(booking_stmt).scalar_one_or_none()
    if booking_conflict is not None:
        raise TimeBlockConflictError("Cannot create block over existing active bookings")

    block = TimeBlock(
        business_id=business_id,
        staff_id=staff_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        reason=reason.strip() if reason else None,
        notes=notes.strip() if notes else None,
        created_by_admin_id=created_by_admin_id,
    )
    session.add(block)
    return block


def delete_time_block(
    session: Session,
    *,
    business_id: int,
    block_id: int,
) -> TimeBlock:
    block = session.execute(
        select(TimeBlock).where(
            TimeBlock.id == block_id,
            TimeBlock.business_id == business_id,
        )
    ).scalar_one_or_none()
    if not block:
        raise TimeBlockNotFoundError("Time block not found")

    session.delete(block)
    return block
