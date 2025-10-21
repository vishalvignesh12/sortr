from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from .. import models
from ..schemas import AdminStats
from ..security import get_current_admin_user
from ..db import get_session

router = APIRouter(prefix="/admin")

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Get comprehensive system statistics - admin only"""
    # Get total users
    result = await session.execute(select(func.count(models.users.c.id)))
    total_users = result.scalar()
    
    # Get active bookings
    result = await session.execute(
        select(func.count(models.bookings.c.id))
        .where(models.bookings.c.status == 'holding')
    )
    active_bookings = result.scalar()
    
    # Get slot statistics
    result = await session.execute(
        select(func.count(models.slot_status.c.slot_id))
        .where(models.slot_status.c.occupied == False)
    )
    available_slots = result.scalar()
    
    result = await session.execute(
        select(func.count(models.slot_status.c.slot_id))
        .where(models.slot_status.c.occupied == True)
    )
    occupied_slots = result.scalar()
    
    return AdminStats(
        total_users=total_users,
        active_bookings=active_bookings,
        available_slots=available_slots,
        occupied_slots=occupied_slots
    )

@router.get("/users")
async def get_all_users(current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Get all users with details - admin only"""
    result = await session.execute(
        select(models.users).order_by(models.users.c.created_at.desc())
    )
    users = result.fetchall()
    
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        for user in users
    ]

@router.get("/bookings")
async def get_all_bookings(current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Get all bookings - admin only"""
    result = await session.execute(
        select(models.bookings).order_by(models.bookings.c.created_at.desc())
    )
    bookings = result.fetchall()
    
    return [
        {
            "id": str(booking.id),
            "user_id": str(booking.user_id) if booking.user_id else None,
            "slot_id": booking.slot_id,
            "status": booking.status,
            "hold_until": booking.hold_until,
            "created_at": booking.created_at,
            "updated_at": booking.updated_at
        }
        for booking in bookings
    ]

@router.get("/slots")
async def get_all_slots(current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Get all slots with status - admin only"""
    result = await session.execute(
        select(models.slots, models.slot_status)
        .select_from(models.slots.outerjoin(models.slot_status))
        .order_by(models.slots.c.slot_id)
    )
    slot_data = result.fetchall()
    
    return [
        {
            "slot_id": slot.slot_id,
            "zone_id": slot.zone_id,
            "polygon": slot.polygon,
            "vehicle_type_hint": slot.vehicle_type_hint,
            "occupied": slot_status.occupied if slot_status else False,
            "confidence": slot_status.confidence if slot_status else 1.0,
            "vehicle_type": slot_status.vehicle_type if slot_status else None,
            "last_seen": slot_status.last_seen if slot_status else None,
            "reserved_until": slot_status.reserved_until if slot_status else None,
            "predicted_free_minutes": slot_status.predicted_free_minutes if slot_status else None,
            "prediction_confidence": slot_status.prediction_confidence if slot_status else None,
            "updated_at": slot_status.updated_at if slot_status else slot.updated_at
        }
        for slot, slot_status in slot_data
    ]

@router.get("/payments")
async def get_all_payments(current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Get all payments - admin only"""
    result = await session.execute(
        select(models.payments).order_by(models.payments.c.created_at.desc())
    )
    payments = result.fetchall()
    
    return [
        {
            "id": str(payment.id),
            "user_id": str(payment.user_id),
            "booking_id": str(payment.booking_id),
            "amount": payment.amount,
            "status": payment.status,
            "payment_method": payment.payment_method,
            "transaction_id": payment.transaction_id,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at
        }
        for payment in payments
    ]

@router.put("/users/{user_id}/activate")
async def activate_user(user_id: str, current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Activate a user account - admin only"""
    await session.execute(
        models.users.update()
        .where(models.users.c.id == user_id)
        .values(is_active=True)
    )
    await session.commit()
    return {"message": f"User {user_id} activated"}

@router.put("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Deactivate a user account - admin only"""
    await session.execute(
        models.users.update()
        .where(models.users.c.id == user_id)
        .values(is_active=False)
    )
    await session.commit()
    return {"message": f"User {user_id} deactivated"}

@router.put("/users/{user_id}/make-admin")
async def make_admin(user_id: str, current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Grant admin privileges to a user - admin only"""
    await session.execute(
        models.users.update()
        .where(models.users.c.id == user_id)
        .values(is_admin=True)
    )
    await session.commit()
    return {"message": f"User {user_id} granted admin privileges"}

@router.put("/users/{user_id}/remove-admin")
async def remove_admin(user_id: str, current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Remove admin privileges from a user - admin only"""
    # Prevent removing admin privileges from themselves
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove admin privileges from yourself"
        )
    
    await session.execute(
        models.users.update()
        .where(models.users.c.id == user_id)
        .values(is_admin=False)
    )
    await session.commit()
    return {"message": f"Admin privileges removed from user {user_id}"}