import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.session import get_db
from schemas.booking import BookingCreate
from models.business import Business
from models.staff import Staff
from models.service import Service
from models.customer import Customer
from services.booking_service import (
    create_booking,
    get_business_bookings_by_date,
    SlotNotAvailable
)

# ---------------------------------------------------------
# Configuración
# ---------------------------------------------------------

logger = logging.getLogger(__name__)
TZ_ARG = ZoneInfo("America/Argentina/Buenos_Aires")

router = APIRouter(
    prefix="/v1/business",
    tags=["Bookings"]
)

# ---------------------------------------------------------
# POST /bookings
# ---------------------------------------------------------

@router.post("/{business_slug}/bookings", status_code=status.HTTP_201_CREATED)
def create_new_booking(
    business_slug: str,
    payload: BookingCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Endpoint transaccional para crear reservas.
    """

    try:
        # 🚨 LA TRANSACCIÓN ARRANCA PRIMERO
        with db.begin():

            # -------------------------------------------------
            # FASE 1: Validaciones
            # -------------------------------------------------

            business = db.query(Business).filter(
                Business.slug == business_slug
            ).first()
            if not business:
                logger.warning(f"Booking attempt on invalid business: {business_slug}")
                raise HTTPException(status_code=404, detail="Business not found")

            staff = db.query(Staff).filter(
                Staff.slug == payload.staff_slug,
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

            # -------------------------------------------------
            # FASE 2: Datetime
            # -------------------------------------------------

            start_datetime = datetime.combine(
                payload.date,
                payload.time,
                tzinfo=TZ_ARG
            )

            if start_datetime <= datetime.now(TZ_ARG):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot create a booking in the past."
                )

            # -------------------------------------------------
            # FASE 3: Customer + Booking
            # -------------------------------------------------

            customer_data = payload.customer
            customer = db.query(Customer).filter(
                Customer.email == customer_data.email
            ).first()

            if not customer:
                customer = Customer(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.phone,
                )
                db.add(customer)
                db.flush()

            new_booking = create_booking(
                session=db,
                business_id=business.id,
                staff_id=staff.id,
                service_id=service.id,
                customer_id=customer.id,
                start_datetime=start_datetime,
            )

            return new_booking

    except SlotNotAvailable as e:
        logger.info(f"Slot conflict in {business_slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected time slot is no longer available."
        )

    except IntegrityError as e:
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


# ---------------------------------------------------------
# GET /bookings
# ---------------------------------------------------------

@router.get("/{business_slug}/bookings", status_code=status.HTTP_200_OK)
def list_bookings(
    business_slug: str,
    date_param: date = Query(..., alias="date", description="Fecha YYYY-MM-DD"),
    staff_slug: str | None = Query(None, description="Filtrar por staff (opcional)"),
    db: Session = Depends(get_db),
):
    """
    Lista reservas internas filtradas por fecha.
    """

    business = db.query(Business).filter(Business.slug == business_slug).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    staff_id = None
    if staff_slug:
        staff = db.query(Staff).filter(
            Staff.slug == staff_slug,
            Staff.business_id == business.id
        ).first()
        if not staff:
            raise HTTPException(status_code=404, detail="Staff filter not found")
        staff_id = staff.id

    return get_business_bookings_by_date(
        session=db,
        business_id=business.id,
        day=date_param,
        staff_id=staff_id,
    )
