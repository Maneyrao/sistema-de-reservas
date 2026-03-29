"""
Middleware que asigna un request_id único a cada request y lo propaga:
- Header de respuesta: X-Request-ID
- Variable de contexto: REQUEST_ID_CTX (accesible desde logging filter)
"""
import logging
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default="")


class _RequestIdFilter(logging.Filter):
    """Inyecta request_id en cada LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID_CTX.get("")
        return True


# Aplicar el filter al root logger una sola vez al importar
_filter = _RequestIdFilter()
logging.getLogger().addFilter(_filter)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = REQUEST_ID_CTX.set(request_id)
        try:
            response = await call_next(request)
        finally:
            REQUEST_ID_CTX.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response
