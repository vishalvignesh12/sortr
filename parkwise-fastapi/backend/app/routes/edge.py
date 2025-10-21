from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from .. import models
from ..db import get_session
from ..cache import get_slot_list, set_slot_list, get_slot_status, set_slot_status
from datetime import datetime
from typing import List, Optional

router = APIRouter(prefix="/v1/edge")

# Dependency to verify edge API key
async def check_edge_api_key(request: Request):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # In a real implementation, you'd check the API key against a database
    # For now, we'll allow any key for development purposes
    # EDGE_API_KEY should be defined in your settings
    from ..core import settings
    if api_key != settings.EDGE_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@router.get("/slots")
async def get_all_slots_edge(
    session: AsyncSession = Depends(get_session)
):
    """
    Get all parking slots with their status - for edge devices and frontend
    This endpoint is accessible without authentication for edge devices with API key
    """
    try:
        # Check cache first
        cached_slots = await get_slot_list()
        if cached_slots:
            return cached_slots

        # Query slots with their status
        result = await session.execute(
            text("""
                SELECT 
                    s.slot_id as slot_id,
                    s.zone_id,
                    s.polygon,
                    s.vehicle_type_hint,
                    COALESCE(ss.occupied, FALSE) as occupied,
                    COALESCE(ss.confidence, 1.0) as confidence,
                    ss.vehicle_type,
                    ss.last_seen,
                    ss.reserved_until,
                    ss.predicted_free_minutes,
                    ss.prediction_confidence
                FROM slots s
                LEFT JOIN slot_status ss ON s.slot_id = ss.slot_id
                ORDER BY s.slot_id
            """)
        )
        
        rows = result.fetchall()
        slots = []
        for row in rows:
            slot_data = {
                "slot_id": row.slot_id,
                "zone_id": row.zone_id,
                "polygon": row.polygon,
                "vehicle_type_hint": row.vehicle_type_hint,
                "occupied": row.occupied,
                "confidence": float(row.confidence) if row.confidence else 1.0,
                "vehicle_type": row.vehicle_type,
                "last_seen": row.last_seen.isoformat() if row.last_seen else None,
                "reserved_until": row.reserved_until.isoformat() if row.reserved_until else None,
                "predicted_free_minutes": row.predicted_free_minutes,
                "prediction_confidence": row.prediction_confidence
            }
            slots.append(slot_data)

        # Cache the result
        await set_slot_list(slots)
        
        return slots
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving slots: {str(e)}")


@router.get("/slots/{slot_id}")
async def get_slot_by_id_edge(
    slot_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific parking slot by ID - for edge devices and frontend
    """
    try:
        # Check cache first
        cached_slot = await get_slot_status(slot_id)
        if cached_slot:
            return cached_slot

        # Query the specific slot with its status
        result = await session.execute(
            text("""
                SELECT 
                    s.slot_id as slot_id,
                    s.zone_id,
                    s.polygon,
                    s.vehicle_type_hint,
                    COALESCE(ss.occupied, FALSE) as occupied,
                    COALESCE(ss.confidence, 1.0) as confidence,
                    ss.vehicle_type,
                    ss.last_seen,
                    ss.reserved_until,
                    ss.predicted_free_minutes,
                    ss.prediction_confidence
                FROM slots s
                LEFT JOIN slot_status ss ON s.slot_id = ss.slot_id
                WHERE s.slot_id = :slot_id
            """),
            {"slot_id": slot_id}
        )
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Slot {slot_id} not found")

        slot_data = {
            "slot_id": row.slot_id,
            "zone_id": row.zone_id,
            "polygon": row.polygon,
            "vehicle_type_hint": row.vehicle_type_hint,
            "occupied": row.occupied,
            "confidence": float(row.confidence) if row.confidence else 1.0,
            "vehicle_type": row.vehicle_type,
            "last_seen": row.last_seen.isoformat() if row.last_seen else None,
            "reserved_until": row.reserved_until.isoformat() if row.reserved_until else None,
            "predicted_free_minutes": row.predicted_free_minutes,
            "prediction_confidence": row.prediction_confidence
        }

        # Cache the result
        await set_slot_status(slot_id, slot_data)
        
        return slot_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving slot {slot_id}: {str(e)}")


@router.post("/slots/{slot_id}/update")
async def update_slot_status_edge(
    slot_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """
    Update a parking slot status from edge device (camera, sensor, etc.)
    Requires edge API key
    """
    # Verify edge API key
    await check_edge_api_key(request)
    
    try:
        # Parse the request body
        body = await request.json()
        occupied = body.get('occupied', None)
        confidence = body.get('confidence', 1.0)
        vehicle_type = body.get('vehicle_type', 'unknown')
        
        if occupied is None:
            raise HTTPException(status_code=400, detail="occupied field is required")
        
        # Update the slot status in the database
        await session.execute(
            text("""
                INSERT INTO slot_status (slot_id, occupied, confidence, vehicle_type, last_seen, updated_at)
                VALUES (:slot_id, :occupied, :confidence, :vehicle_type, now(), now())
                ON CONFLICT (slot_id) 
                DO UPDATE SET 
                    occupied = EXCLUDED.occupied,
                    confidence = EXCLUDED.confidence,
                    vehicle_type = EXCLUDED.vehicle_type,
                    last_seen = EXCLUDED.last_seen,
                    updated_at = now()
            """),
            {
                "slot_id": slot_id,
                "occupied": occupied,
                "confidence": confidence,
                "vehicle_type": vehicle_type
            }
        )
        await session.commit()
        
        # Invalidate cache
        from ..cache import invalidate_slot_list
        await invalidate_slot_list()
        await set_slot_status(slot_id, {
            "slot_id": slot_id,
            "occupied": occupied,
            "confidence": confidence,
            "vehicle_type": vehicle_type,
            "last_seen": datetime.utcnow().isoformat()
        })
        
        # Send WebSocket notification about the slot update
        from ..websocket import notify_slot_update
        await notify_slot_update(slot_id, {
            "slot_id": slot_id,
            "occupied": occupied,
            "confidence": confidence,
            "vehicle_type": vehicle_type,
            "last_seen": datetime.utcnow().isoformat()
        })
        
        return {"message": f"Slot {slot_id} status updated successfully", "slot_id": slot_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating slot {slot_id}: {str(e)}")


@router.get("/health")
async def edge_health():
    """
    Health check for edge API
    """
    return {"status": "healthy", "service": "edge-api", "timestamp": datetime.utcnow().isoformat()}