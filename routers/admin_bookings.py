from datetime import date, datetime

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.session import get_db
from dependencies.admin_auth import get_current_admin_user
from models.admin_user import AdminUser
from models.booking import BookingStatus
from schemas.admin_booking import (
    AdminBookingOut,
    AdminCancelBookingRequest,
    AdminCreateBookingRequest,
    AdminRescheduleBookingRequest,
    AdminUpdateStatusRequest,
)
from schemas.pagination import PaginatedResponse
from routers.ws import ws_manager


def _fire_broadcast(business_id: int, event: dict) -> None:
    """Lanza broadcast WS en fire-and-forget desde handlers síncronos."""
    try:
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(ws_manager.broadcast(business_id, event), loop=loop)
    except Exception:
        pass
from services.admin_booking_service import (
    AdminBookingConflictError,
    AdminBookingError,
    cancel_booking_by_admin,
    create_booking_by_admin,
    get_booking_detail,
    list_bookings_for_range,
    reschedule_booking_by_admin,
    update_booking_status_by_admin,
)
from services.booking_service import BookingNotFound
from services.timezone_utils import get_business_tz, to_business_tz


router = APIRouter(prefix="/admin/bookings", tags=["Admin Bookings"])


def _parse_status_filters(raw_statuses: list[str] | None) -> list[BookingStatus] | None:
    if not raw_statuses:
        return None

    parsed: list[BookingStatus] = []
    valid_values = {item.value: item for item in BookingStatus}
    for raw in raw_statuses:
        normalized = raw.strip().lower()
        normalized = "canceled" if normalized == "cancelled" else normalized
        status_item = valid_values.get(normalized)
        if status_item is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{raw}'. Allowed: {[k for k in valid_values]}",
            )
        parsed.append(status_item)
    return parsed


@router.get("", status_code=status.HTTP_200_OK)
def admin_list_bookings(
    date_from: date = Query(...),
    date_to: date = Query(...),
    status_filter: list[str] | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1, description="Página (1-based)"),
    page_size: int = Query(default=50, ge=1, le=200, description="Registros por página"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
) -> PaginatedResponse[AdminBookingOut]:
    if date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_to must be greater than or equal to date_from",
        )
    if (date_to - date_from).days > 31:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agenda date range cannot exceed 31 days",
        )

    parsed_statuses = _parse_status_filters(status_filter)
    result = list_bookings_for_range(
        session=db,
        business_id=current_admin.business_id,
        date_from=date_from,
        date_to=date_to,
        statuses=parsed_statuses,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse.build(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.post("", response_model=AdminBookingOut, status_code=status.HTTP_201_CREATED)
def admin_create_booking(
    payload: AdminCreateBookingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    normalized_status = payload.status.strip().lower()
    valid_statuses = {
        BookingStatus.pending.value: BookingStatus.pending,
        BookingStatus.confirmed.value: BookingStatus.confirmed,
    }
    if normalized_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin can only create pending or confirmed bookings",
        )

    tz = get_business_tz(db, current_admin.business_id)
    start_datetime = datetime.combine(payload.date, payload.time, tzinfo=tz)

    try:
        booking = create_booking_by_admin(
            session=db,
            business_id=current_admin.business_id,
            staff_slug=payload.staff_slug,
            service_slug=payload.service_slug,
            first_name=payload.customer.first_name,
            last_name=payload.customer.last_name,
            phone=payload.customer.phone,
            email=payload.customer.email,
            start_datetime=start_datetime,
            admin_user_id=current_admin.id,
            notes=payload.notes,
            status=valid_statuses[normalized_status],
        )
        item = get_booking_detail(
            db,
            business_id=current_admin.business_id,
            booking_id=booking.id,
        )
        db.commit()
    except AdminBookingConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AdminBookingError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if item is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Booking serialization error")

    background_tasks.add_task(
        _fire_broadcast,
        current_admin.business_id,
        {"event": "booking_created", "booking_id": booking.id, "data": item},
    )
    return item


@router.post("/{booking_id}/cancel", response_model=AdminBookingOut, status_code=status.HTTP_200_OK)
def admin_cancel_booking(
    booking_id: int,
    payload: AdminCancelBookingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    tz = get_business_tz(db, current_admin.business_id)
    try:
        booking = cancel_booking_by_admin(
            session=db,
            business_id=current_admin.business_id,
            booking_id=booking_id,
            reason=payload.reason,
            admin_user_id=current_admin.id,
        )
        result = list_bookings_for_range(
            session=db,
            business_id=current_admin.business_id,
            date_from=to_business_tz(booking.start_datetime, tz).date(),
            date_to=to_business_tz(booking.start_datetime, tz).date(),
        )
        db.commit()
    except BookingNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AdminBookingError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    for row in result["items"]:
        if row["id"] == booking.id:
            background_tasks.add_task(
                _fire_broadcast,
                current_admin.business_id,
                {"event": "booking_cancelled", "booking_id": booking.id},
            )
            return row
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Booking serialization error")


@router.post("/{booking_id}/reschedule", response_model=AdminBookingOut, status_code=status.HTTP_200_OK)
def admin_reschedule_booking(
    booking_id: int,
    payload: AdminRescheduleBookingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    tz = get_business_tz(db, current_admin.business_id)
    new_start_datetime = datetime.combine(payload.new_date, payload.new_time, tzinfo=tz)

    try:
        new_booking = reschedule_booking_by_admin(
            session=db,
            business_id=current_admin.business_id,
            booking_id=booking_id,
            new_start_datetime=new_start_datetime,
            reason=payload.reason,
            admin_user_id=current_admin.id,
        )
        rows = list_bookings_for_range(
            session=db,
            business_id=current_admin.business_id,
            date_from=payload.new_date,
            date_to=payload.new_date,
        )
        db.commit()
    except BookingNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AdminBookingConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AdminBookingError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    for row in rows["items"]:
        if row["id"] == new_booking.id:
            background_tasks.add_task(
                _fire_broadcast,
                current_admin.business_id,
                {"event": "booking_rescheduled", "booking_id": booking_id, "new_booking_id": new_booking.id},
            )
            return row
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Booking serialization error")


@router.patch("/{booking_id}/status", response_model=AdminBookingOut, status_code=status.HTTP_200_OK)
def admin_update_booking_status(
    booking_id: int,
    payload: AdminUpdateStatusRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    normalized = payload.status.strip().lower()
    normalized = "canceled" if normalized == "cancelled" else normalized

    valid_values = {item.value: item for item in BookingStatus}
    if normalized not in valid_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'",
        )

    tz = get_business_tz(db, current_admin.business_id)
    try:
        booking = update_booking_status_by_admin(
            session=db,
            business_id=current_admin.business_id,
            booking_id=booking_id,
            new_status=valid_values[normalized],
            admin_user_id=current_admin.id,
            reason=payload.reason,
        )
        rows = list_bookings_for_range(
            session=db,
            business_id=current_admin.business_id,
            date_from=to_business_tz(booking.start_datetime, tz).date(),
            date_to=to_business_tz(booking.start_datetime, tz).date(),
        )
        db.commit()
    except BookingNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AdminBookingError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    for row in rows:
        if row["id"] == booking.id:
            return row
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Booking serialization error")
