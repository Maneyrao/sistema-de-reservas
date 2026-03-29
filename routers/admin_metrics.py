"""
Endpoints de métricas para el dashboard administrativo.

GET /admin/metrics/summary       — Resumen del día
GET /admin/metrics/weekly        — Comparativa semana actual vs anterior
GET /admin/metrics/staff         — Ocupación por staff hoy
GET /admin/metrics/top-services  — Servicios más reservados (últimos 30 días)
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.session import get_db
from dependencies.admin_auth import get_current_admin_user
from models.admin_user import AdminUser
from services.metrics_service import (
    get_daily_summary,
    get_staff_occupancy,
    get_top_services,
    get_weekly_comparison,
)

router = APIRouter(prefix="/admin/metrics", tags=["Admin Metrics"])


@router.get("/summary")
def admin_metrics_summary(
    target_date: date | None = Query(default=None, description="Fecha objetivo (default: hoy)"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
) -> dict:
    return get_daily_summary(
        db,
        business_id=current_admin.business_id,
        target_date=target_date,
    )


@router.get("/weekly")
def admin_metrics_weekly(
    reference_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
) -> dict:
    return get_weekly_comparison(
        db,
        business_id=current_admin.business_id,
        reference_date=reference_date,
    )


@router.get("/staff")
def admin_metrics_staff(
    target_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
) -> list:
    return get_staff_occupancy(
        db,
        business_id=current_admin.business_id,
        target_date=target_date,
    )


@router.get("/top-services")
def admin_metrics_top_services(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
) -> list:
    return get_top_services(
        db,
        business_id=current_admin.business_id,
        days=days,
        limit=limit,
    )
