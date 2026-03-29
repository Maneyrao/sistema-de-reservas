import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy.orm import Session

from models.admin_user import AdminUser
from models.business import Business


class AdminAuthError(Exception):
    pass


class AdminTokenError(AdminAuthError):
    pass


@dataclass
class AdminTokenPayload:
    admin_user_id: int
    business_id: int
    email: str
    role: str
    exp: int


def _get_jwt_secret() -> str:
    secret = os.getenv("ADMIN_JWT_SECRET")
    if not secret:
        raise AdminAuthError("ADMIN_JWT_SECRET is not configured")
    return secret


def _get_jwt_exp_minutes() -> int:
    raw = os.getenv("ADMIN_JWT_EXPIRE_MINUTES", "720")
    try:
        value = int(raw)
    except ValueError as exc:
        raise AdminAuthError("ADMIN_JWT_EXPIRE_MINUTES must be numeric") from exc
    return max(5, value)


def get_access_token_ttl_seconds() -> int:
    return _get_jwt_exp_minutes() * 60


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * ((4 - len(raw) % 4) % 4)
    return base64.urlsafe_b64decode((raw + padding).encode("ascii"))


def _sign(message: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(digest)


def _password_iterations() -> int:
    raw = os.getenv("ADMIN_PASSWORD_PBKDF2_ITERATIONS", "390000")
    try:
        value = int(raw)
    except ValueError as exc:
        raise AdminAuthError("ADMIN_PASSWORD_PBKDF2_ITERATIONS must be numeric") from exc
    return max(120000, value)


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise AdminAuthError("Password must be at least 8 characters long")

    iterations = _password_iterations()
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt, expected = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_raw)
    except ValueError:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return hmac.compare_digest(digest.hex(), expected)


def create_admin_access_token(admin_user: AdminUser) -> str:
    secret = _get_jwt_secret()
    now = int(time.time())
    exp = now + (_get_jwt_exp_minutes() * 60)

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(admin_user.id),
        "business_id": admin_user.business_id,
        "email": admin_user.email,
        "role": admin_user.role,
        "iat": now,
        "exp": exp,
        "token_type": "access",
    }

    header_raw = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_raw = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_raw}.{payload_raw}".encode("ascii")
    signature = _sign(signing_input, secret)
    return f"{header_raw}.{payload_raw}.{signature}"


def decode_admin_access_token(token: str) -> AdminTokenPayload:
    secret = _get_jwt_secret()

    parts = token.split(".")
    if len(parts) != 3:
        raise AdminTokenError("Malformed token")

    header_raw, payload_raw, signature = parts
    signing_input = f"{header_raw}.{payload_raw}".encode("ascii")
    expected_signature = _sign(signing_input, secret)
    if not hmac.compare_digest(signature, expected_signature):
        raise AdminTokenError("Invalid token signature")

    try:
        header = json.loads(_b64url_decode(header_raw))
        payload = json.loads(_b64url_decode(payload_raw))
    except Exception as exc:
        raise AdminTokenError("Invalid token encoding") from exc

    if header.get("alg") != "HS256":
        raise AdminTokenError("Unsupported token algorithm")
    if payload.get("token_type") != "access":
        raise AdminTokenError("Invalid token type")

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        raise AdminTokenError("Token expired")

    try:
        admin_user_id = int(payload["sub"])
        business_id = int(payload["business_id"])
        email = str(payload["email"])
        role = str(payload["role"])
    except Exception as exc:
        raise AdminTokenError("Invalid token payload") from exc

    return AdminTokenPayload(
        admin_user_id=admin_user_id,
        business_id=business_id,
        email=email,
        role=role,
        exp=exp,
    )


def authenticate_admin(
    session: Session,
    *,
    business_slug: str,
    email: str,
    password: str,
) -> AdminUser | None:
    business = session.query(Business).filter(Business.slug == business_slug).first()
    if not business:
        return None

    admin = session.query(AdminUser).filter(
        AdminUser.business_id == business.id,
        AdminUser.email == email.lower().strip(),
        AdminUser.is_active.is_(True),
    ).first()
    if not admin:
        return None

    if not verify_password(password, admin.password_hash):
        return None

    return admin


def touch_last_login(admin_user: AdminUser) -> None:
    admin_user.last_login_at = datetime.now(timezone.utc)


def create_admin_user(
    session: Session,
    *,
    business_slug: str,
    full_name: str,
    email: str,
    password: str,
    role: str = "owner",
) -> AdminUser:
    business = session.query(Business).filter(Business.slug == business_slug).first()
    if not business:
        raise AdminAuthError(f"Business '{business_slug}' not found")

    normalized_email = email.lower().strip()
    existing = session.query(AdminUser).filter(
        AdminUser.business_id == business.id,
        AdminUser.email == normalized_email,
    ).first()
    if existing:
        raise AdminAuthError("Admin user already exists for this business/email")

    admin_user = AdminUser(
        business_id=business.id,
        full_name=full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        is_active=True,
        role=role,
    )
    session.add(admin_user)
    return admin_user


def ensure_admin_user(
    session: Session,
    *,
    business_slug: str,
    full_name: str,
    email: str,
    password: str,
    role: str = "owner",
) -> AdminUser:
    business = session.query(Business).filter(Business.slug == business_slug).first()
    if not business:
        raise AdminAuthError(f"Business '{business_slug}' not found")

    normalized_email = email.lower().strip()
    admin_user = session.query(AdminUser).filter(
        AdminUser.business_id == business.id,
        AdminUser.email == normalized_email,
    ).first()

    if admin_user is None:
        admin_user = AdminUser(
            business_id=business.id,
            full_name=full_name.strip(),
            email=normalized_email,
            password_hash=hash_password(password),
            is_active=True,
            role=role,
        )
        session.add(admin_user)
        return admin_user

    admin_user.full_name = full_name.strip()
    admin_user.email = normalized_email
    admin_user.password_hash = hash_password(password)
    admin_user.is_active = True
    admin_user.role = role
    session.add(admin_user)
    return admin_user
