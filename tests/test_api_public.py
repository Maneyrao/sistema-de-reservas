"""Tests de integración — endpoints públicos."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from tests.factories import (
    make_availability,
    make_booking,
    make_business,
    make_customer,
    make_service,
    make_staff,
    make_staff_service,
)
from models.booking import BookingStatus

ARG = ZoneInfo("America/Argentina/Buenos_Aires")


def next_weekday(weekday: int) -> date:
    """Retorna la próxima fecha (>= mañana) para el día de la semana dado (0=lunes)."""
    today = date.today()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


# Siempre un lunes en el futuro para los tests
FUTURE_MONDAY = next_weekday(0)


class TestAvailabilitySlots:
    def test_get_slots_no_availability(self, client: TestClient, db_session):
        business = make_business(db_session, slug="test-barber")
        service = make_service(db_session, business=business, slug="corte")
        staff = make_staff(db_session, business=business)
        make_staff_service(db_session, staff=staff, service=service)
        db_session.commit()

        response = client.get(
            "/v1/business/test-barber/availability/slots",
            params={
                "service_slug": "corte",
                "date_from": str(FUTURE_MONDAY),
                "date_to": str(FUTURE_MONDAY),
            },
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_get_slots_returns_slots(self, client: TestClient, db_session):
        business = make_business(db_session, slug="test-barber", timezone="America/Argentina/Buenos_Aires")
        service = make_service(db_session, business=business, slug="corte", duration_minutes=30)
        staff = make_staff(db_session, business=business)
        make_staff_service(db_session, staff=staff, service=service)
        make_availability(db_session, staff=staff, weekday=0, start_time=time(9, 0), end_time=time(10, 0))
        db_session.commit()

        response = client.get(
            "/v1/business/test-barber/availability/slots",
            params={
                "service_slug": "corte",
                "date_from": str(FUTURE_MONDAY),
                "date_to": str(FUTURE_MONDAY),
            },
        )
        assert response.status_code == 200
        slots = response.json()
        assert len(slots) > 0
        assert "start" in slots[0]
        assert "end" in slots[0]

    def test_get_slots_business_not_found(self, client: TestClient, db_session):
        response = client.get(
            "/v1/business/nonexistent/availability/slots",
            params={
                "service_slug": "corte",
                "date_from": str(FUTURE_MONDAY),
                "date_to": str(FUTURE_MONDAY),
            },
        )
        assert response.status_code == 404

    def test_get_slots_date_range_too_large(self, client: TestClient, db_session):
        make_business(db_session, slug="test-barber")
        db_session.commit()

        far_future = FUTURE_MONDAY + timedelta(days=45)
        response = client.get(
            "/v1/business/test-barber/availability/slots",
            params={
                "service_slug": "corte",
                "date_from": str(FUTURE_MONDAY),
                "date_to": str(far_future),
            },
        )
        assert response.status_code == 400


class TestCreateBooking:
    def _setup(self, db_session):
        business = make_business(
            db_session,
            slug="test-barber",
            timezone="America/Argentina/Buenos_Aires",
        )
        service = make_service(db_session, business=business, slug="corte", duration_minutes=30)
        staff = make_staff(db_session, business=business, slug="juan")
        make_staff_service(db_session, staff=staff, service=service)
        make_availability(
            db_session,
            staff=staff,
            weekday=0,  # Monday
            start_time=time(9, 0),
            end_time=time(18, 0),
        )
        db_session.commit()
        return business, service, staff

    def _booking_payload(self, book_date: date = None) -> dict:
        target_date = book_date or FUTURE_MONDAY
        return {
            "service_slug": "corte",
            "staff_slug": "juan",
            "date": str(target_date),
            "time": "10:00:00",
            "customer": {
                "first_name": "Carlos",
                "last_name": "Lopez",
                "phone": "+5491112345678",
            },
        }

    def test_create_booking_success(self, client: TestClient, db_session):
        self._setup(db_session)

        response = client.post(
            "/v1/business/test-barber/bookings",
            json=self._booking_payload(),
        )
        assert response.status_code in (200, 201), response.json()
        data = response.json()
        assert "public_token" in data
        assert data["status"] == "confirmed"

    def test_create_booking_missing_phone_fails_validation(self, client: TestClient, db_session):
        self._setup(db_session)

        payload = self._booking_payload()
        payload["customer"]["phone"] = ""

        response = client.post("/v1/business/test-barber/bookings", json=payload)
        assert response.status_code == 422

    def test_create_booking_past_date_fails_validation(self, client: TestClient, db_session):
        self._setup(db_session)

        payload = self._booking_payload(book_date=date(2024, 6, 3))
        response = client.post("/v1/business/test-barber/bookings", json=payload)
        assert response.status_code == 422

    def test_create_booking_idempotency(self, client: TestClient, db_session):
        self._setup(db_session)

        payload = self._booking_payload()
        headers = {"Idempotency-Key": "test-key-001"}

        r1 = client.post("/v1/business/test-barber/bookings", json=payload, headers=headers)
        r2 = client.post("/v1/business/test-barber/bookings", json=payload, headers=headers)

        assert r1.status_code in (200, 201), r1.json()
        assert r2.status_code in (200, 201), r2.json()
        assert r1.json()["public_token"] == r2.json()["public_token"]

    def test_create_booking_conflict(self, client: TestClient, db_session):
        business, service, staff = self._setup(db_session)
        customer = make_customer(db_session)

        # Pre-existing booking at 10:00 on FUTURE_MONDAY
        start = datetime(FUTURE_MONDAY.year, FUTURE_MONDAY.month, FUTURE_MONDAY.day, 10, 0, 0, tzinfo=ARG)
        end = datetime(FUTURE_MONDAY.year, FUTURE_MONDAY.month, FUTURE_MONDAY.day, 10, 30, 0, tzinfo=ARG)
        make_booking(
            db_session,
            business=business,
            staff=staff,
            service=service,
            customer=customer,
            start_datetime=start,
            end_datetime=end,
        )
        db_session.commit()

        payload = self._booking_payload()
        payload["customer"] = {
            "first_name": "Pedro",
            "last_name": "Garcia",
            "phone": "+5491187654321",
        }
        response = client.post("/v1/business/test-barber/bookings", json=payload)
        assert response.status_code == 409
