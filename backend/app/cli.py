"""Command-line tasks for deployment.

Usage (from the backend directory):
    python -m app.cli create-admin --email admin@example.com --password <password>
"""

import argparse
import sys

from pydantic import EmailStr, TypeAdapter, ValidationError

from app.core.database import SessionLocal
from app.domain.errors import ConflictError
from app.domain.models import Role
from app.services.accounts import AccountRegistry

MIN_PASSWORD_LENGTH = 8


def create_admin(email: str, password: str) -> int:
    """Creates an administrator account; returns a process exit code."""
    try:
        email = TypeAdapter(EmailStr).validate_python(email)
    except ValidationError:
        print(f"Некоректний email: {email}", file=sys.stderr)
        return 1
    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"Пароль має містити щонайменше {MIN_PASSWORD_LENGTH} символів", file=sys.stderr)
        return 1

    with SessionLocal() as session:
        try:
            admin = AccountRegistry(session).new_user(email, password, Role.ADMIN)
        except ConflictError as exc:
            print(exc.message, file=sys.stderr)
            return 1
        session.add(admin)
        session.commit()
    print(f"Адміністратора {email} створено")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Службові команди FitClub")
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser("create-admin", help="створити обліковий запис адміністратора")
    admin.add_argument("--email", required=True)
    admin.add_argument("--password", required=True)

    args = parser.parse_args(argv)
    if args.command == "create-admin":
        return create_admin(args.email, args.password)
    return 1


if __name__ == "__main__":
    sys.exit(main())
