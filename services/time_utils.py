"""
Utilidades de tiempo puras, sin dependencias de DB ni de negocio.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

STEP_MINUTES = 15


def overlaps(
    start_a: datetime,
    end_a: datetime,
    start_b: datetime,
    end_b: datetime,
) -> bool:
    """
    Retorna True si los intervalos semiabiertos [a_start, a_end) y [b_start, b_end)
    se solapan. Requiere datetimes comparables (mismo timezone o ambos naive).
    """
    return start_a < end_b and start_b < end_a


def to_tz(value: datetime, tz: ZoneInfo) -> datetime:
    """
    Convierte un datetime al timezone dado.
    Si el datetime es naive, asume que ya está en ese timezone.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value.astimezone(tz)


def is_step_aligned(dt: datetime, step_minutes: int = STEP_MINUTES) -> bool:
    """
    Verifica que el datetime esté alineado a bloques de `step_minutes` minutos exactos.
    """
    return (
        dt.minute % step_minutes == 0
        and dt.second == 0
        and dt.microsecond == 0
    )
