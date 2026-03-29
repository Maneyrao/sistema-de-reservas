import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.session import SessionLocal
from services.admin_auth_service import AdminAuthError, create_admin_user


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create first admin user for dashboard")
    parser.add_argument("--business-slug", required=True, help="Business slug, e.g. club-amsterdam")
    parser.add_argument("--full-name", required=True, help="Admin full name")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--role", default="owner", help="Admin role, default owner")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    with SessionLocal() as db:
        try:
            with db.begin():
                admin = create_admin_user(
                    db,
                    business_slug=args.business_slug,
                    full_name=args.full_name,
                    email=args.email,
                    password=args.password,
                    role=args.role,
                )
                db.flush()
                print(
                    f"Admin created successfully. id={admin.id}, email={admin.email}, business_id={admin.business_id}"
                )
                return 0
        except AdminAuthError as exc:
            print(f"Error: {exc}")
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
