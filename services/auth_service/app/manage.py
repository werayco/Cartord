import asyncio
import argparse
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from app.db.session import AsyncSessionLocal
from app.models import Employee
from app.core.utils import hash_password
from app.core.schemas import Roles


def parse_args():
    parser = argparse.ArgumentParser(description="Update an Admin")
    parser.add_argument("--email", type=str, required=True, help="Admin Email (to find the admin)")
    parser.add_argument("--name", type=str, help="New name")
    parser.add_argument("--username", type=str, help="New username")
    parser.add_argument("--password", type=str, help="New password")
    return parser.parse_args()


async def update_admin(email: str, password: str | None, name: str | None, username: str | None):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Employee).where(Employee.email == email, Employee.role == Roles.ADMIN.value)
        )
        admin = result.scalars().first()
        if not admin:
            print("No admin found with that email")
            return

        if username and username != admin.username:
            existing = await db.execute(
                select(Employee).where(Employee.username == username, Employee.id != admin.id)
            )
            if existing.scalars().first():
                print(f"Username '{username}' is already taken")
                return
            admin.username = username

        if name:
            admin.name = name
        if password:
            admin.password = hash_password(password)

        try:
            await db.commit()
            print("Admin updated")
        except IntegrityError as e:
            await db.rollback()
            print(f"Update failed: {e}")


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(update_admin(args.email, args.password, args.name, args.username))