import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from logging_config import setup_logging
from middleware.request_id import RequestIdMiddleware

setup_logging()

from routers.availability import router as availability_router
from routers.booking import router as bookings_router
from routers.public_catalog import router as public_catalog_router
from routers.cron import router as cron_router
from routers.admin_auth import router as admin_auth_router
from routers.admin_bookings import router as admin_bookings_router
from routers.admin_blocks import router as admin_blocks_router
from routers.admin_business import router as admin_business_router
from routers.admin_services import router as admin_services_router
from routers.admin_staff import router as admin_staff_router
from routers.admin_metrics import router as admin_metrics_router
from routers.ws import router as ws_router
from services.booking_service import (
    SlotNotAvailable,
    BookingNotFound,
    InvalidService,
    InvalidBookingRequest,
)

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title="Booking System API",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Middlewares (orden inverso al de ejecución — el último añadido se ejecuta primero)
# ---------------------------------------------------------------------------
app.add_middleware(RequestIdMiddleware)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers globales
# ---------------------------------------------------------------------------

@app.exception_handler(SlotNotAvailable)
async def slot_not_available_handler(request: Request, exc: SlotNotAvailable):
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc), "code": "SLOT_UNAVAILABLE"},
    )


@app.exception_handler(BookingNotFound)
async def booking_not_found_handler(request: Request, exc: BookingNotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "code": "BOOKING_NOT_FOUND"},
    )


@app.exception_handler(InvalidService)
async def invalid_service_handler(request: Request, exc: InvalidService):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "code": "INVALID_SERVICE"},
    )


@app.exception_handler(InvalidBookingRequest)
async def invalid_booking_handler(request: Request, exc: InvalidBookingRequest):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "code": "INVALID_BOOKING"},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "code": "VALIDATION_ERROR"},
    )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

# MVP cliente final: solo disponibilidad, reserva y cron privado de recordatorios.
app.include_router(public_catalog_router)
app.include_router(availability_router)
app.include_router(bookings_router)
app.include_router(cron_router)
app.include_router(admin_auth_router)
app.include_router(admin_bookings_router)
app.include_router(admin_blocks_router)
app.include_router(admin_business_router)
app.include_router(admin_services_router)
app.include_router(admin_staff_router)
app.include_router(admin_metrics_router)
app.include_router(ws_router)
