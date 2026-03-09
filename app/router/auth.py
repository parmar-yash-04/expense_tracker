from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import User
from app.oauth2 import create_access_token
from app.utils import verify_password, hash_password
from app.schemas import TokenResponse, UserCreate, UserResponse
from app.security_logger import log_failed_authentication

router = APIRouter(prefix="/auth", tags=["Authentication"])

DUMMY_PASSWORD_HASH = "$2b$12$t5YsPYR5xHa.jJv92L.Yguv7xxkln2QafjpWn9kBJ0ElCy.j4dPqm"


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.email == username).first()
    
    if not user:
        verify_password(password, DUMMY_PASSWORD_HASH)
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        if existing_user.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = hash_password(user_data.password)
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db), request: Request = None):
    client_ip = request.client.host if request and request.client else "unknown"
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    
    if not user:
        log_failed_authentication(user_credentials.username, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(data={"user_id": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}
