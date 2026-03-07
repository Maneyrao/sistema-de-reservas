from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.business import router as business_router
from routers.availability import router as availability_router
from routers.booking import router as bookings_router

app = FastAPI(
    title="Booking System API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⬇️ IMPORTANTE: sin prefix acá
app.include_router(business_router)
app.include_router(availability_router)
app.include_router(bookings_router)
