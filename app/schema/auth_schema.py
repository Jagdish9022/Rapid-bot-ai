from datetime import datetime
from pydantic import BaseModel, EmailStr
 
class UserBase(BaseModel):
    email: EmailStr
    username: str
 
class UserCreate(UserBase):
    password: str
 
class UserLogin(BaseModel):
    email: EmailStr
    password: str
 
class User(UserBase):
    id: str
    created_at: datetime
    is_active: bool = True
 
    class Config:
        from_attributes = True
 
class Token(BaseModel):
    access_token: str
    token_type: str
 