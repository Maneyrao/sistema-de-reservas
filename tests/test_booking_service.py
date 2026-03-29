"""Tests unitarios para services/booking_service.py"""
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest

from models.booking import BookingStatus
from services.booking_service import (
    InvalidBookingRequest,
    InvalidService,
    SlotNotAvailable,
    cancel_booking,
    create_booking,
    normalize_phone,
    resolve_customer,
)
from tests.factories import (
    make_availability,
    make_booking,
    make_business,
    make_customer,
    make_service,
    make_staff,
    make_staff_service,
)

ARG = ZoneInfo("America/Argentina/Buenos_Aires")


class TestNormalizePhone:
    def test_strips_non_digits(self):
        # "+54 911 1234-5678" → digits: 5,4,9,1,1,1,2,3,4,5,6,7,8
        assert normalize_phone("+54 911 1234-5678") == "+5491112345678"

    def test_adds_plus_prefix(self):
        assert normalize_phone("5491112345678") == "+5491112345678"

    def test_empty_returns_empty(self):
        assert normalize_phone("") == ""

    def test_only_symbols_returns_empty(self):
        assert normalize_phone("---") == ""


class TestResolveCustomer:
    def test_creates_new_customer(self, db_session):
        customer = resolve_customer(
            db_session,
            first_name="Carlos",
            last_name="Lopez",
            phone="+5491112345678",
        )
        assert customer.id is not None
        assert customer.name == "Carlos Lopez"
        assert customer.phone == "+5491112345678"

    def test_finds_by_phone(self, db_session):
        existing = make_customer(db_session, phone="+5491112345678", name="Old Name")
        db_session.commit()

        customer = resolve_customer(
            db_session,
            first_name="Carlos",
            last_name="Lopez",
            phone="+5491112345678",
        )
        assert customer.id == existing.id
        assert customer.name == "Carlos Lopez"

    def test_missing_phone_raises(self, db_session):
        with pytest.raises(InvalidBookingRequest, match="phone"):
            resolve_customer(
                db_session,
                first_name="Carlos",
                last_name="Lopez",
                phone="",
            )

    def test_missing_name_raises(self, db_session):
        with pytest.raises(InvalidBookingRequest, match="first_name"):
            resolve_customer(
                db_session,
                first_name="",
                last_name="Lopez",
                phone="+5491112345678",
            )


class TestCreateBooking:
    def _setup(self, db_session):
        business = make_business(db_session, timezone="America/Argentina/Buenos_Aires")
        service = make_service(db_session, business=business, duration_minutes=30)
        staff = make_staff(db_session, business=business)
        make_staff_service(db_session, staff=staff, service=service)
        make_availability(
            db_session,
            staff=staff,
            weekday=0,  # Monday
            start_time=time(9, 0),
            end_time=time(18, 0),
        )
        customer = make_customer(db_session)
        db_session.commit()
        return business, service, staff, customer

    def test_creates_booking_successfully(self, db_session):
        business, service, staff, customer = self._setup(db_session)
        start = datetime(2024, 6, 3, 10, 0, 0, tzinfo=ARG)  # Monday

        booking = create_booking(
            db_session,
            business_id=business.id,
            staff_id=staff.id,
            service_id=service.id,
            customer_id=customer.id,
            start_datetime=start,
        )
        assert booking.status == BookingStatus.confirmed
        assert booking.public_token is not None
        assert booking.end_datetime == start.replace(hour=10, minute=30)

    def test_slot_not_available_conflict(self, db_session):
        business, service, staff, customer = self._setup(db_session)
        start = datetime(2024, 6, 3, 10, 0, 0, tzinfo=ARG)
        end = datetime(2024, 6, 3, 10, 30, 0, tzinfo=ARG)
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

        with pytest.raises(SlotNotAvailable):
            create_booking(
                db_session,
                business_id=business.id,
                staff_id=staff.id,
                service_id=service.id,
                customer_id=customer.id,
                start_datetime=start,
            )

    def test_unaligned_step_raises(self, db_session):
        business, service, staff, customer = self._setup(db_session)
        # 10:07 is not 15-min aligned
        start = datetime(2024, 6, 3, 10, 7, 0, tzinfo=ARG)

        with pytest.raises(InvalidBookingRequest, match="15 minutos"):
            create_booking(
                db_session,
                business_id=business.id,
                staff_id=staff.id,
                service_id=service.id,
                customer_id=customer.id,
                start_datetime=start,
            )

    def test_outside_availability_raises(self, db_session):
        business, service, staff, customer = self._setup(db_session)
        # 7:00 is before availability (9:00)
        start = datetime(2024, 6, 3, 7, 0, 0, tzinfo=ARG)

        with pytest.raises(InvalidBookingRequest, match="disponibilidad"):
            create_booking(
                db_session,
                business_id=business.id,
                staff_id=staff.id,
                service_id=service.id,
                customer_id=customer.id,
                start_datetime=start,
            )

    def test_invalid_service_raises(self, db_session):
        business, service, staff, customer = self._setup(db_session)
        start = datetime(2024, 6, 3, 10, 0, 0, tzinfo=ARG)

        with pytest.raises(InvalidService):
            create_booking(
                db_session,
                business_id=business.id,
                staff_id=staff.id,
                service_id=999,  # nonexistent
                customer_id=customer.id,
                start_datetime=start,
            )


class TestCancelBooking:
    def test_cancels_confirmed_booking(self, db_session):
        business = make_business(db_session)
        service = make_service(db_session, business=business)
        staff = make_staff(db_session, business=business)
        customer = make_customer(db_session)
        start = datetime(2024, 6, 3, 10, 0, tzinfo=ARG)
        end = datetime(2024, 6, 3, 10, 30, tzinfo=ARG)
        booking = make_booking(
            db_session,
            business=business,
            staff=staff,
            service=service,
            customer=customer,
            start_datetime=start,
            end_datetime=end,
        )
        db_session.commit()

        result = cancel_booking(db_session, booking_id=booking.id, reason="customer request")
        assert result.status == BookingStatus.canceled
        assert result.canceled_reason == "customer request"
        assert result.canceled_at is not None

    def test_idempotent_cancel_already_canceled(self, db_session):
        business = make_business(db_session)
        service = make_service(db_session, business=business)
        staff = make_staff(db_session, business=business)
        customer = make_customer(db_session)
        start = datetime(2024, 6, 3, 10, 0, tzinfo=ARG)
        end = datetime(2024, 6, 3, 10, 30, tzinfo=ARG)
        booking = make_booking(
            db_session,
            business=business,
            staff=staff,
            service=service,
            customer=customer,
            start_datetime=start,
            end_datetime=end,
            status=BookingStatus.canceled,
        )
        db_session.commit()

        result = cancel_booking(db_session, booking_id=booking.id)
        assert result.status == BookingStatus.canceled
