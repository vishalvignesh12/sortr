from fastapi import APIRouter, HTTPException, Depends, Request
from ..schemas import HoldRequest, HoldResponse
from ..db import get_session
from ..core import settings
from ..audit import log_booking_create
from sqlalchemy import text
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/v1/bookings")

# In a production system, you would use Redis for distributed locks
# For this development setup, we'll implement a simple in-memory lock
# which works for single-server deployments
import asyncio
from typing import Dict
from contextlib import contextmanager

# Simple in-memory lock implementation for development
_locks: Dict[str, asyncio.Lock] = {}
_locks_lock = asyncio.Lock()  # lock to protect access to the locks dict

async def _acquire_slot_lock(slot_id: str, ttl_ms=5000):
    """Acquire a lock for a specific slot ID"""
    async with _locks_lock:
        if slot_id not in _locks:
            _locks[slot_id] = asyncio.Lock()
        lock = _locks[slot_id]
    
    # Try to acquire the lock
    if lock.locked():
        return None  # Lock is already held by another request
    else:
        await lock.acquire()
        return lock  # Successfully acquired the lock

async def _release_slot_lock(slot_id: str, lock):
    """Release a lock for a specific slot ID"""
    if lock:
        lock.release()
        # Optionally clean up the lock after release
        async with _locks_lock:
            if slot_id in _locks and not _locks[slot_id].locked():
                del _locks[slot_id]

@router.post("/hold", response_model=HoldResponse)
async def hold_slot(req: HoldRequest, request: Request, session=Depends(get_session)):
    # Acquire a lock for the slot to prevent race conditions
    lock = await _acquire_slot_lock(req.slot_id, ttl_ms=5000)
    if not lock:
        raise HTTPException(status_code=429, detail="Try again")

    try:
        # transaction: SELECT FOR UPDATE -> insert booking -> update slot_status.reserved_until
        async with session.begin():
            # For SQLite, we use different locking mechanism
            # In a real PostgreSQL setup, FOR UPDATE would work
            r = await session.execute(text("""
                SELECT * FROM slot_status WHERE slot_id = :slot_id
            """), {'slot_id': req.slot_id})
            row = r.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="slot not found")
            now = datetime.utcnow()
            if row.reserved_until and row.reserved_until > now:
                raise HTTPException(status_code=409, detail="slot already reserved")
            if row.occupied:
                raise HTTPException(status_code=409, detail="slot occupied")
            hold_until = now + timedelta(minutes=req.hold_minutes)
            booking_id = str(uuid.uuid4())
            await session.execute(text("""
                INSERT INTO bookings (id, user_id, slot_id, status, hold_until) 
                VALUES (:id, :user_id, :slot_id, :status, :hold_until)
            """), {
                'id': booking_id, 
                'user_id': req.user_id, 
                'slot_id': req.slot_id, 
                'status': 'holding', 
                'hold_until': hold_until
            })
            await session.execute(text("""
                UPDATE slot_status SET reserved_until = :hold_until WHERE slot_id = :slot_id
            """), {'hold_until': hold_until, 'slot_id': req.slot_id})
        
        # Log the booking creation
        if req.user_id:
            await log_booking_create(session, req.user_id, booking_id, request)
        
        return HoldResponse(booking_id=booking_id, hold_until=hold_until)
    finally:
        # Release the lock
        await _release_slot_lock(req.slot_id, lock)