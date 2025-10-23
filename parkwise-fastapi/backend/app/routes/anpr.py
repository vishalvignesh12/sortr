from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional, List
from datetime import datetime
from .. import models
from ..db import get_session
from ..security import get_current_user, get_current_admin_user
from .. import anpr_processor
from ..cv_processor import ParkingSpotDetector
import logging

router = APIRouter(prefix="/v1/anpr", tags=["anpr"])
logger = logging.getLogger(__name__)


@router.get("/plates")
async def list_plates(
    status_filter: Optional[str] = 'active',
    zone_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    List all detected license plates with filtering

    Query parameters:
    - status: 'active' or 'exited', defaults to 'active'
    - zone_id: Filter by parking zone/level
    - limit: Max results, default 100
    - offset: Pagination offset, default 0
    """
    try:
        # Build query
        query = select(models.vehicle_plates).offset(offset).limit(limit)

        # Apply status filter
        if status_filter:
            query = query.where(models.vehicle_plates.c.status == status_filter)

        # Apply zone filter
        if zone_id:
            query = query.where(models.vehicle_plates.c.zone_id == zone_id)

        # Order by most recent first
        query = query.order_by(models.vehicle_plates.c.last_seen.desc())

        result = await session.execute(query)
        plates = result.fetchall()

        # Convert to dict
        plates_list = []
        for plate in plates:
            plates_list.append({
                'id': str(plate.id),
                'license_plate': plate.license_plate,
                'slot_id': plate.slot_id,
                'zone_id': plate.zone_id,
                'vehicle_type': plate.vehicle_type,
                'confidence': plate.confidence,
                'first_seen': plate.first_seen.isoformat() if plate.first_seen else None,
                'last_seen': plate.last_seen.isoformat() if plate.last_seen else None,
                'status': plate.status,
                'image_path': plate.image_path
            })

        return {
            'total': len(plates_list),
            'offset': offset,
            'limit': limit,
            'plates': plates_list
        }

    except Exception as e:
        logger.error(f"Error listing plates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list plates: {str(e)}"
        )


@router.get("/plates/{license_plate}")
async def get_plate_details(
    license_plate: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get details for specific license plate (normalized to uppercase)
    """
    try:
        # Normalize plate to uppercase
        normalized_plate = license_plate.upper()

        # Query for most recent active entry
        result = await session.execute(
            select(models.vehicle_plates)
            .where(models.vehicle_plates.c.license_plate == normalized_plate)
            .order_by(models.vehicle_plates.c.last_seen.desc())
            .limit(1)
        )
        plate = result.fetchone()

        if not plate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"License plate {normalized_plate} not found"
            )

        # Get slot details
        slot_result = await session.execute(
            select(models.slots).where(models.slots.c.slot_id == plate.slot_id)
        )
        slot = slot_result.fetchone()

        return {
            'id': str(plate.id),
            'license_plate': plate.license_plate,
            'slot_id': plate.slot_id,
            'zone_id': plate.zone_id,
            'vehicle_type': plate.vehicle_type,
            'confidence': plate.confidence,
            'first_seen': plate.first_seen.isoformat() if plate.first_seen else None,
            'last_seen': plate.last_seen.isoformat() if plate.last_seen else None,
            'status': plate.status,
            'image_path': plate.image_path,
            'slot_info': {
                'slot_id': slot.slot_id if slot else None,
                'zone_id': slot.zone_id if slot else None,
                'vehicle_type_hint': slot.vehicle_type_hint if slot else None
            } if slot else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plate details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plate details: {str(e)}"
        )


@router.get("/plates/{license_plate}/history")
async def get_plate_history(
    license_plate: str,
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get historical parking records for a license plate

    Query parameters:
    - limit: Max results, default 50
    - start_date: ISO timestamp, filter from date
    - end_date: ISO timestamp, filter to date
    """
    try:
        # Normalize plate to uppercase
        normalized_plate = license_plate.upper()

        # Build query
        query = select(models.vehicle_plates).where(
            models.vehicle_plates.c.license_plate == normalized_plate
        )

        # Apply date filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(models.vehicle_plates.c.first_seen >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(models.vehicle_plates.c.first_seen <= end_dt)

        # Order by most recent first
        query = query.order_by(models.vehicle_plates.c.first_seen.desc()).limit(limit)

        result = await session.execute(query)
        history = result.fetchall()

        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No history found for license plate {normalized_plate}"
            )

        # Convert to list of dicts
        history_list = []
        for record in history:
            history_list.append({
                'id': str(record.id),
                'license_plate': record.license_plate,
                'slot_id': record.slot_id,
                'zone_id': record.zone_id,
                'vehicle_type': record.vehicle_type,
                'confidence': record.confidence,
                'first_seen': record.first_seen.isoformat() if record.first_seen else None,
                'last_seen': record.last_seen.isoformat() if record.last_seen else None,
                'status': record.status
            })

        return {
            'license_plate': normalized_plate,
            'total_records': len(history_list),
            'history': history_list
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plate history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plate history: {str(e)}"
        )


@router.post("/process-image-with-plate")
async def process_image_with_plate(
    image: UploadFile = File(...),
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin/testing endpoint to manually process image with ANPR

    Requires admin privileges
    """
    try:
        # Check if ANPR is enabled
        if not anpr_processor.is_anpr_enabled():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ANPR service is currently disabled"
            )

        # Read image data
        image_data = await image.read()

        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image data provided"
            )

        # Validate image format
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )

        # Initialize detector and process
        detector = ParkingSpotDetector()

        import cv2
        import numpy as np

        # Convert to image frame
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image data"
            )

        # Detect vehicles
        detections = detector.detect_vehicles_in_frame(frame)

        # Process each detection for plates
        plate_results = []
        for detection in detections:
            plate_data = anpr_processor.process_vehicle_for_plate(
                vehicle_bbox=detection['bbox'],
                full_image=frame,
                vehicle_type=detection['vehicle_type'],
                slot_id='test_slot'
            )

            if plate_data:
                plate_results.append({
                    'license_plate': plate_data['license_plate'],
                    'confidence': plate_data['confidence'],
                    'vehicle_type': plate_data['vehicle_type'],
                    'vehicle_bbox': detection['bbox']
                })

        return {
            'total_vehicles_detected': len(detections),
            'total_plates_detected': len(plate_results),
            'detections': detections,
            'plates': plate_results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image with ANPR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )


@router.delete("/plates/{license_plate}")
async def delete_plate(
    license_plate: str,
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin endpoint to remove incorrect plate detection

    Requires admin privileges
    """
    try:
        # Normalize plate to uppercase
        normalized_plate = license_plate.upper()

        # Check if plate exists
        result = await session.execute(
            select(models.vehicle_plates).where(
                models.vehicle_plates.c.license_plate == normalized_plate
            )
        )
        plate = result.fetchone()

        if not plate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"License plate {normalized_plate} not found"
            )

        # Delete the plate record
        await session.execute(
            delete(models.vehicle_plates).where(
                models.vehicle_plates.c.license_plate == normalized_plate
            )
        )

        # Log audit trail
        from sqlalchemy import insert
        await session.execute(
            insert(models.audit_logs).values(
                user_id=str(current_user.id),
                action='delete_plate',
                resource_type='vehicle_plate',
                resource_id=normalized_plate,
                details={'license_plate': normalized_plate, 'reason': 'admin_deletion'}
            )
        )

        await session.commit()

        logger.info(f"Admin {current_user.email} deleted plate: {normalized_plate}")

        return {
            'message': f'License plate {normalized_plate} successfully deleted',
            'deleted_plate': normalized_plate
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting plate: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete plate: {str(e)}"
        )
