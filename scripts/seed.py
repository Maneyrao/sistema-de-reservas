from datetime import time

from sqlalchemy import select

from database.session import SessionLocal
from models.admin_user import AdminUser
from models.availability import AvailabilityRule
from models.business import Business
from models.service import Service
from models.staff import Staff
from models.staff_service import StaffService
from services.admin_auth_service import ensure_admin_user


BUSINESS_SLUG = "club-amsterdam"
BUSINESS_NAME = "Club Amsterdam"
BUSINESS_TIMEZONE = "America/Argentina/Buenos_Aires"
BUSINESS_TAGLINE = "Experiencia premium en cada corte"
BUSINESS_HERO_TITLE = "Reserva tu lugar en la silla de Club Amsterdam"
BUSINESS_HERO_DESCRIPTION = (
    "Agenda premium para cortes precisos, barba prolija y una experiencia cuidada de punta a punta."
)
BUSINESS_ANNOUNCEMENT = "Reservas directas online. Confirmacion final por WhatsApp manual."
BUSINESS_BOOKING_NOTE = "Pago en el local luego del servicio."
BUSINESS_ADDRESS = "Santamaría 2390"
BUSINESS_PHONE = "+541139215677"
BUSINESS_INSTAGRAM_URL = "https://www.instagram.com/clubamsterdam_/"
BUSINESS_MAPS_URL = "https://www.google.com/maps?q=-34.67492319999999,-58.5717124"

MATI_STAFF_SLUG = "mati"
MATI_STAFF_NAME = "Matias Damonte"
MATI_STAFF_TITLE = "Founder Barber"
MATI_STAFF_BIO = (
    "Especialista en cortes clasicos y modernos con foco en prolijidad, ritmo de agenda y experiencia premium."
)
MATI_STAFF_AVATAR_URL = "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=800&q=80"
MATI_ADMIN_EMAIL = "tmaneyro@gmail.com"
MATI_ADMIN_PASSWORD = "jujuy2366"

BASE_SERVICES = [
    {
        "slug": "corte-barba",
        "name": "Corte de Barba",
        "duration_minutes": 30,
        "price_amount": 10000,
    },
    {
        "slug": "corte-cabello",
        "name": "Corte de Cabello",
        "duration_minutes": 45,
        "price_amount": 15000,
    },
    {
        "slug": "corte-cabello-barba",
        "name": "Corte de Cabello + Barba",
        "duration_minutes": 45,
        "price_amount": 20000,
    },
    {
        "slug": "limpieza-facial",
        "name": "Limpieza facial",
        "duration_minutes": 45,
        "price_amount": 25000,
    },
]

DEFAULT_AVAILABILITY = [
    (weekday, time(13, 45), time(20, 0))
    for weekday in range(7)
]


def get_or_create(session, model, filters: dict, defaults: dict | None = None):
    stmt = select(model).filter_by(**filters)
    instance = session.execute(stmt).scalar_one_or_none()

    if instance:
        return instance

    data = {**filters, **(defaults or {})}
    instance = model(**data)
    session.add(instance)
    session.flush()
    return instance


def ensure_business(session) -> Business:
    business = get_or_create(
        session,
        Business,
        filters={"slug": BUSINESS_SLUG},
        defaults={
            "name": BUSINESS_NAME,
            "timezone": BUSINESS_TIMEZONE,
        },
    )
    business.name = BUSINESS_NAME
    business.timezone = BUSINESS_TIMEZONE
    business.tagline = BUSINESS_TAGLINE
    business.hero_title = BUSINESS_HERO_TITLE
    business.hero_description = BUSINESS_HERO_DESCRIPTION
    business.announcement = BUSINESS_ANNOUNCEMENT
    business.booking_note = BUSINESS_BOOKING_NOTE
    business.address = BUSINESS_ADDRESS
    business.phone = BUSINESS_PHONE
    business.instagram_url = BUSINESS_INSTAGRAM_URL
    business.maps_url = BUSINESS_MAPS_URL
    session.add(business)
    session.flush()
    return business


def ensure_mati_staff(session, *, business_id: int) -> Staff:
    staff = session.execute(
        select(Staff).where(
            Staff.business_id == business_id,
            Staff.slug == MATI_STAFF_SLUG,
        )
    ).scalar_one_or_none()

    if staff is None:
        staff = Staff(
            business_id=business_id,
            slug=MATI_STAFF_SLUG,
            name=MATI_STAFF_NAME,
            title=MATI_STAFF_TITLE,
            bio=MATI_STAFF_BIO,
            avatar_url=MATI_STAFF_AVATAR_URL,
            active=True,
        )
        session.add(staff)
        session.flush()
        return staff

    staff.name = MATI_STAFF_NAME
    staff.title = MATI_STAFF_TITLE
    staff.bio = MATI_STAFF_BIO
    staff.avatar_url = MATI_STAFF_AVATAR_URL
    staff.active = True
    session.add(staff)
    session.flush()
    return staff


def ensure_base_services(session, *, business_id: int) -> list[Service]:
    services_by_slug = {
        service.slug: service
        for service in session.execute(
            select(Service).where(Service.business_id == business_id)
        ).scalars().all()
    }

    ensured: list[Service] = []
    for item in BASE_SERVICES:
        service = services_by_slug.get(item["slug"])
        if service is None:
            service = Service(
                business_id=business_id,
                slug=item["slug"],
                name=item["name"],
                duration_minutes=item["duration_minutes"],
                price_amount=item["price_amount"],
                price_currency="ARS",
                active=True,
            )
            session.add(service)
            session.flush()
        else:
            service.name = item["name"]
            service.duration_minutes = item["duration_minutes"]
            service.price_amount = item["price_amount"]
            service.price_currency = "ARS"
            service.active = True
            session.add(service)

        ensured.append(service)

    session.flush()
    return ensured


def ensure_staff_service_assignments(
    session,
    *,
    staff_id: int,
    service_ids: list[int],
) -> None:
    existing_assignments = session.execute(
        select(StaffService).where(StaffService.staff_id == staff_id)
    ).scalars().all()
    existing_by_service_id = {assignment.service_id: assignment for assignment in existing_assignments}
    target_service_ids = set(service_ids)

    for service_id in target_service_ids:
        if service_id in existing_by_service_id:
            continue
        session.add(StaffService(staff_id=staff_id, service_id=service_id))

    for assignment in existing_assignments:
        if assignment.service_id not in target_service_ids:
            session.delete(assignment)


def ensure_default_availability(session, *, staff_id: int) -> None:
    existing_rules = session.execute(
        select(AvailabilityRule).where(AvailabilityRule.staff_id == staff_id)
    ).scalars().all()

    if existing_rules:
        return

    for weekday, start_time, end_time in DEFAULT_AVAILABILITY:
        session.add(
            AvailabilityRule(
                staff_id=staff_id,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time,
            )
        )


def ensure_owner_admin(session, *, business_slug: str) -> AdminUser:
    admin_user = ensure_admin_user(
        session,
        business_slug=business_slug,
        full_name=MATI_STAFF_NAME,
        email=MATI_ADMIN_EMAIL,
        password=MATI_ADMIN_PASSWORD,
        role="owner",
    )
    session.flush()

    other_admins = session.execute(
        select(AdminUser).where(
            AdminUser.business_id == admin_user.business_id,
            AdminUser.id != admin_user.id,
        )
    ).scalars().all()
    for other_admin in other_admins:
        other_admin.is_active = False
        session.add(other_admin)

    return admin_user


def run_seed():
    with SessionLocal() as session:
        with session.begin():
            business = ensure_business(session)
            mati_staff = ensure_mati_staff(session, business_id=business.id)
            services = ensure_base_services(session, business_id=business.id)
            ensure_staff_service_assignments(
                session,
                staff_id=mati_staff.id,
                service_ids=[service.id for service in services],
            )
            ensure_default_availability(session, staff_id=mati_staff.id)
            ensure_owner_admin(session, business_slug=business.slug)

        print("Seed ejecutado correctamente")


if __name__ == "__main__":
    run_seed()
