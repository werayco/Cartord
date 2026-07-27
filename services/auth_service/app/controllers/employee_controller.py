from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models import Employee
from app.config import settings
from app.schemas import RegisterEmployee, Roles, RegisterAdmin
from app.schemas import (ChangePasswordRequest,LoginRequest,RegisterRequest,TokenResponse)
from app.utils import (hash_password,verify_password,get_tokens)

class EmployeeController:
    @staticmethod
    async def register_admin(payload: RegisterAdmin, db: AsyncSession):
        result = await db.execute(
            select(func.count()).select_from(Employee).where(Employee.role == Roles.ADMIN.value)
        )
        admin_count = result.scalar_one()

        if admin_count >= settings.ADMIN_COUNT:
            raise HTTPException(status_code=409, detail="An admin already exists")

        try:
            data = payload.model_dump()
            data["role"] = Roles.ADMIN.value
            data["password"] = hash_password(data["password"])

            add_admin = Employee(**data)
            db.add(add_admin)
            await db.commit()
            await db.refresh(add_admin)
            return {"message": "Admin registered successfully"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
    @staticmethod
    async def register_employee(payload: RegisterEmployee, db: AsyncSession):
        try:
            data = payload.model_dump()
            result = await db.execute(
                select(Employee).where(
                    or_(
                        Employee.email == data.get("email"),
                        Employee.username == data.get("username"),
                    )
                )
            )
            if result.scalars().first():
                raise HTTPException(status_code=409, detail="Username already exists")

            data["is_admin"] = False
            data["password"] = hash_password(data["password"])

            add_employee = Employee(**data)
            db.add(add_employee)
            await db.commit()
            await db.refresh(add_employee)
            return {"message": "Employee registered successfully", "id": str(add_employee.id)}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    async def register_inventory_manager(payload: RegisterEmployee, db: AsyncSession):
        try:
            data = payload.model_dump()
            result = await db.execute(
                select(Employee).where(
                    or_(
                        Employee.email == data.get("email"),
                        Employee.username == data.get("username"),
                    )
                )
            )
            if result.scalars().first():
                raise HTTPException(status_code=409, detail="Username already exists")

            data["role"] = Roles.INVENTORY_MANAGER.value
            data["password"] = hash_password(data["password"])

            add_employee = Employee(**data)
            db.add(add_employee)
            await db.commit()
            await db.refresh(add_employee)
            return {"message": "Inventory Manager registered successfully"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
