# Importar Base desde database (como ya lo tenés)
from database.base import Base

# Importar TODOS los modelos para registrar mappers
from models.business import Business
from models.staff import Staff
from models.service import Service
from models.customer import Customer
from models.availability import AvailabilityRule
from models.booking import Booking, BookingStatus

__all__ = [
    "Base",
    "Business",
    "Staff",
    "Service",
    "Customer",
    "AvailabilityRule",
    "Booking",
    "BookingStatus",
]
