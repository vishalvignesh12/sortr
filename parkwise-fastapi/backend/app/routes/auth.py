from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from .. import models
from ..schemas import UserCreate, UserLogin, Token, RefreshTokenRequest
from ..security import verify_password, get_password_hash, create_access_token, create_refresh_token
from ..db import get_session
from ..audit import log_user_login
from datetime import timedelta
import uuid

router = APIRouter(prefix="/auth")

security = HTTPBearer()

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, request: Request, session: AsyncSession = Depends(get_session)):
    # Check if user already exists
    result = await session.execute(
        select(models.users).where(models.users.c.email == user_data.email)
    )
    existing_user = result.fetchone()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user_id = str(uuid.uuid4())
    
    await session.execute(
        insert(models.users).values(
            id=user_id,
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
    )
    await session.commit()
    
    # Create tokens
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, request: Request, session: AsyncSession = Depends(get_session)):
    # Find user by email
    result = await session.execute(
        select(models.users).where(models.users.c.email == user_data.email)
    )
    user = result.fetchone()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log the login event
    await log_user_login(session, str(user.id), request)
    
    # Create tokens
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.post("/refresh")
async def refresh_token(token_request: RefreshTokenRequest, request: Request):
    # In a real implementation, you would validate the refresh token
    # For this example, we'll just create new tokens
    # In production, refresh tokens should be stored and validated properly
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token implementation requires a secure storage mechanism"
    )