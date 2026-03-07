from datetime import time
from sqlalchemy import select
from database.session import SessionLocal
from models.business import Business
from models.staff import Staff
from models.service import Service
from models.availability import AvailabilityRule


def get_or_create(session, model, filters: dict, defaults: dict | None = None):
    stmt = select(model).filter_by(**filters)
    instance = session.execute(stmt).scalar_one_or_none()

    if instance:
        return instance

    data = {**filters, **(defaults or {})}
    instance = model(**data)
    session.add(instance)
    session.flush()  # obtiene ID sin commit
    return instance


def run_seed():
    with SessionLocal() as session:
        with session.begin():

            # -----------------
            # BUSINESS
            # -----------------
            business = get_or_create(
                session,
                Business,
                filters={"slug": "club-amsterdam"},
                defaults={
                    "name": "Club Amsterdam",
                    "timezone": "America/Argentina/Buenos_Aires",
                },
            )

            # -----------------
            # STAFF
            # -----------------
            staff = get_or_create(
                session,
                Staff,
                filters={
                    "business_id": business.id,
                    "slug": "mati",
                },
                defaults={
                    "name": "Matías Damonte",
                    "active": True,
                },
            )

            # -----------------
            # SERVICES
            # -----------------
            services_data = [
                {"name": "Corte", "slug": "corte", "duration": 45},
                {"name": "Barba", "slug": "barba", "duration": 30},
                {"name": "Corte + Barba", "slug": "corte-barba", "duration": 45},
            ]

            for service in services_data:
                get_or_create(
                    session,
                    Service,
                    filters={
                        "business_id": business.id,
                        "slug": service["slug"],
                    },
                    defaults={
                        "name": service["name"],
                        "duration_minutes": service["duration"],
                        "active": True,
                    },
                )

            # -----------------
            # AVAILABILITY RULES
            # -----------------
            availability_rules = []

            # Martes a Jueves → 10:00–20:00
            for weekday in (1, 2, 3):
                availability_rules.append(
                    {
                        "weekday": weekday,
                        "start_time": time(10, 0),
                        "end_time": time(20, 0),
                    }
                )

            # Viernes y Sábado → 10:00–21:00
            for weekday in (4, 5):
                availability_rules.append(
                    {
                        "weekday": weekday,
                        "start_time": time(10, 0),
                        "end_time": time(21, 0),
                    }
                )

            for rule in availability_rules:
                get_or_create(
                    session,
                    AvailabilityRule,
                    filters={
                        "staff_id": staff.id,
                        "weekday": rule["weekday"],
                        "start_time": rule["start_time"],
                        "end_time": rule["end_time"],
                    },
                )

        print("✅ Seed ejecutado correctamente")


if __name__ == "__main__":
    run_seed()
