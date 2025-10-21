from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from . import models
from .db import get_session
from datetime import datetime
import uuid

async def log_audit(
    session: AsyncSession,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str = None,
    details: dict = None,
    request: Request = None
):
    """
    Log an audit event to the audit_logs table
    """
    ip_address = None
    user_agent = None
    
    if request:
        # Get IP address (considering proxies)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip_address = forwarded.split(",")[0]
        else:
            ip_address = request.client.host if request.client else None
            
        user_agent = request.headers.get("user-agent")
    
    # Create audit log entry
    audit_log_id = str(uuid.uuid4())
    
    await session.execute(
        insert(models.audit_logs).values(
            id=audit_log_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    )
    await session.commit()

# Example usage functions for common audit events
async def log_user_login(session: AsyncSession, user_id: str, request: Request = None):
    await log_audit(session, user_id, "user_login", "user", user_id, {}, request)

async def log_booking_create(session: AsyncSession, user_id: str, booking_id: str, request: Request = None):
    await log_audit(session, user_id, "create_booking", "booking", booking_id, {}, request)

async def log_payment_process(session: AsyncSession, user_id: str, payment_id: str, details: dict = None, request: Request = None):
    await log_audit(session, user_id, "process_payment", "payment", payment_id, details or {}, request)

async def log_slot_update(session: AsyncSession, user_id: str = None, slot_id: str = None, request: Request = None):
    await log_audit(session, user_id, "update_slot_status", "slot", slot_id, {}, request)

async def log_admin_action(session: AsyncSession, user_id: str, action: str, resource_type: str, resource_id: str = None, details: dict = None, request: Request = None):
    await log_audit(session, user_id, action, resource_type, resource_id, details or {}, request)