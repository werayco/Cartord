from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import UUID
from app.config import *
from app.db.session import get_db
from app.models.employee import Employee
from app.utils import (get_current_user_dep, get_tokens, cache_refresh_tokens)
from app.controllers.employee_controller import EmployeeController
from app.controllers.customer_controller import AuthController
from app.schemas import *

employee_router = APIRouter(prefix="/api/v1/auth/employee", tags=["auth"])

@employee_router.post("/register-employee", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterEmployee, db: AsyncSession = Depends(get_db), current_user: Employee = Depends(get_current_user_dep(Employee))):
    return await EmployeeController.register_employee(payload, db, current_user)

@employee_router.post("/register-inventory-manager", status_code=status.HTTP_201_CREATED)
async def register_inventory_manager(payload: RegisterEmployee, db: AsyncSession = Depends(get_db), current_user: Employee = Depends(get_current_user_dep(Employee))):
    return await EmployeeController.register_inventory_manager(payload, db, current_user)

@employee_router.delete("/{username}", status_code=status.HTTP_201_CREATED)
async def delete_user(username: str, db: AsyncSession = Depends(get_db), current_user: Employee = Depends(get_current_user_dep(Employee))):
    return await EmployeeController.delete_user(username, db, current_user)

@employee_router.get("/employees", status_code=status.HTTP_201_CREATED, response_model=list[EmployeeOut])
async def get_all_employees(db: AsyncSession = Depends(get_db), current_user: Employee = Depends(get_current_user_dep(Employee))):
    return await EmployeeController.get_all_employees(db, current_user)

@employee_router.get("/inventory-managers", status_code=status.HTTP_201_CREATED, response_model=list[EmployeeOut])
async def get_all_inventory_managers(db: AsyncSession = Depends(get_db), current_user: Employee = Depends(get_current_user_dep(Employee))):
    return await EmployeeController.get_all_inventory_managers(db, current_user)

@employee_router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await EmployeeController.login(payload, db)

@employee_router.post("/refresh")
async def refresh(payload:RefreshRequest, current_user: Employee = Depends(get_current_user_dep(Employee))):
    tokens = await cache_refresh_tokens(current_user.id,payload.refresh_token)
    return tokens

@employee_router.get("/me", response_model=EmployeeOut)
async def me(current_user: Employee = Depends(get_current_user_dep(Employee))):
    return current_user

@employee_router.post("/change-password")
async def change_password(payload: ChangePasswordRequest,current_user = Depends(get_current_user_dep(Employee)),db: AsyncSession = Depends(get_db),):
    return await AuthController.change_password(payload, current_user, db)