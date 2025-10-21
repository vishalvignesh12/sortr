from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .. import models
from ..schemas import User
from ..security import get_current_user, get_current_admin_user
from ..db import get_session

router = APIRouter(prefix="/users")

@router.get("/me", response_model=User)
async def get_current_user_profile(current_user = Depends(get_current_user)):
    return current_user

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str, current_user = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # Only allow users to view their own profile unless they are admin
    if str(current_user.id) != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )
    
    result = await session.execute(
        select(models.users).where(models.users.c.id == user_id)
    )
    user = result.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.get("/", response_model=list[User])
async def get_users(current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Get all users - admin only"""
    result = await session.execute(
        select(models.users)
    )
    users = result.fetchall()
    return users