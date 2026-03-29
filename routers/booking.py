import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.session import get_db
from schemas.booking import BookingCreate
from models.business import Business
from models.staff import Staff
from models.service import Service
from models.customer import Customer
from services.booking_service import (
    build_email_fallback,
    create_booking,
    get_booking_by_idempotency_key,
    InvalidBookingRequest,
    normalize_phone,
    resolve_customer,
    SlotNotAvailable,
)
from services.timezone_utils import get_business_tz, to_business_tz

# ---------------------------------------------------------
# Configuracion
# ---------------------------------------------------------

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/business",
    tags=["Bookings"]
)
limiter = Limiter(key_func=get_remote_address)

def _normalize_idempotency_key(raw_key: str | None) -> str | None:
    if raw_key is None:
        return None
    normalized = raw_key.strip()
    if not normalized:
        return None
    if len(normalized) > 120:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key exceeds 120 chars.",
        )
    return normalized


def _serialize_booking_response(
    db: Session,
    *,
    business: Business,
    booking,
) -> dict:
    tz = get_business_tz(db, business.id)

    staff = db.query(Staff).filter(
        Staff.id == booking.staff_id,
        Staff.business_id == business.id,
    ).first()
    service = db.query(Service).filter(
        Service.id == booking.service_id,
        Service.business_id == business.id,
    ).first()
    customer = db.query(Customer).filter(Customer.id == booking.customer_id).first()

    return {
        "id": booking.id,
        "status": booking.status.value,
        "business_slug": business.slug,
        "staff_slug": staff.slug if staff else None,
        "service_slug": service.slug if service else None,
        "service_name": service.name if service else None,
        "customer_name": customer.name if customer else None,
        "customer_phone": customer.phone if customer else None,
        "start_datetime": to_business_tz(booking.start_datetime, tz).isoformat(),
        "end_datetime": to_business_tz(booking.end_datetime, tz).isoformat(),
        "public_token": booking.public_token,
        "idempotency_key": booking.idempotency_key,
        "notes": booking.notes,
    }


@router.post("/{business_slug}/bookings", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_new_booking(
    request: Request,
    business_slug: str,
    payload: BookingCreate,
    db: Annotated[Session, Depends(get_db)],
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    """
    Endpoint transaccional para crear reservas.
    """

    requested_staff_slug = payload.staff_slug.strip().lower()

    normalized_idempotency_key = _normalize_idempotency_key(idempotency_key)
    business: Business | None = None

    try:
        with db.begin():
            business = db.query(Business).filter(
                Business.slug == business_slug
            ).first()
            if not business:
                logger.warning(f"Booking attempt on invalid business: {business_slug}")
                raise HTTPException(status_code=404, detail="Business not found")

            tz = get_business_tz(db, business.id)

            if normalized_idempotency_key:
                existing_booking = get_booking_by_idempotency_key(
                    session=db,
                    business_id=business.id,
                    idempotency_key=normalized_idempotency_key,
                )
                if existing_booking:
                    response.status_code = status.HTTP_200_OK
                    return _serialize_booking_response(
                        db,
                        business=business,
                        booking=existing_booking,
                    )

            staff = db.query(Staff).filter(
                Staff.slug == requested_staff_slug,
                Staff.business_id == business.id,
                Staff.active.is_(True)
            ).first()
            if not staff:
                raise HTTPException(status_code=404, detail="Staff not found or inactive")

            service = db.query(Service).filter(
                Service.slug == payload.service_slug,
                Service.business_id == business.id,
                Service.active.is_(True)
            ).first()
            if not service:
                raise HTTPException(status_code=404, detail="Service not found or inactive")

            start_datetime = datetime.combine(
                payload.date,
                payload.time,
                tzinfo=tz
            )

            if start_datetime <= datetime.now(tz):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot create a booking in the past."
                )

            customer_data = payload.customer
            phone = normalize_phone(customer_data.phone)
            if not phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer phone is required.",
                )

            first_name = customer_data.first_name.strip()
            last_name = customer_data.last_name.strip()
            if not first_name or not last_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer first_name and last_name are required.",
                )
            raw_email = customer_data.email.lower() if customer_data.email else None
            resolved_email = raw_email or build_email_fallback(phone)
            customer = resolve_customer(
                db,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email=resolved_email,
            )

            new_booking = create_booking(
                session=db,
                business_id=business.id,
                staff_id=staff.id,
                service_id=service.id,
                customer_id=customer.id,
                start_datetime=start_datetime,
                idempotency_key=normalized_idempotency_key,
                notes=payload.notes,
            )
            db.flush()

            return _serialize_booking_response(
                db,
                business=business,
                booking=new_booking,
            )

    except InvalidBookingRequest as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SlotNotAvailable as e:
        logger.info(f"Slot conflict in {business_slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected time slot is no longer available."
        )

    except IntegrityError as e:
        db.rollback()

        if normalized_idempotency_key and business is None:
            business = db.query(Business).filter(Business.slug == business_slug).first()

        if normalized_idempotency_key and business:
            existing_booking = get_booking_by_idempotency_key(
                session=db,
                business_id=business.id,
                idempotency_key=normalized_idempotency_key,
            )
            if existing_booking:
                response.status_code = status.HTTP_200_OK
                return _serialize_booking_response(
                    db,
                    business=business,
                    booking=existing_booking,
                )

        logger.error(f"Integrity error while creating booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Data conflict occurred."
        )

    except SQLAlchemyError as e:
        logger.critical(f"Database error while creating booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred."
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error in create_booking endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )
