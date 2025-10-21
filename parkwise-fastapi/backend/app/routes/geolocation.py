from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from .. import models
from ..schemas import GeoSearchRequest, GeoUpdate
from ..security import get_current_user, get_current_admin_user
from ..db import get_session
from math import radians, sin, cos, sqrt, atan2
import json

router = APIRouter(prefix="/geolocation")

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in meters
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    r = 6371000  # Radius of earth in meters
    return c * r

@router.post("/search-nearby")
async def search_nearby(
    request: GeoSearchRequest,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Search for parking slots within a radius of a given point
    This is a simplified version - in production, use PostGIS for better performance
    """
    center_lat = request.center.lat
    center_lng = request.center.lng
    radius_meters = request.radius_meters
    limit = min(request.limit, 100)  # Cap the limit for performance
    
    # Get all slots with location data
    query = text("""
        SELECT s.slot_id, s.zone_id, s.polygon, s.vehicle_type_hint, s.created_at,
               ss.occupied, ss.confidence, ss.vehicle_type, ss.last_seen, ss.reserved_until,
               ss.predicted_free_minutes, ss.prediction_confidence
        FROM slots s
        LEFT JOIN slot_status ss ON s.slot_id = ss.slot_id
        WHERE s.polygon IS NOT NULL
    """)
    
    result = await session.execute(query)
    slots = result.fetchall()
    
    # Filter slots by distance using Haversine formula
    nearby_slots = []
    for slot in slots:
        try:
            # Extract coordinates from polygon (assuming it's a GeoJSON Point or Polygon)
            polygon_data = slot.polygon
            if polygon_data and polygon_data.get('type') == 'Point':
                lng, lat = polygon_data.get('coordinates', [None, None])
                if lat is not None and lng is not None:
                    distance = haversine_distance(center_lat, center_lng, lat, lng)
                    if distance <= radius_meters:
                        slot_dict = {
                            "slot_id": slot.slot_id,
                            "zone_id": slot.zone_id,
                            "polygon": slot.polygon,
                            "vehicle_type_hint": slot.vehicle_type_hint,
                            "occupied": slot.occupied,
                            "confidence": slot.confidence,
                            "vehicle_type": slot.vehicle_type,
                            "distance_meters": round(distance, 2),
                            "last_seen": slot.last_seen,
                            "reserved_until": slot.reserved_until,
                            "predicted_free_minutes": slot.predicted_free_minutes,
                            "prediction_confidence": slot.prediction_confidence
                        }
                        nearby_slots.append(slot_dict)
        except Exception:
            # Skip slots with invalid location data
            continue
    
    # Sort by distance
    nearby_slots.sort(key=lambda x: x.get('distance_meters', float('inf')))
    
    # Limit results
    return nearby_slots[:limit]

@router.get("/zones")
async def get_zones(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all parking zones with their boundaries
    """
    query = text("""
        SELECT DISTINCT zone_id, polygon
        FROM slots
        WHERE zone_id IS NOT NULL AND polygon IS NOT NULL
    """)
    
    result = await session.execute(query)
    zones = result.fetchall()
    
    return [
        {
            "zone_id": zone.zone_id,
            "polygon": zone.polygon
        }
        for zone in zones
        if zone.polygon  # Only return zones with polygon data
    ]

@router.post("/update-location")
async def update_slot_location(
    location_update: GeoUpdate,
    current_user = Depends(get_current_admin_user),  # Only admins can update locations
    session: AsyncSession = Depends(get_session)
):
    """
    Update the location (coordinates/polygon) of a parking slot
    """
    # First check if the slot exists
    result = await session.execute(
        select(models.slots).where(models.slots.c.slot_id == location_update.slot_id)
    )
    slot = result.fetchone()
    
    if not slot:
        raise HTTPException(
            status_code=404,
            detail=f"Slot {location_update.slot_id} not found"
        )
    
    # Update the slot with new location data
    update_query = text("""
        UPDATE slots 
        SET polygon = :polygon
        WHERE slot_id = :slot_id
    """)
    
    polygon_data = location_update.polygon
    if not polygon_data and location_update.coordinates:
        # If no polygon provided but coordinates are, create a point
        polygon_data = {
            "type": "Point",
            "coordinates": [location_update.coordinates.lng, location_update.coordinates.lat]
        }
    
    await session.execute(update_query, {
        "polygon": json.dumps(polygon_data) if polygon_data else None,
        "slot_id": location_update.slot_id
    })
    await session.commit()
    
    return {
        "message": f"Location updated for slot {location_update.slot_id}",
        "slot_id": location_update.slot_id,
        "polygon": polygon_data
    }

@router.get("/slot/{slot_id}/location")
async def get_slot_location(
    slot_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get the location of a specific slot
    """
    query = text("""
        SELECT slot_id, zone_id, polygon, vehicle_type_hint
        FROM slots
        WHERE slot_id = :slot_id
    """)
    
    result = await session.execute(query, {"slot_id": slot_id})
    slot = result.fetchone()
    
    if not slot:
        raise HTTPException(
            status_code=404,
            detail=f"Slot {slot_id} not found"
        )
    
    return {
        "slot_id": slot.slot_id,
        "zone_id": slot.zone_id,
        "polygon": slot.polygon,
        "vehicle_type_hint": slot.vehicle_type_hint
    }