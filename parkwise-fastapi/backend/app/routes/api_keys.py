from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from .. import models
from ..schemas import ApiKeyCreate, ApiKeyResponse, ApiKeyListResponse
from ..security import get_current_admin_user
from ..db import get_session
from passlib.context import CryptContext
import uuid
import secrets

router = APIRouter(prefix="/api-keys")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_api_key():
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def verify_api_key(hashed, plain):
    """Verify an API key against its hash"""
    return pwd_context.verify(plain, hashed)

@router.post("/", response_model=ApiKeyResponse)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
    request: Request = None
):
    """Create a new API key - admin only"""
    # Generate a new API key
    raw_api_key = generate_api_key()
    hashed_api_key = pwd_context.hash(raw_api_key)
    
    api_key_id = str(uuid.uuid4())
    
    await session.execute(
        insert(models.api_keys).values(
            id=api_key_id,
            api_key=hashed_api_key,
            description=api_key_data.description,
            created_by=str(current_user.id),
            expires_at=api_key_data.expires_at
        )
    )
    await session.commit()
    
    # Return response with raw API key (only shown once)
    return ApiKeyResponse(
        id=api_key_id,
        api_key=raw_api_key,  # This is the raw key to be returned only once
        description=api_key_data.description,
        created_by=str(current_user.id),
        created_at=datetime.utcnow(),
        expires_at=api_key_data.expires_at,
        is_active=True,
        last_used=None
    )

@router.get("/", response_model=list[ApiKeyListResponse])
async def list_api_keys(
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """List all API keys - admin only"""
    result = await session.execute(
        select(models.api_keys)
        .where(models.api_keys.c.created_by == str(current_user.id))
        .order_by(models.api_keys.c.created_at.desc())
    )
    api_keys = result.fetchall()
    
    return [
        ApiKeyListResponse(
            id=str(api_key.id),
            description=api_key.description,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            is_active=api_key.is_active,
            last_used=api_key.last_used
        )
        for api_key in api_keys
    ]

@router.put("/{api_key_id}/activate")
async def activate_api_key(
    api_key_id: str,
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Activate an API key - admin only"""
    await session.execute(
        update(models.api_keys)
        .where(
            models.api_keys.c.id == api_key_id,
            models.api_keys.c.created_by == str(current_user.id)
        )
        .values(is_active=True)
    )
    await session.commit()
    return {"message": f"API key {api_key_id} activated"}

@router.put("/{api_key_id}/deactivate")
async def deactivate_api_key(
    api_key_id: str,
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Deactivate an API key - admin only"""
    await session.execute(
        update(models.api_keys)
        .where(
            models.api_keys.c.id == api_key_id,
            models.api_keys.c.created_by == str(current_user.id)
        )
        .values(is_active=False)
    )
    await session.commit()
    return {"message": f"API key {api_key_id} deactivated"}

@router.delete("/{api_key_id}")
async def delete_api_key(
    api_key_id: str,
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete an API key - admin only"""
    result = await session.execute(
        select(models.api_keys)
        .where(
            models.api_keys.c.id == api_key_id,
            models.api_keys.c.created_by == str(current_user.id)
        )
    )
    api_key = result.fetchone()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    await session.execute(
        models.api_keys.delete()
        .where(models.api_keys.c.id == api_key_id)
    )
    await session.commit()
    return {"message": f"API key {api_key_id} deleted"}