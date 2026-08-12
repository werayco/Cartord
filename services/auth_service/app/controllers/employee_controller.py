from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models import Employee
from app.core.config import settings
from app.core.schemas import LoginRequest, RegisterEmployee, RegisterAdmin, Roles
from app.db.session import AsyncSessionLocal
from app.core.utils import hash_password, verify_password, get_tokens


class EmployeeController:
    @staticmethod
    async def register_admin(payload: RegisterAdmin, db: AsyncSession):
        result = await db.execute(
                select(Employee).where(
                    or_(
                        Employee.email == payload.email,
                        Employee.username == payload.username,
                    )
                )
            )
        if result.scalars().first():
            return {"message": "Admin already exists", "created": True}

        try:
            data = payload.model_dump()
            data["role"] = Roles.ADMIN
            data["password"] = hash_password(data["password"])

            admin_data = Employee(**data)
            db.add(admin_data)

            await db.commit()
            await db.refresh(admin_data)
            return {"message": "Admin registered successfully", "created": True}
        except Exception as e:
            await db.rollback()
            print("error --- ", str(e))
            return {"message": "Error during admin registration", "error": str(e), "created": False}

    @staticmethod
    async def register_employee(payload: RegisterEmployee, db: AsyncSession, current_user: Employee):
        print("the user role is",current_user.role)
        if current_user.role != Roles.ADMIN:
            raise HTTPException(status_code=403, detail="Only an admin can create an employee account")

        try:
            data = payload.model_dump()
            result = await db.execute(
                select(Employee).where(
                    or_(
                        Employee.email == payload.email,
                        Employee.username == payload.username,
                    )
                )
            )
            if result.scalars().first():
                raise HTTPException(status_code=409, detail="Username already exists")

            data["role"] = Roles.EMPLOYEE
            data["password"] = hash_password(data["password"])

            add_employee = Employee(**data)
            db.add(add_employee)
            await db.commit()
            await db.refresh(add_employee)
            return {"message": "Employee registered successfully"}
        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def register_inventory_manager(payload: RegisterEmployee, db: AsyncSession, current_user: Employee):
        if current_user.role != Roles.ADMIN:
            raise HTTPException(status_code=403, detail="Only an admin can create an inventory manager account")

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

            data["role"] = Roles.INVENTORY_MANAGER
            data["password"] = hash_password(data["password"])

            add_employee = Employee(**data)
            db.add(add_employee)
            await db.commit()
            await db.refresh(add_employee)
            return {"message": "Inventory Manager registered successfully"}
        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def run():
        data = RegisterAdmin(email=settings.ADMIN_EMAIL, name=settings.ADMIN_NAME, password=settings.ADMIN_PASSWORD, username=settings.ADMIN_USERNAME)
        async with AsyncSessionLocal() as db:
            response = await EmployeeController.register_admin(payload=data, db=db)
            return "Admin Created" if response.get("created") else response["message"]

    @staticmethod
    async def get_all_employees(db: AsyncSession, current_user: Employee):
        if current_user.role != Roles.ADMIN:
            raise HTTPException(status_code=403, detail="Only an admin can view employees")
        result = await db.execute(select(Employee).where(Employee.role == Roles.EMPLOYEE))
        return result.scalars().all()

    @staticmethod
    async def get_all_inventory_managers(db: AsyncSession, current_user: Employee):
        if current_user.role != Roles.ADMIN:
            raise HTTPException(status_code=403, detail="Only an admin can view inventory managers")
        result = await db.execute(select(Employee).where(Employee.role == Roles.INVENTORY_MANAGER))
        return result.scalars().all()

    @staticmethod
    async def delete_user(username: str, db: AsyncSession, current_user: Employee):
        if current_user.role != Roles.ADMIN:
            raise HTTPException(status_code=403, detail="Only an admin can delete users")

        if username == current_user.username:
            raise HTTPException(status_code=400, detail="Admins cannot delete their own account")

        result = await db.execute(select(Employee).where(Employee.username == username))
        employee = result.scalars().first()
        if not employee:
            raise HTTPException(status_code=404, detail="User not found")

        if employee.role == Roles.ADMIN:
            raise HTTPException(status_code=403, detail="Cannot delete an admin account")

        try:
            await db.delete(employee)
            await db.commit()
            return {"message": "User deleted successfully"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
    @staticmethod
    async def login(payload: LoginRequest, db: AsyncSession):
        result = await db.execute(select(Employee).where(Employee.username == payload.username))
        Emplo = result.scalar_one_or_none()
        if not Emplo or not verify_password(payload.password, Emplo.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        tokens = await get_tokens(Emplo)
        return {"response": "Login successful", "tokens": tokens}