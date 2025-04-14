from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.models import Book, BorrowLog, User, Category

from src.schema import BookCreate, BookOut, BookUpdate, BorrowOut, CategoryOut, CategoryCreate

from src.database import get_db

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiting based on client IP
limiter = Limiter(key_func=get_remote_address)

import logging
import datetime

from src.auth_api import get_current_user, get_current_librarian


router = APIRouter(prefix="/v1", tags=["BOOKS_API"])

logger = logging.getLogger()


@router.post("/books/", response_model=BookOut)
@limiter.limit("5/minute")
def add_book(request: Request, book: BookCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_librarian)):
    """API to add books

    Args:
        request (Request)
        book (BookCreate)
        db (Session, optional): Defaults to Depends(get_db).
        current_user (User, optional): Defaults to Depends(get_current_librarian).

    Returns:
        Book obj
    """
    new_book = Book(**book.dict())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    logger.info(f"book added by {current_user.email}: {book.title}")
    return new_book

@router.put("/books/{book_id}", response_model=BookOut)
@limiter.limit("5/minute")
def update_book(request: Request, book_id: int, book: BookUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_librarian)):
    """update the details of the book

    Args:
        request (Request)
        book_id (int)
        book (BookUpdate)
        db (Session, optional) Defaults to Depends(get_db).
        current_user (User, optional) Defaults to Depends(get_current_librarian).

    Raises:
        HTTPException

    Returns:
        _type_
    """
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="book not found")
    for field, value in book.dict(exclude_unset=True).items():
        setattr(db_book, field, value)
    db.commit()
    db.refresh(db_book)
    logger.info(f"book updated by {current_user.email}: {book_id}")
    return db_book

@router.delete("/books/{book_id}", status_code=204)
@limiter.limit("5/minute")
def delete_book(request: Request, book_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_librarian)):
    """Delere a book based on the ID 

    Args:
        request (Request)
        book_id (int)
        db (Session, optional). Defaults to Depends(get_db).
        current_user (User, optional). Defaults to Depends(get_current_librarian).

    Raises:
        HTTPException
    """
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="book not found")
    db.delete(db_book)
    db.commit()
    logger.info(f"book deleted by {current_user.email}- {book_id}")


@router.get("/books/search", response_model=List[BookOut])
@limiter.limit("5/minute")
def search_books(request: Request, title: Optional[str] = Query(None), author: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Search for a book based on the author or title"""
    query = db.query(Book)
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))
    return query.all()


@router.post("/books/borrow/{book_id}", response_model=BorrowOut)
@limiter.limit("5/minute")
def borrow_book(request: Request, book_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """API to borrow a book in the library system, check if the book is availabel and reduce the available_copies

    Args:
        request (Request)
        book_id (int)
        db (Session, optional). Defaults to Depends(get_db).
        current_user (User, optional). Defaults to Depends(get_current_user).
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book or book.available_copies < 1:
        raise HTTPException(status_code=400, detail="book not available")
    existing_borrow = db.query(BorrowLog).filter(BorrowLog.user_id == current_user.id, BorrowLog.book_id == book_id).first()
    if existing_borrow:
        raise HTTPException(status_code=400, detail="you already borrowed this book")
    borrow_entry = BorrowLog(user_id=current_user.id, book_id=book_id)
    book.available_copies -= 1
    db.add(borrow_entry)
    db.commit()
    db.refresh(borrow_entry)
    logger.info(f"{current_user.email} borrowed book {book_id}")
    return borrow_entry


@router.post("/books/return/{book_id}", response_model=BorrowOut)
@limiter.limit("5/minute")
def return_book(request: Request, book_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """API to return the book and incerase the available copies

    Args:
        request (Request): 
        book_id (int): 
        db (Session, optional): Defaults to Depends(get_db).
        current_user (User, optional): Defaults to Depends(get_current_user).
    """
    borrow_entry = db.query(BorrowLog).filter(BorrowLog.user_id == current_user.id, BorrowLog.book_id == book_id).first()
    if not borrow_entry:
        raise HTTPException(status_code=400, detail="you haven't borrowed this book")
    book = db.query(Book).filter(Book.id == book_id).first()
    book.available_copies += 1
    db.commit()
    db.refresh(borrow_entry)
    logger.info(f"{current_user.email} returned book {book_id}")
    return borrow_entry


@router.get("/users/history", response_model=List[BorrowOut])
@limiter.limit("5/minute")
def get_borrow_history(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get Borrow History of a User who is logged in"""
    return db.query(BorrowLog).filter(BorrowLog.user_id == current_user.id).all()


@router.post("/categories/", response_model=CategoryOut)
@limiter.limit("5/minute")
def create_category(request: Request, category: CategoryCreate, db: Session = Depends(get_db)):
    """ API to add category of books """
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category