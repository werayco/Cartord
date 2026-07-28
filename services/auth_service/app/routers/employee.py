from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import *
from app.db.session import get_db
from app.models.employee import Employee
from app.utils import (get_current_user_dep, get_tokens)
from app.controllers.employee_controller import EmployeeController
from app.controllers.customer_controller import AuthController
from app.schemas import *

employee_router = APIRouter(prefix="/api/v1/auth/employee", tags=["auth"])

@employee_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterEmployee, db: AsyncSession = Depends(get_db), current_user: Employee = Depends(get_current_user_dep(Employee))):
    return await EmployeeController.register_employee(payload, db, current_user)

@employee_router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthController.login(payload, db, table=Employee)

@employee_router.post("/refresh")
async def refresh(current_user: Employee = Depends(get_current_user_dep(Employee))):
    tokens = await get_tokens(current_user)
    return tokens

@employee_router.get("/me")
async def me(current_user: Employee = Depends(get_current_user_dep(Employee))):
    return current_user

@employee_router.post("/change-password")
async def change_password(payload: ChangePasswordRequest,current_user = Depends(get_current_user_dep(Employee)),db: AsyncSession = Depends(get_db),):
    return await AuthController.change_password(payload, current_user, db)