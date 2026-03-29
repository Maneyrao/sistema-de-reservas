import hmac
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from services.booking_service import (
    get_bookings_pending_reminder,
    mark_booking_reminder_sent,
)
from services.whatsapp_service import send_whatsapp_reminder_dummy


router = APIRouter(
    prefix="/cron",
    tags=["Cron"]
)


def _validate_cron_secret(
    x_cron_secret: str | None = Header(default=None, alias="x-cron-secret"),
) -> None:
    expected_secret = os.getenv("CRON_SECRET")

    if not expected_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CRON_SECRET is not configured.",
        )

    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, expected_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron secret.",
        )


@router.post("/send-reminders", status_code=status.HTTP_200_OK)
def send_reminders(
    db: Session = Depends(get_db),
    _: None = Depends(_validate_cron_secret),
):
    """
    Endpoint privado para cron: envia recordatorios WA para reservas en +2h.
    """
    sent_count = 0

    with db.begin():
        to_remind = get_bookings_pending_reminder(session=db)
        sent_at = datetime.now(timezone.utc)

        for booking, phone, customer_name, service_name in to_remind:
            # Hueco para integracion real WA (Twilio/Meta)
            send_whatsapp_reminder_dummy(
                phone,
                customer_name,
                service_name,
                booking.start_datetime.isoformat(),
            )
            mark_booking_reminder_sent(
                session=db,
                booking=booking,
                sent_at=sent_at,
            )
            sent_count += 1

    return {
        "sent": sent_count,
    }
