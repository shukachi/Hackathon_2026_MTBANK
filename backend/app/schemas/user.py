from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import RoleEnum


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    role: RoleEnum
    full_name: str
    age: int | None
    family_id: int
    parent_id: int | None
    created_at: datetime


class RegisterRequest(BaseModel):
    login: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    login: str
    password: str
