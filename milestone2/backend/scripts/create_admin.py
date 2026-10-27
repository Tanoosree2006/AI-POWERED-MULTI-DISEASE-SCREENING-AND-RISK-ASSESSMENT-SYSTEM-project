"""Create an admin user (run from backend/): python scripts/create_admin.py USERNAME
The password is read from the ADMIN_PASSWORD environment variable or prompted; it is never stored in plain text."""
import getpass
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.security import hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.services import crud  # noqa: E402


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/create_admin.py USERNAME")
    username = sys.argv[1]
    password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Password (8-72 chars): ")
    if not 8 <= len(password) <= 72:
        sys.exit("Password must be 8-72 characters")
    with SessionLocal() as db:
        if crud.get_user_by_username(db, username):
            sys.exit("User already exists")
        user = crud.create_user(db, username, hash_password(password), role="admin")
        crud.add_audit(db, "admin_created", user.id)
    print(f"Admin '{username}' created")


if __name__ == "__main__":
    main()
