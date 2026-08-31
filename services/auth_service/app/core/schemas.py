from enum import Enum
from pydantic import BaseModel, ConfigDict
from uuid import UUID

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
    SELLER = "seller"

class RegisterSeller(BaseModel):
    email: str
    name: str
    password: str
    username: str

class RegisterAdmin(BaseModel):
    email: str
    name: str
    password: str
    username: str

class SellerOut(BaseModel):
    id: UUID
    email: str
    name: str
    username: str
    role: str
    model_config = {"from_attributes": True}
    
class DeleteUser(BaseModel):
    username: str
    password: str

class BuyerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    username: str
    name: str
    shipping_address: str | None
    id: UUID

class UpdateUser(BaseModel):
    email: str | None = None
    name: str | None = None
    username: str | None = None
    shipping_address: str | None = None