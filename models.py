from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    last_login: Optional[datetime]
    created_at: datetime

class NoteCreate(BaseModel):
    title: str
    content: str

class Note(BaseModel):
    id: int
    title: str
    content: str
    user_id: int
    created_at: datetime
    updated_at: datetime

class NoteUpdate(BaseModel):
    title: str
    content: str

class UserActivity(BaseModel):
    id: int
    user_id: int
    activity_type: str
    description: str
    ip_address: Optional[str]
    created_at: datetime