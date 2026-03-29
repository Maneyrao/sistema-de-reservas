"""Tests unitarios para services/availability_service.py"""
from datetime import date, time
from zoneinfo import ZoneInfo

import pytest

from services.availability_service import get_available_slots
from tests.factories import (
    make_availability,
    make_business,
    make_service,
    make_staff,
    make_staff_service,
    make_booking,
    make_customer,
)
from models.booking import BookingStatus
from datetime import datetime


ARG = ZoneInfo("America/Argentina/Buenos_Aires")


class TestGetAvailableSlots:
    def test_no_rules_returns_empty(self, db_session):
        business = make_business(db_session, timezone="America/Argentina/Buenos_Aires")
        service = make_service(db_session, business=business, duration_minutes=30)
        db_session.commit()

        slots = get_available_slots(
            db_session,
            business_id=business.id,
            service_slug=service.slug,
            date_from=date(2024, 6, 3),  # Monday
            date_to=date(2024, 6, 3),
        )
        assert slots == []

    def test_returns_slots_for_rule(self, db_session):
        business = make_business(db_session, timezone="America/Argentina/Buenos_Aires")
        service = make_service(db_session, business=business, duration_minutes=30)
        staff = make_staff(db_session, business=business)
        make_staff_service(db_session, staff=staff, service=service)
        # Monday = weekday 0
        make_availability(
            db_session,
            staff=staff,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(11, 0),
        )
        db_session.commit()

        slots = get_available_slots(
            db_session,
            business_id=business.id,
            service_slug=service.slug,
            date_from=date(2024, 6, 3),  # Monday
            date_to=date(2024, 6, 3),
        )
        # 9:00-11:00 with 30min service and 15min step → 9:00, 9:15, 9:30, 9:45, 10:00, 10:15, 10:30
        assert len(slots) == 7
        assert all("start" in s and "end" in s for s in slots)

    def test_existing_booking_blocks_slot(self, db_session):
        business = make_business(db_session, timezone="America/Argentina/Buenos_Aires")
        service = make_service(db_session, business=business, duration_minutes=30)
        staff = make_staff(db_session, business=business)
        make_staff_service(db_session, staff=staff, service=service)
        make_availability(
            db_session,
            staff=staff,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        customer = make_customer(db_session)

        # Book 9:00-9:30
        start = datetime(2024, 6, 3, 9, 0, 0, tzinfo=ARG)
        end = datetime(2024, 6, 3, 9, 30, 0, tzinfo=ARG)
        make_booking(
            db_session,
            business=business,
            staff=staff,
            service=service,
            customer=customer,
            start_datetime=start,
            end_datetime=end,
            status=BookingStatus.confirmed,
        )
        db_session.commit()

        slots = get_available_slots(
            db_session,
            business_id=business.id,
            service_slug=service.slug,
            date_from=date(2024, 6, 3),
            date_to=date(2024, 6, 3),
        )
        # 9:00-10:00 with 30min service: 9:00 blocked, 9:15 blocked (ends 9:45 ok but starts during booking)
        # Actually 9:15 start → ends 9:45, booking 9:00-9:30 overlaps → blocked
        # 9:30 → ends 10:00, booking ends 9:30, no overlap (semiopen) → available
        start_times = [s["start"].hour * 60 + s["start"].minute for s in slots]
        assert 9 * 60 not in start_times  # 9:00 blocked
        assert 9 * 60 + 15 not in start_times  # 9:15 blocked (service ends 9:45, overlaps booking)
        assert 9 * 60 + 30 in start_times  # 9:30 free

    def test_service_not_found_raises(self, db_session):
        business = make_business(db_session)
        db_session.commit()

        with pytest.raises(ValueError, match="Service not found"):
            get_available_slots(
                db_session,
                business_id=business.id,
                service_slug="nonexistent",
                date_from=date(2024, 6, 3),
                date_to=date(2024, 6, 3),
            )

    def test_staff_slug_filter(self, db_session):
        business = make_business(db_session, timezone="America/Argentina/Buenos_Aires")
        service = make_service(db_session, business=business, duration_minutes=30)
        staff_a = make_staff(db_session, business=business, slug="juan")
        staff_b = make_staff(db_session, business=business, slug="pedro")
        make_staff_service(db_session, staff=staff_a, service=service)
        make_staff_service(db_session, staff=staff_b, service=service)
        make_availability(db_session, staff=staff_a, weekday=0, start_time=time(9, 0), end_time=time(10, 0))
        # staff_b has no availability on Monday
        db_session.commit()

        slots_a = get_available_slots(
            db_session,
            business_id=business.id,
            service_slug=service.slug,
            date_from=date(2024, 6, 3),
            date_to=date(2024, 6, 3),
            staff_slug="juan",
        )
        slots_b = get_available_slots(
            db_session,
            business_id=business.id,
            service_slug=service.slug,
            date_from=date(2024, 6, 3),
            date_to=date(2024, 6, 3),
            staff_slug="pedro",
        )
        assert len(slots_a) > 0
        assert len(slots_b) == 0
