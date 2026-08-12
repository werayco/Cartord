from enum import Enum
from pydantic import BaseModel, ConfigDict

class RegisterRequest(BaseModel):
    email: str
    name: str
    username: str
    password: str
    shipping_address: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class RefreshRequest(BaseModel):
    refresh_token: str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class Roles(Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    INVENTORY_MANAGER = "inventory_manager"

class RegisterEmployee(BaseModel):
    email: str
    name: str
    role: Roles = "employee"
    password: str

class RegisterAdmin(BaseModel):
    email: str
    name: str
    password: str
    username: str

class EmployeeOut(BaseModel):
    email: str
    name: str
    username: str
    role: str
    model_config = {"from_attributes": True}

class RegisterEmployee(BaseModel):
    email: str
    name: str
    password: str
    username: str

class DeleteUser(BaseModel):
    username: str
    password: str

class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    username: str
    name: str
    shipping_address: str | None

class UpdateUser(BaseModel):
    email: str | None = None
    name: str | None = None
    username: str | None = None
    shipping_address: str | None = None