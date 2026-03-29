"""
Configuración de logging estructurado JSON para producción.

Uso:
    from logging_config import setup_logging
    setup_logging()

En desarrollo (LOG_FORMAT=text) emite logs legibles.
En producción (LOG_FORMAT=json o default) emite JSON por línea.
"""
import logging
import os
import sys
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    """Formateador minimalista de una sola línea JSON."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        payload: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        # request_id propagado via contextvars (inyectado por middleware)
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    """
    Configura el root logger según las variables de entorno:
    - LOG_LEVEL: DEBUG | INFO | WARNING | ERROR (default: INFO)
    - LOG_FORMAT: json | text (default: json)
    """
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json").lower()

    log_level = getattr(logging, log_level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    if log_format == "text":
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    else:
        handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # Silenciar loggers ruidosos de libs
    for noisy in ("sqlalchemy.engine", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
