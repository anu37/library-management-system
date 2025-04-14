from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from src.models import Role

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[Role] = "user"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Role] = None


class UserSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    model_config = {
        "from_attributes": True
    }

class UserInDB(UserSchema):
    hashed_password: str

class BookCreate(BaseModel):
    title: str
    author: Optional[str] = None
    category_id: Optional[int] = None
    no_of_copies: int = 1

class BookOut(BaseModel):
    id: int
    title: str
    author: Optional[str]
    category_id: Optional[int]
    no_of_copies: int
    available_copies: int

    model_config = {
        "from_attributes": True
    }

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category_id: Optional[int] = None
    no_of_copies: Optional[int] = None
    available_copies: Optional[int] = None

class BorrowOut(BaseModel):
    id: int
    book_id: int
    user_id: int
    borrow_date: date
    status: str

    model_config = {
        "from_attributes": True
    }

class CategoryCreate(BaseModel):
    name: str

class CategoryOut(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }