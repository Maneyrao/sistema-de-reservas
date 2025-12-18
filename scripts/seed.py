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

            #Business
            business = get_or_create(
                session,
                Business,
                filters={"slug": "amsterdam"},
                defaults={
                    "name": "Amsterdam Barbería",
                    "timezone": "America/Argentina/Buenos_Aires",
                },
            )

            #Staff
            staff = get_or_create(
                session,
                Staff,
                filters={
                    "business_id": business.id,
                    "name": "Matías",
                },
            )

            #Services
            services_data = [
                ("Corte", 45),
                ("Barba", 30),
                ("Corte + Barba", 45),
            ]

            for name, duration in services_data:
                get_or_create(
                    session,
                    Service,
                    filters={
                        "business_id": business.id,
                        "name": name,
                    },
                    defaults={
                        "duration_minutes": duration,
                        "active": True,
                    },
                )

            # Availability Rules
            # Convención weekday: 0=Lunes ... 6=Domingo

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

        print("Seed ejecutado correctamente")


if __name__ == "__main__":
    run_seed()
