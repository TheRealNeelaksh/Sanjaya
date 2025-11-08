import bcrypt
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from sqlalchemy.orm import Session
from . import models

# Load environment variables
load_dotenv(dotenv_path="project_sanjaya/.env")
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")

if not SECRET_KEY or not JWT_SECRET:
    raise ValueError("SECRET_KEY and JWT_SECRET must be set in the .env file")

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against its hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_jwt_token(data: dict, expires_delta: timedelta = timedelta(hours=24)):
    """Creates a JWT token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")

def decode_jwt_token(token: str):
    """Decodes a JWT token."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None

def register_user(db: Session, username: str, password: str, role: str) -> models.User:
    """Registers a new user."""
    password_hash = hash_password(password)
    new_user = models.User(username=username, password_hash=password_hash, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def login_user(db: Session, username: str, password: str):
    """Logs in a user and returns a JWT token."""
    user = db.query(models.User).filter(models.User.username == username).first()
    if user and verify_password(password, user.password_hash):
        if user.role == 'child':
            return create_jwt_token(data={"sub": user.username, "role": user.role}, expires_delta=timedelta(hours=24))
        else:
            return create_jwt_token(data={"sub": user.username, "role": user.role})
    return None

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_jwt_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not an admin",
        )
    return current_user

def admin_user_exists(db: Session) -> bool:
    """Checks if an admin user exists."""
    return db.query(models.User).filter(models.User.role == "admin").first() is not None

# TODO: Add more robust error handling and user feedback.
