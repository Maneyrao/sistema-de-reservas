"""
Unified end-to-end test for every endpoint in the Club Amsterdam booking system.

Usage:
    # 1. Start the server (in a separate terminal):
    #    uvicorn main:app --reload
    #
    # OR run directly (uses FastAPI TestClient, no running server needed):
    #    python scripts/test_all_endpoints.py

Expected result: all tests print [PASS] and summary shows 100% passed.
"""

import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Must be set BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./booking_local.db"
os.environ.setdefault("CRON_SECRET", "test-cron-secret")
os.environ.setdefault("ADMIN_JWT_SECRET", "super-secret-admin-key")
os.environ.setdefault("ADMIN_JWT_EXPIRE_MINUTES", "720")

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import models  # noqa: F401
from database.base import Base
from database.session import SessionLocal, engine
from fastapi.testclient import TestClient
from main import app
from models.booking import Booking
from scripts.seed import run_seed

TZ_ARG = ZoneInfo("America/Argentina/Buenos_Aires")
BUSINESS_SLUG = "club-amsterdam"
ADMIN_EMAIL = "tmaneyro@gmail.com"
ADMIN_PASSWORD = "jujuy2366"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

passed: list[str] = []
failed: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        print(f"  [PASS] {label}")
        passed.append(label)
    else:
        msg = f"{label}" + (f" - {detail}" if detail else "")
        print(f"  [FAIL] {msg}")
        failed.append(msg)
    return condition


def check_status(label: str, response, expected: int) -> bool:
    ok = response.status_code == expected
    detail = f"expected {expected}, got {response.status_code}: {response.text[:200]}" if not ok else ""
    return check(label, ok, detail)


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    run_seed()


def next_allowed_day() -> datetime:
    now = datetime.now(TZ_ARG)
    return now + timedelta(days=1)


def force_into_reminder_window(booking_id: int) -> None:
    """Move booking start to ~2 hours from now so the cron can pick it up."""
    with SessionLocal() as db:
        with db.begin():
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return
            target = (datetime.now(TZ_ARG) + timedelta(hours=2)).replace(second=0, microsecond=0)
            booking.start_datetime = target
            booking.end_datetime = target + timedelta(minutes=45)
            booking.reminder_sent_at = None
            db.add(booking)


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------

def main() -> int:
    print("Resetting local database and seeding data...")
    reset_db()

    client = TestClient(app)

    # -----------------------------------------------------------------------
    section("1. SANITY - OpenAPI & Docs")
    # -----------------------------------------------------------------------
    check_status("GET /openapi.json -> 200", client.get("/openapi.json"), 200)
    check_status("GET /docs -> 200", client.get("/docs"), 200)

    # -----------------------------------------------------------------------
    section("2. PUBLIC CATALOG")
    # -----------------------------------------------------------------------
    catalog_ok = client.get(f"/v1/business/{BUSINESS_SLUG}/catalog")
    check_status("GET /catalog (public) -> 200", catalog_ok, 200)
    if catalog_ok.status_code == 200:
        catalog_payload = catalog_ok.json()
        check("GET /catalog returns business slug",
              catalog_payload.get("business", {}).get("slug") == BUSINESS_SLUG,
              f"got {catalog_payload.get('business', {}).get('slug')}")
        check("GET /catalog returns public services",
              isinstance(catalog_payload.get("services"), list) and len(catalog_payload["services"]) >= 1,
              f"got {catalog_payload.get('services')}")
        check("GET /catalog returns default staff slug=mati",
              catalog_payload.get("booking_rules", {}).get("default_staff_slug") == "mati",
              f"got {catalog_payload.get('booking_rules', {}).get('default_staff_slug')}")
        check("GET /catalog includes seeded service corte-cabello",
              any(item.get("slug") == "corte-cabello" for item in catalog_payload.get("services", [])),
              f"got {catalog_payload.get('services')}")
        check("GET /catalog returns hero_title",
              bool(catalog_payload.get("business", {}).get("hero_title")),
              f"got {catalog_payload.get('business')}")
        check("GET /catalog returns staff public title",
              bool(catalog_payload.get("staff", [{}])[0].get("title")),
              f"got {catalog_payload.get('staff')}")

    # -----------------------------------------------------------------------
    section("3. AVAILABILITY")
    # -----------------------------------------------------------------------
    booking_day = next_allowed_day()
    date_str = booking_day.date().isoformat()

    # 2a. Valid request
    avail_ok = client.get(
        f"/v1/business/{BUSINESS_SLUG}/availability/slots",
        params={"service_slug": "corte-cabello", "date_from": date_str, "date_to": date_str, "staff_slug": "mati"},
    )
    check_status("GET /availability/slots (valid) -> 200", avail_ok, 200)
    slots = avail_ok.json() if avail_ok.status_code == 200 else []
    check("GET /availability/slots returns a list of slots", isinstance(slots, list) and len(slots) > 0,
          f"got {len(slots)} slots")

    if len(slots) < 5:
        print("\n  [ABORT] Not enough slots to run booking tests. Check seed data and date.")
        print_summary()
        return 1

    # 2b. Unknown staff slug → 400
    avail_bad_staff = client.get(
        f"/v1/business/{BUSINESS_SLUG}/availability/slots",
        params={"service_slug": "corte-cabello", "date_from": date_str, "date_to": date_str, "staff_slug": "nobody"},
    )
    check_status("GET /availability/slots (bad staff) -> 404", avail_bad_staff, 404)

    # 2c. Inverted date range → 400
    yesterday = (booking_day - timedelta(days=1)).date().isoformat()
    avail_bad_range = client.get(
        f"/v1/business/{BUSINESS_SLUG}/availability/slots",
        params={"service_slug": "corte-cabello", "date_from": date_str, "date_to": yesterday, "staff_slug": "mati"},
    )
    check_status("GET /availability/slots (inverted range) -> 400", avail_bad_range, 400)

    # 2d. Unknown service -> 404
    avail_bad_service = client.get(
        f"/v1/business/{BUSINESS_SLUG}/availability/slots",
        params={"service_slug": "nope", "date_from": date_str, "date_to": date_str, "staff_slug": "mati"},
    )
    check_status("GET /availability/slots (bad service) -> 404", avail_bad_service, 404)

    # -----------------------------------------------------------------------
    section("4. PUBLIC BOOKINGS")
    # -----------------------------------------------------------------------
    slot0 = datetime.fromisoformat(slots[0]["start"])
    slot4 = datetime.fromisoformat(slots[4]["start"])

    def build_payload(slot_dt: datetime, first: str, last: str, phone: str, email: str, notes: str = "") -> dict:
        return {
            "service_slug": "corte-cabello",
            "staff_slug": "mati",
            "date": slot_dt.date().isoformat(),
            "time": slot_dt.time().strftime("%H:%M:%S"),
            "customer": {"first_name": first, "last_name": last, "phone": phone, "email": email},
            "notes": notes,
        }

    payload_1 = build_payload(slot0, "Juan", "Perez", "+5491112345678", "juan@example.com", "prueba 1")
    payload_2 = build_payload(slot4, "Ana", "Garcia", "+5491122233344", "ana@example.com", "prueba 2")

    # 3a. Create booking #1
    booking_1 = client.post(
        f"/v1/business/{BUSINESS_SLUG}/bookings",
        headers={"Idempotency-Key": "itest-001"},
        json=payload_1,
    )
    check_status("POST /bookings (create booking #1) -> 201", booking_1, 201)
    booking_1_id = booking_1.json().get("id") if booking_1.status_code == 201 else None

    # 3b. Idempotency retry — same key, same payload → 200 with same ID
    booking_1_retry = client.post(
        f"/v1/business/{BUSINESS_SLUG}/bookings",
        headers={"Idempotency-Key": "itest-001"},
        json=payload_1,
    )
    check_status("POST /bookings (idempotent retry) -> 200", booking_1_retry, 200)
    if booking_1.status_code == 201 and booking_1_retry.status_code == 200:
        check(
            "POST /bookings idempotent retry returns same booking ID",
            booking_1.json().get("id") == booking_1_retry.json().get("id"),
            f"got {booking_1_retry.json().get('id')} vs {booking_1.json().get('id')}",
        )

    # 3c. Slot conflict — different key, same slot → 409
    booking_1_conflict = client.post(
        f"/v1/business/{BUSINESS_SLUG}/bookings",
        headers={"Idempotency-Key": "itest-002"},
        json={**payload_1, "customer": {**payload_1["customer"], "phone": "+5499999999999", "email": "other@x.com"}},
    )
    check_status("POST /bookings (slot conflict) -> 409", booking_1_conflict, 409)

    # 3d. Misaligned time (5-min offset) → 400
    misaligned_time = (slot0 + timedelta(minutes=5)).time().strftime("%H:%M:%S")
    booking_misaligned = client.post(
        f"/v1/business/{BUSINESS_SLUG}/bookings",
        headers={"Idempotency-Key": "itest-003"},
        json={**payload_1, "time": misaligned_time,
              "customer": {**payload_1["customer"], "phone": "+5498888888888", "email": "mis@x.com"}},
    )
    check_status("POST /bookings (misaligned time) -> 400", booking_misaligned, 400)

    # 3e. Create booking #2 (for reschedule test later)
    booking_2 = client.post(
        f"/v1/business/{BUSINESS_SLUG}/bookings",
        headers={"Idempotency-Key": "itest-004"},
        json=payload_2,
    )
    check_status("POST /bookings (create booking #2) -> 201", booking_2, 201)
    booking_2_id = booking_2.json().get("id") if booking_2.status_code == 201 else None

    # -----------------------------------------------------------------------
    section("5. CRON - Send Reminders")
    # -----------------------------------------------------------------------

    # 4a. No secret → 401
    check_status("POST /cron/send-reminders (no secret) -> 401",
                 client.post("/cron/send-reminders"), 401)

    # 4b. Wrong secret → 401
    check_status("POST /cron/send-reminders (bad secret) -> 401",
                 client.post("/cron/send-reminders", headers={"x-cron-secret": "wrong!"}), 401)

    # 4c. Force booking into reminder window, then trigger cron
    if booking_1_id:
        force_into_reminder_window(booking_1_id)

    cron_ok = client.post("/cron/send-reminders", headers={"x-cron-secret": os.environ["CRON_SECRET"]})
    check_status("POST /cron/send-reminders (valid secret) -> 200", cron_ok, 200)

    # 4d. Second run → same endpoint, should send 0 (already marked sent)
    cron_second = client.post("/cron/send-reminders", headers={"x-cron-secret": os.environ["CRON_SECRET"]})
    check_status("POST /cron/send-reminders (second run) -> 200", cron_second, 200)
    if cron_second.status_code == 200:
        check("POST /cron/send-reminders (second run) sends 0 reminders",
              cron_second.json().get("sent") == 0,
              f"got sent={cron_second.json().get('sent')}")

    # -----------------------------------------------------------------------
    section("6. ADMIN AUTH")
    # -----------------------------------------------------------------------

    # 5a. Login with wrong password → 401
    login_bad = client.post("/admin/auth/login", json={
        "business_slug": BUSINESS_SLUG,
        "email": ADMIN_EMAIL,
        "password": "wrong-password",
    })
    check_status("POST /admin/auth/login (wrong password) -> 401", login_bad, 401)

    # 5b. Login with wrong email → 401
    login_bad_email = client.post("/admin/auth/login", json={
        "business_slug": BUSINESS_SLUG,
        "email": "nobody@clubamsterdam.com",
        "password": ADMIN_PASSWORD,
    })
    check_status("POST /admin/auth/login (wrong email) -> 401", login_bad_email, 401)

    # 5c. Valid login → 200 + token
    login_ok = client.post("/admin/auth/login", json={
        "business_slug": BUSINESS_SLUG,
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
    })
    check_status("POST /admin/auth/login (valid credentials) -> 200", login_ok, 200)
    token = login_ok.json().get("access_token") if login_ok.status_code == 200 else None
    check("POST /admin/auth/login returns access_token", bool(token), f"token={token}")
    auth_headers = {"Authorization": f"Bearer {token}"} if token else {}

    # 5d. GET /me without token → 401
    check_status("GET /admin/auth/me (no token) -> 401",
                 client.get("/admin/auth/me"), 401)

    # 5e. GET /me with valid token → 200
    me = client.get("/admin/auth/me", headers=auth_headers)
    check_status("GET /admin/auth/me (valid token) -> 200", me, 200)
    if me.status_code == 200:
        check("GET /admin/auth/me returns correct email",
              me.json().get("email") == ADMIN_EMAIL,
              f"got {me.json().get('email')}")

    business_info = client.get("/admin/business", headers=auth_headers)
    check_status("GET /admin/business -> 200", business_info, 200)
    if business_info.status_code == 200:
        check("GET /admin/business returns hero title",
              bool(business_info.json().get("hero_title")),
              f"got {business_info.json()}")

    business_update = client.patch("/admin/business",
                                   json={"announcement": "Agenda premium activa"},
                                   headers=auth_headers)
    check_status("PATCH /admin/business -> 200", business_update, 200)
    if business_update.status_code == 200:
        check("PATCH /admin/business updates announcement",
              business_update.json().get("announcement") == "Agenda premium activa",
              f"got {business_update.json()}")

    # -----------------------------------------------------------------------
    section("7. ADMIN BOOKINGS - List")
    # -----------------------------------------------------------------------

    # 6a. Without auth → 401
    check_status("GET /admin/bookings (no auth) -> 401",
                 client.get("/admin/bookings", params={"date_from": date_str, "date_to": date_str}), 401)

    # 6b. With auth, valid date range → 200
    agenda = client.get("/admin/bookings",
                        params={"date_from": date_str, "date_to": date_str},
                        headers=auth_headers)
    check_status("GET /admin/bookings (valid range) -> 200", agenda, 200)
    if agenda.status_code == 200:
        bookings_list = agenda.json()
        check("GET /admin/bookings returns our bookings",
              isinstance(bookings_list, list) and len(bookings_list) >= 1,
              f"got {len(bookings_list)} bookings")

    # 6c. Status filter
    agenda_filtered = client.get("/admin/bookings",
                                 params={"date_from": date_str, "date_to": date_str, "status": "pending"},
                                 headers=auth_headers)
    check_status("GET /admin/bookings (status filter) -> 200", agenda_filtered, 200)

    # -----------------------------------------------------------------------
    section("8. ADMIN BOOKINGS - Cancel")
    # -----------------------------------------------------------------------
    if booking_1_id:
        # 7a. Cancel booking #1
        cancel = client.post(f"/admin/bookings/{booking_1_id}/cancel",
                             json={"reason": "cliente no puede asistir"},
                             headers=auth_headers)
        check_status(f"POST /admin/bookings/{booking_1_id}/cancel -> 200", cancel, 200)
        if cancel.status_code == 200:
            check("Cancel returns status=canceled",
                  cancel.json().get("status") == "canceled",
                  f"got {cancel.json().get('status')}")

        # 7b. Cancel already-canceled booking -> 200 (idempotent)
        cancel_again = client.post(f"/admin/bookings/{booking_1_id}/cancel",
                                   json={"reason": "doble cancelacion"},
                                   headers=auth_headers)
        check_status(f"POST /admin/bookings/{booking_1_id}/cancel (already canceled) -> 200", cancel_again, 200)

        # 7c. Cancel non-existent booking → 404
        check_status("POST /admin/bookings/99999/cancel (not found) -> 404",
                     client.post("/admin/bookings/99999/cancel", json={}, headers=auth_headers), 404)
    else:
        print("  [SKIP] Cancel tests - booking #1 was not created")

    # -----------------------------------------------------------------------
    section("9. ADMIN BOOKINGS - Reschedule")
    # -----------------------------------------------------------------------
    if booking_2_id:
        new_time = (slot4 + timedelta(minutes=45)).time().strftime("%H:%M:%S")
        reschedule = client.post(f"/admin/bookings/{booking_2_id}/reschedule",
                                 json={"new_date": date_str, "new_time": new_time, "reason": "ajuste interno"},
                                 headers=auth_headers)
        check_status(f"POST /admin/bookings/{booking_2_id}/reschedule -> 200", reschedule, 200)
        rescheduled_id = reschedule.json().get("id") if reschedule.status_code == 200 else None

        # 8b. Reschedule non-existent → 404
        check_status("POST /admin/bookings/99999/reschedule (not found) -> 404",
                     client.post("/admin/bookings/99999/reschedule",
                                 json={"new_date": date_str, "new_time": "10:00:00"},
                                 headers=auth_headers), 404)

        # -----------------------------------------------------------------------
        section("10. ADMIN BOOKINGS - Update Status")
        # -----------------------------------------------------------------------
        if rescheduled_id:
            update_status = client.patch(f"/admin/bookings/{rescheduled_id}/status",
                                         json={"status": "completed", "reason": "servicio realizado"},
                                         headers=auth_headers)
            check_status(f"PATCH /admin/bookings/{rescheduled_id}/status -> 200", update_status, 200)
            if update_status.status_code == 200:
                check("PATCH /status returns status=completed",
                      update_status.json().get("status") == "completed",
                      f"got {update_status.json().get('status')}")

            # Invalid status value → 400
            update_bad = client.patch(f"/admin/bookings/{rescheduled_id}/status",
                                      json={"status": "flying"},
                                      headers=auth_headers)
            check_status("PATCH /admin/bookings/{id}/status (invalid status) -> 400", update_bad, 400)

            # Non-existent booking → 404
            check_status("PATCH /admin/bookings/99999/status (not found) -> 404",
                         client.patch("/admin/bookings/99999/status",
                                      json={"status": "confirmed"},
                                      headers=auth_headers), 404)
    else:
        print("  [SKIP] Reschedule / update-status tests - booking #2 was not created")

    # -----------------------------------------------------------------------
    section("11. ADMIN BLOCKS - Create, List, Delete")
    # -----------------------------------------------------------------------
    block_start = slot0.replace(hour=15, minute=0, second=0, microsecond=0)
    block_end = block_start + timedelta(hours=1)

    # 10a. No auth → 401
    check_status("GET /admin/blocks (no auth) -> 401",
                 client.get("/admin/blocks", params={"date_from": date_str, "date_to": date_str}), 401)

    # 10b. Create block
    create_block = client.post("/admin/blocks",
                               json={
                                   "staff_slug": "mati",
                                   "start_datetime": block_start.isoformat(),
                                   "end_datetime": block_end.isoformat(),
                                   "reason": "almuerzo",
                                   "notes": "bloqueo de prueba",
                               },
                               headers=auth_headers)
    check_status("POST /admin/blocks (create block) -> 201", create_block, 201)
    block_id = create_block.json().get("id") if create_block.status_code == 201 else None

    # 10c. List blocks
    list_blocks = client.get("/admin/blocks",
                             params={"date_from": date_str, "date_to": date_str, "staff_slug": "mati"},
                             headers=auth_headers)
    check_status("GET /admin/blocks (list) -> 200", list_blocks, 200)
    if list_blocks.status_code == 200 and block_id:
        block_ids_in_list = [b["id"] for b in list_blocks.json()]
        check("GET /admin/blocks contains created block",
              block_id in block_ids_in_list,
              f"block {block_id} not in {block_ids_in_list}")

    # 10d. Global block (no staff_slug)
    global_block_start = slot0.replace(hour=16, minute=0, second=0, microsecond=0)
    global_block_end = global_block_start + timedelta(minutes=30)
    create_global_block = client.post("/admin/blocks",
                                      json={
                                          "start_datetime": global_block_start.isoformat(),
                                          "end_datetime": global_block_end.isoformat(),
                                          "reason": "cierre general",
                                      },
                                      headers=auth_headers)
    check_status("POST /admin/blocks (global block, no staff) -> 201", create_global_block, 201)
    global_block_id = create_global_block.json().get("id") if create_global_block.status_code == 201 else None

    # 10e. Delete staff block
    if block_id:
        delete_block = client.delete(f"/admin/blocks/{block_id}", headers=auth_headers)
        check_status(f"DELETE /admin/blocks/{block_id} -> 200", delete_block, 200)
        if delete_block.status_code == 200:
            check("DELETE /admin/blocks returns deleted=true",
                  delete_block.json().get("deleted") is True,
                  f"got {delete_block.json()}")

        # Delete again → 404
        check_status(f"DELETE /admin/blocks/{block_id} (already deleted) -> 404",
                     client.delete(f"/admin/blocks/{block_id}", headers=auth_headers), 404)

    # 10f. Delete global block
    if global_block_id:
        delete_global = client.delete(f"/admin/blocks/{global_block_id}", headers=auth_headers)
        check_status(f"DELETE /admin/blocks/{global_block_id} (global block) -> 200", delete_global, 200)

    # 10g. Delete non-existent block → 404
    check_status("DELETE /admin/blocks/99999 (not found) -> 404",
                 client.delete("/admin/blocks/99999", headers=auth_headers), 404)

    # -----------------------------------------------------------------------
    section("12. ADMIN SERVICES & STAFF")
    # -----------------------------------------------------------------------

    services_before = client.get("/admin/services", headers=auth_headers)
    check_status("GET /admin/services -> 200", services_before, 200)
    seeded_haircut = None
    if services_before.status_code == 200:
        seeded_haircut = next((item for item in services_before.json() if item["slug"] == "corte-cabello"), None)
        check("GET /admin/services contains seeded haircut service",
              seeded_haircut is not None,
              f"got {services_before.json()}")

    create_service_response = client.post("/admin/services",
                                          json={
                                              "name": "Afeitado Premium",
                                              "slug": "afeitado-premium",
                                              "duration_minutes": 30,
                                              "price_amount": 18000,
                                              "price_currency": "ARS",
                                              "active": True,
                                          },
                                          headers=auth_headers)
    check_status("POST /admin/services (create) -> 201", create_service_response, 201)
    created_service_id = create_service_response.json().get("id") if create_service_response.status_code == 201 else None

    if created_service_id:
        update_service_response = client.patch(f"/admin/services/{created_service_id}",
                                               json={"price_amount": 19000},
                                               headers=auth_headers)
        check_status("PATCH /admin/services/{id} -> 200", update_service_response, 200)
        if update_service_response.status_code == 200:
            check("PATCH /admin/services updates price",
                  update_service_response.json().get("price_amount") == 19000,
                  f"got {update_service_response.json()}")

    create_staff_response = client.post("/admin/staff",
                                        json={
                                            "name": "Nicolas",
                                            "slug": "nico",
                                            "title": "Senior Barber",
                                            "bio": "Especialista en fades",
                                            "avatar_url": "https://example.com/nico.jpg",
                                            "active": True,
                                            "service_ids": [created_service_id] if created_service_id else [],
                                            "availability_rules": [
                                                {"weekday": 0, "start_time": "14:00:00", "end_time": "19:00:00"},
                                                {"weekday": 2, "start_time": "14:00:00", "end_time": "19:00:00"},
                                            ],
                                        },
                                        headers=auth_headers)
    check_status("POST /admin/staff (create) -> 201", create_staff_response, 201)
    created_staff_id = create_staff_response.json().get("id") if create_staff_response.status_code == 201 else None

    staff_list_response = client.get("/admin/staff", headers=auth_headers)
    check_status("GET /admin/staff -> 200", staff_list_response, 200)
    if staff_list_response.status_code == 200 and created_staff_id:
        check("GET /admin/staff contains created barber",
              any(item["id"] == created_staff_id for item in staff_list_response.json()),
              f"got {staff_list_response.json()}")

    if created_staff_id and created_service_id and seeded_haircut:
        update_staff_response = client.patch(f"/admin/staff/{created_staff_id}",
                                             json={
                                                 "service_ids": [created_service_id, seeded_haircut["id"]],
                                                 "availability_rules": [
                                                     {"weekday": 1, "start_time": "13:00:00", "end_time": "18:00:00"}
                                                 ],
                                             },
                                             headers=auth_headers)
        check_status("PATCH /admin/staff/{id} -> 200", update_staff_response, 200)
        if update_staff_response.status_code == 200:
            updated_staff = update_staff_response.json()
            check("PATCH /admin/staff updates assigned services",
                  len(updated_staff.get("services", [])) == 2,
                  f"got {updated_staff}")

    admin_booking_create = client.post("/admin/bookings",
                                       json={
                                           "staff_slug": "mati",
                                           "service_slug": "corte-cabello",
                                           "date": date_str,
                                           "time": "18:00:00",
                                           "customer": {
                                               "first_name": "Pedro",
                                               "last_name": "Suarez",
                                               "phone": "+5491133399999",
                                               "email": "pedro@example.com",
                                           },
                                           "notes": "cargado desde admin",
                                           "status": "confirmed",
                                       },
                                       headers=auth_headers)
    check_status("POST /admin/bookings (manual create) -> 201", admin_booking_create, 201)

    if created_staff_id:
        delete_staff_response = client.delete(f"/admin/staff/{created_staff_id}", headers=auth_headers)
        check_status("DELETE /admin/staff/{id} -> 200", delete_staff_response, 200)
        if delete_staff_response.status_code == 200:
            check("DELETE /admin/staff deactivates barber",
                  delete_staff_response.json().get("active") is False,
                  f"got {delete_staff_response.json()}")

    if created_service_id:
        delete_service_response = client.delete(f"/admin/services/{created_service_id}", headers=auth_headers)
        check_status("DELETE /admin/services/{id} -> 200", delete_service_response, 200)
        if delete_service_response.status_code == 200:
            check("DELETE /admin/services deactivates service",
                  delete_service_response.json().get("active") is False,
                  f"got {delete_service_response.json()}")

    # -----------------------------------------------------------------------
    print_summary()
    return 1 if failed else 0


def print_summary() -> None:
    total = len(passed) + len(failed)
    print(f"\n{'='*60}")
    print(f"  RESULTS: {len(passed)}/{total} passed")
    print(f"{'='*60}")
    if failed:
        print("\nFailed tests:")
        for f in failed:
            print(f"  - {f}")
    else:
        print("\n  All tests passed!")


if __name__ == "__main__":
    raise SystemExit(main())
