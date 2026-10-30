"""Create an admin user in Postgres via SQLAlchemy async session.

Usage:
    python backend/scripts/create_admin.py admin@example.com "YourPassword"
"""

import asyncio
import os
import sys
import getpass

from sqlalchemy import select

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(ROOT, "backend"))

from app.core.security import get_password_hash
from app.db.models import User
from app.db.session import get_sessionmaker


async def main():
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        username = input("Admin email: ").strip().lower()
        if not username:
            print("Admin email is required")
            sys.exit(1)

        while True:
            password = getpass.getpass("Password: ")
            confirm = getpass.getpass("Confirm password: ")
            if not password:
                print("Password cannot be empty")
                continue
            if password != confirm:
                print("Passwords do not match")
                continue
            break

    session_factory = get_sessionmaker()
    async with session_factory() as db:
        existing = await db.execute(select(User).where(User.username == username))
        row = existing.scalar_one_or_none()
        if row is None:
            row = User(
                username=username,
                full_name=username,
                role="admin",
                password_hash=get_password_hash(password),
            )
            db.add(row)
        else:
            row.role = "admin"
            row.password_hash = get_password_hash(password)
        await db.commit()

    print("Admin created/updated:", username)


if __name__ == "__main__":
    asyncio.run(main())
