from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.business import Business
from models.staff import Staff
from models.service import Service

router = APIRouter(
    prefix="/v1/business",
    tags=["Business"]
)

@router.get("/{business_slug}", status_code=status.HTTP_200_OK)
def get_business_details(
    business_slug: str,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(Business.slug == business_slug).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    return business


@router.get("/{business_slug}/staff", status_code=status.HTTP_200_OK)
def list_business_staff(
    business_slug: str,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(Business.slug == business_slug).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    staff_members = db.query(Staff).filter(
        Staff.business_id == business.id,
        Staff.active.is_(True)
    ).all()
    
    return staff_members


@router.get("/{business_slug}/services", status_code=status.HTTP_200_OK)
def list_business_services(
    business_slug: str,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(Business.slug == business_slug).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    services = db.query(Service).filter(
        Service.business_id == business.id,
        Service.active.is_(True)
    ).all()
    
    return services
