import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

# Fuerza ejecucion local para tests de integracion.
os.environ["DATABASE_URL"] = "sqlite:///./booking_local.db"
os.environ.setdefault("CRON_SECRET", "test-cron-secret")
os.environ.setdefault("ADMIN_JWT_SECRET", "super-secret-admin-key")
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import models  # noqa: F401
from database.base import Base
from database.session import SessionLocal, engine
from main import app
from models.booking import Booking
from scripts.seed import run_seed


TZ_ARG = ZoneInfo("America/Argentina/Buenos_Aires")


def reset_local_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    run_seed()


def next_allowed_day() -> datetime:
    now = datetime.now(TZ_ARG)
    return now + timedelta(days=1)


def assert_status(label: str, response, expected_status: int, failures: list[str]) -> None:
    if response.status_code != expected_status:
        failures.append(
            f"{label}: expected {expected_status}, got {response.status_code}, body={response.text}"
        )


def force_booking_into_reminder_window(booking_id: int) -> None:
    with SessionLocal() as db:
        with db.begin():
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return

            target_start = (datetime.now(TZ_ARG) + timedelta(hours=2)).replace(
                second=0,
                microsecond=0,
            )
            booking.start_datetime = target_start
            booking.end_datetime = target_start + timedelta(minutes=45)
            booking.reminder_sent_at = None
            db.add(booking)


def main() -> int:
    reset_local_db()

    client = TestClient(app)
    failures: list[str] = []
    business_slug = "club-amsterdam"

    # Sanity endpoints
    assert_status("openapi", client.get("/openapi.json"), 200, failures)
    assert_status("docs", client.get("/docs"), 200, failures)

    # Availability
    booking_day = next_allowed_day()
    date_from = booking_day.date().isoformat()
    date_to = date_from

    catalog_ok = client.get(f"/v1/business/{business_slug}/catalog")
    assert_status("catalog_ok", catalog_ok, 200, failures)
    if catalog_ok.status_code == 200:
        catalog_payload = catalog_ok.json()
        if catalog_payload.get("business", {}).get("slug") != business_slug:
            failures.append("catalog_ok returned unexpected business slug")
        if catalog_payload.get("booking_rules", {}).get("default_staff_slug") != "mati":
            failures.append("catalog_ok returned unexpected default staff slug")
        if not catalog_payload.get("services"):
            failures.append("catalog_ok returned no services")
        if not any(item.get("slug") == "corte-cabello" for item in catalog_payload.get("services", [])):
            failures.append("catalog_ok missing seeded service corte-cabello")
        if not catalog_payload.get("business", {}).get("hero_title"):
            failures.append("catalog_ok missing hero_title")
        if not catalog_payload.get("staff", [{}])[0].get("title"):
            failures.append("catalog_ok missing public staff title")

    availability_ok = client.get(
        f"/v1/business/{business_slug}/availability/slots",
        params={
            "service_slug": "corte-cabello",
            "date_from": date_from,
            "date_to": date_to,
            "staff_slug": "mati",
        },
    )
    assert_status("availability_ok", availability_ok, 200, failures)

    availability_bad_staff = client.get(
        f"/v1/business/{business_slug}/availability/slots",
        params={
            "service_slug": "corte-cabello",
            "date_from": date_from,
            "date_to": date_to,
            "staff_slug": "otro",
        },
    )
    assert_status("availability_bad_staff", availability_bad_staff, 404, failures)

    availability_bad_range = client.get(
        f"/v1/business/{business_slug}/availability/slots",
        params={
            "service_slug": "corte-cabello",
            "date_from": date_to,
            "date_to": (booking_day.date() - timedelta(days=1)).isoformat(),
            "staff_slug": "mati",
        },
    )
    assert_status("availability_bad_range", availability_bad_range, 400, failures)

    slots = availability_ok.json()
    if not isinstance(slots, list) or not slots:
        failures.append("availability_ok returned no slots, cannot continue booking tests")
        print_results(failures)
        return 1

    slot_start_iso = slots[0]["start"]
    slot_start = datetime.fromisoformat(slot_start_iso)

    booking_payload = {
        "service_slug": "corte-cabello",
        "staff_slug": "mati",
        "date": slot_start.date().isoformat(),
        "time": slot_start.time().strftime("%H:%M:%S"),
        "customer": {
            "first_name": "Juan",
            "last_name": "Perez",
            "phone": "+5491112345678",
            "email": "juan.perez@example.com",
        },
        "notes": "Prueba automatizada",
    }

    booking_ok = client.post(
        f"/v1/business/{business_slug}/bookings",
        headers={"Idempotency-Key": "itest-booking-001"},
        json=booking_payload,
    )
    assert_status("booking_ok", booking_ok, 201, failures)
    booking_id = booking_ok.json().get("id") if booking_ok.status_code == 201 else None

    booking_idempotent_retry = client.post(
        f"/v1/business/{business_slug}/bookings",
        headers={"Idempotency-Key": "itest-booking-001"},
        json=booking_payload,
    )
    assert_status("booking_idempotent_retry", booking_idempotent_retry, 200, failures)
    if booking_ok.status_code == 201 and booking_idempotent_retry.status_code == 200:
        if booking_ok.json().get("id") != booking_idempotent_retry.json().get("id"):
            failures.append("booking_idempotent_retry returned a different booking id")

    booking_conflict = client.post(
        f"/v1/business/{business_slug}/bookings",
        headers={"Idempotency-Key": "itest-booking-002"},
        json=booking_payload,
    )
    assert_status("booking_conflict", booking_conflict, 409, failures)

    misaligned_payload = {
        **booking_payload,
        "time": (slot_start + timedelta(minutes=5)).time().strftime("%H:%M:%S"),
        "customer": {
            "first_name": "Ana",
            "last_name": "Lopez",
            "phone": "+5491122233344",
            "email": "ana.lopez@example.com",
        },
    }
    booking_misaligned = client.post(
        f"/v1/business/{business_slug}/bookings",
        headers={"Idempotency-Key": "itest-booking-003"},
        json=misaligned_payload,
    )
    assert_status("booking_misaligned", booking_misaligned, 400, failures)

    # Cron reminders
    assert_status(
        "cron_no_secret",
        client.post("/cron/send-reminders"),
        401,
        failures,
    )
    assert_status(
        "cron_bad_secret",
        client.post("/cron/send-reminders", headers={"x-cron-secret": "invalid"}),
        401,
        failures,
    )

    if booking_id:
        force_booking_into_reminder_window(booking_id)

    cron_ok = client.post(
        "/cron/send-reminders",
        headers={"x-cron-secret": os.environ["CRON_SECRET"]},
    )
    assert_status("cron_ok", cron_ok, 200, failures)

    cron_second_run = client.post(
        "/cron/send-reminders",
        headers={"x-cron-secret": os.environ["CRON_SECRET"]},
    )
    assert_status("cron_second_run", cron_second_run, 200, failures)
    if cron_second_run.status_code == 200 and cron_second_run.json().get("sent") not in {0, None}:
        failures.append("cron_second_run should not resend reminders")

    # Admin routes hidden from app
    assert_status(
        "admin_hidden_business_details",
        client.get(f"/v1/business/{business_slug}"),
        404,
        failures,
    )
    assert_status(
        "admin_hidden_staff",
        client.get(f"/v1/business/{business_slug}/staff"),
        404,
        failures,
    )
    assert_status(
        "admin_hidden_services",
        client.get(f"/v1/business/{business_slug}/services"),
        404,
        failures,
    )

    print_results(failures)
    return 1 if failures else 0


def print_results(failures: list[str]) -> None:
    if not failures:
        print("OK: all endpoint checks passed.")
        return

    print("FAIL: endpoint checks found issues:")
    for item in failures:
        print(f"- {item}")


if __name__ == "__main__":
    raise SystemExit(main())
