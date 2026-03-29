"""
Factories para construir objetos de dominio en tests.

Cada factory devuelve el objeto ya persistido (session.flush()) pero
sin hacer commit — el test controla la transacción.
"""
from datetime import time

from sqlalchemy.orm import Session

from models.availability import AvailabilityRule
from models.booking import Booking, BookingStatus
from models.business import Business
from models.customer import Customer
from models.service import Service
from models.staff import Staff
from models.staff_service import StaffService


def make_business(
    session: Session,
    *,
    name: str = "Test Barber",
    slug: str = "test-barber",
    timezone: str = "America/Argentina/Buenos_Aires",
) -> Business:
    business = Business(
        name=name,
        slug=slug,
        timezone=timezone,
    )
    session.add(business)
    session.flush()
    return business


def make_service(
    session: Session,
    *,
    business: Business,
    name: str = "Corte",
    slug: str = "corte",
    duration_minutes: int = 30,
    price_amount: int = 2000,
    price_currency: str = "ARS",
    active: bool = True,
) -> Service:
    service = Service(
        business_id=business.id,
        name=name,
        slug=slug,
        duration_minutes=duration_minutes,
        price_amount=price_amount,
        price_currency=price_currency,
        active=active,
    )
    session.add(service)
    session.flush()
    return service


def make_staff(
    session: Session,
    *,
    business: Business,
    name: str = "Juan",
    slug: str = "juan",
    active: bool = True,
) -> Staff:
    staff = Staff(
        business_id=business.id,
        name=name,
        slug=slug,
        active=active,
    )
    session.add(staff)
    session.flush()
    return staff


def make_staff_service(
    session: Session,
    *,
    staff: Staff,
    service: Service,
) -> StaffService:
    ss = StaffService(staff_id=staff.id, service_id=service.id)
    session.add(ss)
    session.flush()
    return ss


def make_availability(
    session: Session,
    *,
    staff: Staff,
    weekday: int = 0,
    start_time: time = time(9, 0),
    end_time: time = time(18, 0),
) -> AvailabilityRule:
    rule = AvailabilityRule(
        staff_id=staff.id,
        weekday=weekday,
        start_time=start_time,
        end_time=end_time,
    )
    session.add(rule)
    session.flush()
    return rule


def make_customer(
    session: Session,
    *,
    name: str = "Carlos Lopez",
    email: str = "carlos@example.com",
    phone: str = "+5491112345678",
) -> Customer:
    customer = Customer(name=name, email=email, phone=phone)
    session.add(customer)
    session.flush()
    return customer


def make_booking(
    session: Session,
    *,
    business: Business,
    staff: Staff,
    service: Service,
    customer: Customer,
    start_datetime,
    end_datetime,
    status: BookingStatus = BookingStatus.confirmed,
) -> Booking:
    booking = Booking(
        business_id=business.id,
        staff_id=staff.id,
        service_id=service.id,
        customer_id=customer.id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        status=status,
        public_token="test-token-" + str(start_datetime.timestamp()),
    )
    session.add(booking)
    session.flush()
    return booking
