from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum, unique
from sqlalchemy.sql import func

from src.database import Base

@unique
class Role(str, PyEnum):
    admin = 'admin'
    user = 'user'
    librarian = "librarian"

@unique
class BorrowStatus(str, PyEnum):
    borrowed = 'borrowed'
    returned = "returned"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hash_password = Column(Text, nullable=False)
    role = Column(Enum(Role), default=Role.user, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    borrow_history = relationship("BorrowLog", back_populates="user")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(250), nullable=False, unique=True)
    author = Column(String(255), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    no_of_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    category = relationship("Category", back_populates="books")
    borrow_records = relationship("BorrowLog", back_populates="book")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    books = relationship("Book", back_populates="category")

class BorrowLog(Base):
    __tablename__ = "borrow_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="borrow_history")
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    book = relationship("Book", back_populates="borrow_records")
    borrow_date = Column(Date, server_default=func.current_date())
    status = Column(Enum(BorrowStatus), default=BorrowStatus.borrowed, nullable=False)