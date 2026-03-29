import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./booking_local.db"
os.environ.setdefault("CRON_SECRET", "test-cron-secret")
os.environ.setdefault("ADMIN_JWT_SECRET", "super-secret-admin-key")
os.environ.setdefault("ADMIN_JWT_EXPIRE_MINUTES", "720")

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import models  # noqa: F401
from database.base import Base
from database.session import SessionLocal, engine
from main import app
from scripts.seed import run_seed
from services.admin_auth_service import create_admin_user


TZ_ARG = ZoneInfo("America/Argentina/Buenos_Aires")


def reset_local_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    run_seed()

    with SessionLocal() as db:
        with db.begin():
            create_admin_user(
                db,
                business_slug="club-amsterdam",
                full_name="Matias Damonte",
                email="mati@clubamsterdam.com",
                password="Amsterdam2026!",
            )


def next_allowed_day() -> datetime:
    now = datetime.now(TZ_ARG)
    for offset in range(1, 10):
        candidate = now + timedelta(days=offset)
        if candidate.weekday() in {1, 2, 3, 4, 5}:
            return candidate
    return now + timedelta(days=1)


def assert_status(label: str, response, expected_status: int, failures: list[str]) -> None:
    if response.status_code != expected_status:
        failures.append(
            f"{label}: expected {expected_status}, got {response.status_code}, body={response.text}"
        )


def main() -> int:
    reset_local_db()
    client = TestClient(app)
    failures: list[str] = []
    business_slug = "club-amsterdam"

    login = client.post(
        "/admin/auth/login",
        json={
            "business_slug": business_slug,
            "email": "mati@clubamsterdam.com",
            "password": "Amsterdam2026!",
        },
    )
    assert_status("admin_login", login, 200, failures)
    token = login.json().get("access_token") if login.status_code == 200 else None
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    me = client.get("/admin/auth/me", headers=headers)
    assert_status("admin_me", me, 200, failures)

    booking_day = next_allowed_day()
    date_from = booking_day.date().isoformat()

    availability = client.get(
        f"/v1/business/{business_slug}/availability/slots",
        params={
            "service_slug": "corte",
            "date_from": date_from,
            "date_to": date_from,
            "staff_slug": "mati",
        },
    )
    assert_status("availability_for_admin_test", availability, 200, failures)
    slots = availability.json() if availability.status_code == 200 else []
    if len(slots) < 3:
        failures.append("availability returned too few slots for admin tests")
        print_results(failures)
        return 1

    def build_booking_payload(slot_index: int, phone: str, email: str):
        start = datetime.fromisoformat(slots[slot_index]["start"])
        return {
            "service_slug": "corte",
            "staff_slug": "mati",
            "date": start.date().isoformat(),
            "time": start.time().strftime("%H:%M:%S"),
            "customer": {
                "first_name": "Cliente",
                "last_name": f"Numero{slot_index}",
                "phone": phone,
                "email": email,
            },
            "notes": f"Booking {slot_index}",
        }, start

    booking_payload_1, start_1 = build_booking_payload(0, "+5491111111111", "cliente1@example.com")
    booking_1 = client.post(
        f"/v1/business/{business_slug}/bookings",
        headers={"Idempotency-Key": "admin-it-1"},
        json=booking_payload_1,
    )
    assert_status("public_booking_1", booking_1, 201, failures)
    booking_1_id = booking_1.json().get("id") if booking_1.status_code == 201 else None

    booking_payload_2, start_2 = build_booking_payload(4, "+5491222222222", "cliente2@example.com")
    booking_2 = client.post(
        f"/v1/business/{business_slug}/bookings",
        headers={"Idempotency-Key": "admin-it-2"},
        json=booking_payload_2,
    )
    assert_status("public_booking_2", booking_2, 201, failures)
    booking_2_id = booking_2.json().get("id") if booking_2.status_code == 201 else None

    agenda = client.get(
        "/admin/bookings",
        params={"date_from": date_from, "date_to": date_from},
        headers=headers,
    )
    assert_status("admin_agenda_list", agenda, 200, failures)

    if booking_1_id:
        cancel = client.post(
            f"/admin/bookings/{booking_1_id}/cancel",
            json={"reason": "cliente no puede asistir"},
            headers=headers,
        )
        assert_status("admin_cancel_booking", cancel, 200, failures)

    if booking_2_id:
        new_time = (start_2 + timedelta(minutes=45)).time().strftime("%H:%M:%S")
        reschedule = client.post(
            f"/admin/bookings/{booking_2_id}/reschedule",
            json={
                "new_date": start_2.date().isoformat(),
                "new_time": new_time,
                "reason": "ajuste interno",
            },
            headers=headers,
        )
        assert_status("admin_reschedule_booking", reschedule, 200, failures)
        rescheduled_id = reschedule.json().get("id") if reschedule.status_code == 200 else None

        if rescheduled_id:
            update_status = client.patch(
                f"/admin/bookings/{rescheduled_id}/status",
                json={"status": "completed", "reason": "servicio realizado"},
                headers=headers,
            )
            assert_status("admin_update_status", update_status, 200, failures)

    block_start = start_1.replace(hour=15, minute=0, second=0, microsecond=0)
    block_end = block_start + timedelta(hours=1)

    create_block = client.post(
        "/admin/blocks",
        json={
            "staff_slug": "mati",
            "start_datetime": block_start.isoformat(),
            "end_datetime": block_end.isoformat(),
            "reason": "almuerzo",
            "notes": "bloqueo manual",
        },
        headers=headers,
    )
    assert_status("admin_create_block", create_block, 201, failures)
    block_id = create_block.json().get("id") if create_block.status_code == 201 else None

    list_blocks = client.get(
        "/admin/blocks",
        params={"date_from": date_from, "date_to": date_from, "staff_slug": "mati"},
        headers=headers,
    )
    assert_status("admin_list_blocks", list_blocks, 200, failures)

    if block_id:
        delete_block = client.delete(f"/admin/blocks/{block_id}", headers=headers)
        assert_status("admin_delete_block", delete_block, 200, failures)

    print_results(failures)
    return 1 if failures else 0


def print_results(failures: list[str]) -> None:
    if not failures:
        print("OK: all admin endpoint checks passed.")
        return

    print("FAIL: admin endpoint checks found issues:")
    for item in failures:
        print(f"- {item}")


if __name__ == "__main__":
    raise SystemExit(main())
