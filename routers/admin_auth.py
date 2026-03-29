from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from database.session import get_db
from dependencies.admin_auth import get_current_admin_user
from models.admin_user import AdminUser
from schemas.admin_auth import AdminLoginRequest, AdminTokenResponse, AdminUserOut
from services.admin_auth_service import (
    AdminAuthError,
    authenticate_admin,
    create_admin_access_token,
    get_access_token_ttl_seconds,
    touch_last_login,
)


router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])
limiter = Limiter(key_func=get_remote_address)


def _build_admin_user_out(admin: AdminUser) -> AdminUserOut:
    return AdminUserOut(
        id=admin.id,
        business_id=admin.business_id,
        full_name=admin.full_name,
        email=admin.email,
        role=admin.role,
        is_active=admin.is_active,
        last_login_at=admin.last_login_at,
    )


@router.post("/login", response_model=AdminTokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def admin_login(
    request: Request,
    payload: AdminLoginRequest,
    db: Session = Depends(get_db),
):
    try:
        with db.begin():
            admin = authenticate_admin(
                db,
                business_slug=payload.business_slug,
                email=payload.email,
                password=payload.password,
            )
            if admin is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                )

            touch_last_login(admin)
            db.add(admin)
            token = create_admin_access_token(admin)
    except AdminAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return AdminTokenResponse(
        access_token=token,
        expires_in_seconds=get_access_token_ttl_seconds(),
        admin=_build_admin_user_out(admin),
    )


@router.get("/me", response_model=AdminUserOut, status_code=status.HTTP_200_OK)
def admin_me(
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    return _build_admin_user_out(current_admin)
