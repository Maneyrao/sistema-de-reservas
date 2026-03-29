from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models.availability import AvailabilityRule
from models.service import Service
from models.staff import Staff
from models.staff_service import StaffService


class AdminCatalogError(Exception):
    pass


class AdminCatalogConflictError(AdminCatalogError):
    pass


class AdminCatalogNotFoundError(AdminCatalogError):
    pass


def _validate_availability_rules(rules: list[dict[str, Any]]) -> None:
    rules_by_weekday: dict[int, list[tuple]] = defaultdict(list)
    for item in rules:
        rules_by_weekday[item["weekday"]].append((item["start_time"], item["end_time"]))

    for weekday_rules in rules_by_weekday.values():
        ordered = sorted(weekday_rules, key=lambda value: value[0])
        for index in range(1, len(ordered)):
            previous_end = ordered[index - 1][1]
            current_start = ordered[index][0]
            if current_start < previous_end:
                raise AdminCatalogError("Availability rules for the same weekday cannot overlap")


def _resolve_service_rows(
    session: Session,
    *,
    business_id: int,
    service_ids: list[int],
) -> list[Service]:
    if not service_ids:
        return []

    rows = session.execute(
        select(Service).where(
            Service.business_id == business_id,
            Service.id.in_(service_ids),
        )
    ).scalars().all()

    if len(rows) != len(set(service_ids)):
        raise AdminCatalogNotFoundError("One or more services were not found in this business")

    return rows


def _sync_staff_services(
    session: Session,
    *,
    staff: Staff,
    service_rows: list[Service],
) -> None:
    target_ids = {service.id for service in service_rows}
    existing_rows = session.execute(
        select(StaffService).where(StaffService.staff_id == staff.id)
    ).scalars().all()
    existing_by_service_id = {row.service_id: row for row in existing_rows}

    for service in service_rows:
        if service.id in existing_by_service_id:
            continue
        session.add(StaffService(staff_id=staff.id, service_id=service.id))

    for row in existing_rows:
        if row.service_id not in target_ids:
            session.delete(row)


def _replace_availability(
    session: Session,
    *,
    staff: Staff,
    rules: list[dict[str, Any]],
) -> None:
    _validate_availability_rules(rules)

    existing_rows = session.execute(
        select(AvailabilityRule).where(AvailabilityRule.staff_id == staff.id)
    ).scalars().all()
    for row in existing_rows:
        session.delete(row)

    for item in rules:
        session.add(
            AvailabilityRule(
                staff_id=staff.id,
                weekday=item["weekday"],
                start_time=item["start_time"],
                end_time=item["end_time"],
            )
        )


def list_services(session: Session, *, business_id: int) -> list[Service]:
    return session.execute(
        select(Service)
        .where(Service.business_id == business_id)
        .order_by(Service.active.desc(), Service.name.asc())
    ).scalars().all()


def create_service(
    session: Session,
    *,
    business_id: int,
    name: str,
    slug: str,
    duration_minutes: int,
    price_amount: int,
    price_currency: str,
    active: bool,
) -> Service:
    existing = session.execute(
        select(Service).where(
            Service.business_id == business_id,
            Service.slug == slug,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise AdminCatalogConflictError("Service slug already exists for this business")

    service = Service(
        business_id=business_id,
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


def update_service(
    session: Session,
    *,
    business_id: int,
    service_id: int,
    changes: dict[str, Any],
) -> Service:
    service = session.execute(
        select(Service).where(
            Service.business_id == business_id,
            Service.id == service_id,
        )
    ).scalar_one_or_none()
    if service is None:
        raise AdminCatalogNotFoundError("Service not found")

    new_slug = changes.get("slug")
    if new_slug and new_slug != service.slug:
        duplicate = session.execute(
            select(Service).where(
                Service.business_id == business_id,
                Service.slug == new_slug,
                Service.id != service_id,
            )
        ).scalar_one_or_none()
        if duplicate is not None:
            raise AdminCatalogConflictError("Service slug already exists for this business")

    for key, value in changes.items():
        setattr(service, key, value)

    session.add(service)
    session.flush()
    return service


def deactivate_service(
    session: Session,
    *,
    business_id: int,
    service_id: int,
) -> Service:
    service = session.execute(
        select(Service).where(
            Service.business_id == business_id,
            Service.id == service_id,
        )
    ).scalar_one_or_none()
    if service is None:
        raise AdminCatalogNotFoundError("Service not found")

    service.active = False
    session.add(service)
    session.flush()
    return service


def list_staff(session: Session, *, business_id: int) -> list[Staff]:
    return session.execute(
        select(Staff)
        .where(Staff.business_id == business_id)
        .options(
            selectinload(Staff.staff_services).selectinload(StaffService.service),
            selectinload(Staff.availability_rules),
        )
        .order_by(Staff.active.desc(), Staff.name.asc())
    ).scalars().all()


def create_staff(
    session: Session,
    *,
    business_id: int,
    name: str,
    slug: str,
    title: str | None,
    bio: str | None,
    avatar_url: str | None,
    active: bool,
    service_ids: list[int],
    availability_rules: list[dict[str, Any]],
) -> Staff:
    existing = session.execute(
        select(Staff).where(
            Staff.business_id == business_id,
            Staff.slug == slug,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise AdminCatalogConflictError("Staff slug already exists for this business")

    staff = Staff(
        business_id=business_id,
        name=name,
        slug=slug,
        title=title,
        bio=bio,
        avatar_url=avatar_url,
        active=active,
    )
    session.add(staff)
    session.flush()

    service_rows = _resolve_service_rows(
        session,
        business_id=business_id,
        service_ids=service_ids,
    )
    _sync_staff_services(session, staff=staff, service_rows=service_rows)
    _replace_availability(
        session,
        staff=staff,
        rules=availability_rules,
    )
    session.flush()

    return session.execute(
        select(Staff)
        .where(Staff.id == staff.id)
        .options(
            selectinload(Staff.staff_services).selectinload(StaffService.service),
            selectinload(Staff.availability_rules),
        )
    ).scalar_one()


def update_staff(
    session: Session,
    *,
    business_id: int,
    staff_id: int,
    changes: dict[str, Any],
) -> Staff:
    staff = session.execute(
        select(Staff)
        .where(
            Staff.business_id == business_id,
            Staff.id == staff_id,
        )
        .options(
            selectinload(Staff.staff_services).selectinload(StaffService.service),
            selectinload(Staff.availability_rules),
        )
    ).scalar_one_or_none()
    if staff is None:
        raise AdminCatalogNotFoundError("Staff not found")

    new_slug = changes.get("slug")
    if new_slug and new_slug != staff.slug:
        duplicate = session.execute(
            select(Staff).where(
                Staff.business_id == business_id,
                Staff.slug == new_slug,
                Staff.id != staff_id,
            )
        ).scalar_one_or_none()
        if duplicate is not None:
            raise AdminCatalogConflictError("Staff slug already exists for this business")

    service_ids = changes.pop("service_ids", None)
    availability_rules = changes.pop("availability_rules", None)

    for key, value in changes.items():
        setattr(staff, key, value)

    if service_ids is not None:
        service_rows = _resolve_service_rows(
            session,
            business_id=business_id,
            service_ids=service_ids,
        )
        _sync_staff_services(session, staff=staff, service_rows=service_rows)

    if availability_rules is not None:
        _replace_availability(
            session,
            staff=staff,
            rules=availability_rules,
        )

    session.add(staff)
    session.flush()

    return session.execute(
        select(Staff)
        .where(Staff.id == staff.id)
        .options(
            selectinload(Staff.staff_services).selectinload(StaffService.service),
            selectinload(Staff.availability_rules),
        )
    ).scalar_one()


def deactivate_staff(
    session: Session,
    *,
    business_id: int,
    staff_id: int,
) -> Staff:
    staff = session.execute(
        select(Staff)
        .where(
            Staff.business_id == business_id,
            Staff.id == staff_id,
        )
        .options(
            selectinload(Staff.staff_services).selectinload(StaffService.service),
            selectinload(Staff.availability_rules),
        )
    ).scalar_one_or_none()
    if staff is None:
        raise AdminCatalogNotFoundError("Staff not found")

    staff.active = False
    session.add(staff)
    session.flush()
    return staff
