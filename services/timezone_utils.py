"""
Resolución de timezone por negocio con caché a nivel módulo.
Las conversiones puras de datetime viven en time_utils.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from models.business import Business
from services.time_utils import STEP_MINUTES, to_tz  # noqa: F401 — re-exportados

# Caché de timezones por business_id. Se invalida al reiniciar el proceso.
_tz_cache: dict[int, ZoneInfo] = {}


def get_business_tz(session: Session, business_id: int) -> ZoneInfo:
    """
    Retorna el ZoneInfo del timezone del negocio.
    Cachea el resultado para evitar queries repetidas.
    """
    if business_id not in _tz_cache:
        tz_str = session.execute(
            select(Business.timezone).where(Business.id == business_id)
        ).scalar_one()
        _tz_cache[business_id] = ZoneInfo(tz_str)
    return _tz_cache[business_id]


def to_business_tz(value, tz: ZoneInfo):
    """
    Alias de to_tz para compatibilidad. Preferir to_tz directamente.
    """
    return to_tz(value, tz)
