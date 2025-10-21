from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from .. import models
from ..schemas import NotificationCreate
from ..security import get_current_user
from ..db import get_session
import uuid
from datetime import datetime

router = APIRouter(prefix="/notifications")

@router.post("/", response_model=dict)
async def create_notification(
    notification_data: NotificationCreate,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a notification
    If no user_id is provided, it creates a notification for the current user
    """
    # Determine who to send the notification to
    target_user_id = notification_data.user_id or str(current_user.id)
    
    # If user_id is provided, only admins can send notifications to other users
    if notification_data.user_id and str(current_user.id) != notification_data.user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to send notifications to other users"
        )
    
    notification_id = str(uuid.uuid4())
    
    await session.execute(
        insert(models.notifications).values(
            id=notification_id,
            user_id=target_user_id,
            type=notification_data.type,
            message=notification_data.message
        )
    )
    await session.commit()
    
    return {
        "id": notification_id,
        "type": notification_data.type,
        "message": notification_data.message,
        "user_id": target_user_id
    }

@router.get("/", response_model=list)
async def get_user_notifications(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get all notifications for the current user"""
    result = await session.execute(
        select(models.notifications)
        .where(models.notifications.c.user_id == str(current_user.id))
        .order_by(models.notifications.c.sent_at.desc())
    )
    notifications = result.fetchall()
    
    return [
        {
            "id": str(notification.id),
            "type": notification.type,
            "message": notification.message,
            "is_read": notification.is_read,
            "sent_at": notification.sent_at
        }
        for notification in notifications
    ]

@router.get("/unread", response_model=list)
async def get_unread_notifications(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get all unread notifications for the current user"""
    result = await session.execute(
        select(models.notifications)
        .where(
            models.notifications.c.user_id == str(current_user.id),
            models.notifications.c.is_read == False
        )
        .order_by(models.notifications.c.sent_at.desc())
    )
    notifications = result.fetchall()
    
    return [
        {
            "id": str(notification.id),
            "type": notification.type,
            "message": notification.message,
            "is_read": notification.is_read,
            "sent_at": notification.sent_at
        }
        for notification in notifications
    ]

@router.put("/{notification_id}/read", response_model=dict)
async def mark_notification_as_read(
    notification_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Mark a notification as read"""
    result = await session.execute(
        select(models.notifications)
        .where(
            models.notifications.c.id == notification_id,
            models.notifications.c.user_id == str(current_user.id)
        )
    )
    notification = result.fetchone()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    await session.execute(
        models.notifications.update()
        .where(models.notifications.c.id == notification_id)
        .values(is_read=True)
    )
    await session.commit()
    
    return {"message": "Notification marked as read"}

@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(
    notification_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a notification"""
    result = await session.execute(
        select(models.notifications)
        .where(
            models.notifications.c.id == notification_id,
            models.notifications.c.user_id == str(current_user.id)
        )
    )
    notification = result.fetchone()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    await session.execute(
        models.notifications.delete()
        .where(models.notifications.c.id == notification_id)
    )
    await session.commit()
    
    return {"message": "Notification deleted"}