"""Tests unitarios para services/time_utils.py"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from services.time_utils import STEP_MINUTES, is_step_aligned, overlaps, to_tz

ARG = ZoneInfo("America/Argentina/Buenos_Aires")
UTC = timezone.utc


class TestOverlaps:
    def test_no_overlap_before(self):
        a_start = datetime(2024, 1, 1, 9, 0, tzinfo=UTC)
        a_end = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)
        b_start = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)
        b_end = datetime(2024, 1, 1, 11, 0, tzinfo=UTC)
        assert not overlaps(a_start, a_end, b_start, b_end)

    def test_no_overlap_after(self):
        a_start = datetime(2024, 1, 1, 11, 0, tzinfo=UTC)
        a_end = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
        b_start = datetime(2024, 1, 1, 9, 0, tzinfo=UTC)
        b_end = datetime(2024, 1, 1, 11, 0, tzinfo=UTC)
        assert not overlaps(a_start, a_end, b_start, b_end)

    def test_overlap_partial(self):
        a_start = datetime(2024, 1, 1, 9, 0, tzinfo=UTC)
        a_end = datetime(2024, 1, 1, 10, 30, tzinfo=UTC)
        b_start = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)
        b_end = datetime(2024, 1, 1, 11, 0, tzinfo=UTC)
        assert overlaps(a_start, a_end, b_start, b_end)

    def test_overlap_contained(self):
        outer_s = datetime(2024, 1, 1, 9, 0, tzinfo=UTC)
        outer_e = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
        inner_s = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)
        inner_e = datetime(2024, 1, 1, 11, 0, tzinfo=UTC)
        assert overlaps(outer_s, outer_e, inner_s, inner_e)

    def test_overlap_identical(self):
        s = datetime(2024, 1, 1, 9, 0, tzinfo=UTC)
        e = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)
        assert overlaps(s, e, s, e)

    def test_semiopen_boundary_touch_no_overlap(self):
        """Intervalos semiabiertos: [a, b) y [b, c) no se solapan."""
        a_end = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)
        b_start = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)
        assert not overlaps(
            datetime(2024, 1, 1, 9, 0, tzinfo=UTC),
            a_end,
            b_start,
            datetime(2024, 1, 1, 11, 0, tzinfo=UTC),
        )


class TestToTz:
    def test_naive_datetime_gets_tz(self):
        naive = datetime(2024, 6, 15, 12, 0, 0)
        result = to_tz(naive, ARG)
        assert result.tzinfo == ARG
        assert result.hour == 12

    def test_aware_datetime_converts(self):
        utc_dt = datetime(2024, 6, 15, 15, 0, 0, tzinfo=UTC)
        result = to_tz(utc_dt, ARG)
        assert result.tzinfo is not None
        # ARG = UTC-3, so 15:00 UTC → 12:00 ARG
        assert result.hour == 12

    def test_same_tz_returns_same_value(self):
        dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=ARG)
        result = to_tz(dt, ARG)
        assert result == dt


class TestIsStepAligned:
    @pytest.mark.parametrize("minute", [0, 15, 30, 45])
    def test_aligned_minutes(self, minute):
        dt = datetime(2024, 1, 1, 10, minute, 0)
        assert is_step_aligned(dt)

    @pytest.mark.parametrize("minute", [1, 7, 14, 16, 29, 31, 44, 46, 59])
    def test_unaligned_minutes(self, minute):
        dt = datetime(2024, 1, 1, 10, minute, 0)
        assert not is_step_aligned(dt)

    def test_nonzero_seconds_fails(self):
        dt = datetime(2024, 1, 1, 10, 0, 1)
        assert not is_step_aligned(dt)

    def test_nonzero_microseconds_fails(self):
        dt = datetime(2024, 1, 1, 10, 0, 0, 1)
        assert not is_step_aligned(dt)

    def test_step_minutes_constant(self):
        assert STEP_MINUTES == 15
