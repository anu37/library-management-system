from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
# from models import User
from src.models import User
from src.database import get_db
from src.schema import TokenData, Token, UserCreate, UserUpdate, UserSchema
from fastapi.encoders import jsonable_encoder
import logging

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger = logging.getLogger()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(prefix="/v1", tags=["USER_AUTH"])

def verify_password(plain_password, hash_password):
    """Verify the hashed password and plain password that is passed by the user from the form 

    Args:
        plain_password (str): The password that is entered from the API doc
        hash_password (str): hashed password key saved inuser table 

    Returns:
        bool: true if the plain password is same as hashed password 
    """
    return pwd_context.verify(plain_password, hash_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db: Session, email: str):
    """Get the user obj which is filtered based on Email ID

    Args:
        db (Session)
        email (str)

    Returns:
        user obj
    """
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str):
    """Authenticate user by checking if the user is added and by verifying the password

    Args:
        db (Session)
        email (str)
        password (str)

    Returns:
        user obj
    """
    user = get_user(db, email)
    print(user)
    if not user:
        return False
    if not verify_password(password, user.hash_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    """Get Current User is used to validate each token received as part of API invocation

    Args:
        token (Annotated[str, Depends)
        db (Session, optional): Defaults to Depends(get_db).

    Returns:
        user obj
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

def get_current_librarian(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Check if the current user role is librarian

    Args:
        current_user (User, optional): Defaults to Depends(get_current_user).
        db (Session, optional): Defaults to Depends(get_db).

    Raises:
        HTTPException: raised if the user does not have librarian privileges

    Returns:
        Current User obj
    """
    if current_user.role != "librarian":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - librarian privileges required."
        )
    return current_user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Add a user to the system 
    Args:
        user (UserCreate): Pydantic JSON structure 
        db (Session, optional): Defaults to Depends(get_db).

    Raises:
        HTTPException: Email already registered

    Returns:
        new_user
    """
    db_user = get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hash_password = get_password_hash(user.password)
    new_user = User(
        name = user.name,
        email=user.email,
        hash_password=hash_password,
        role="user",
        created_at=datetime.now(timezone.utc)
    )
    logger.info(f"user added {user.email}")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.patch("/users/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int,
    updates: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian)
):
    """To update a user role - for using this API you need to have the role of librarian 

    Args:
        user_id (int)
        updates (UserUpdate)
        db (Session, optional): Defaults to Depends(get_db).
        current_user (User, optional): Defaults to Depends(get_current_librarian).

    Raises:
        HTTPException: User not found

    Returns:
        User obj 
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    logger.info(f"user details updated: {update_data}")
    db.commit()
    db.refresh(user)

    return jsonable_encoder(user)


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.get("/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

