from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.business import Business
from models.staff import Staff
from models.service import Service

router = APIRouter(
    prefix="/business",
    tags=["Business"]
)


@router.get("/{business_slug}")
def get_business(
    business_slug: str,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(
        Business.slug == business_slug
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    return business


@router.get("/{business_slug}/staff")
def list_staff(
    business_slug: str,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(
        Business.slug == business_slug
    ).first()

    if not business:
        raise HTTPException(404, "Business not found")

    staff = db.query(Staff).filter(
        Staff.business_id == business.id,
        Staff.active.is_(True)
    ).all()

    return staff


@router.get("/{business_slug}/services")
def list_services(
    business_slug: str,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(
        Business.slug == business_slug
    ).first()

    if not business:
        raise HTTPException(404, "Business not found")

    services = db.query(Service).filter(
        Service.business_id == business.id,
        Service.active.is_(True)
    ).all()

    return services
