from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.security import HTTPBearer
from ..security import get_current_admin_user
from .. import cv_processor
from datetime import datetime
import asyncio

router = APIRouter(prefix="/cv")

security = HTTPBearer()

@router.get("/calibrated-slots")
async def get_calibrated_slots(
    current_user = Depends(get_current_admin_user)
):
    """
    Get all calibrated parking slots with their positions
    Used for UI calibration interface
    """
    from sqlalchemy import select
    from ..db import get_session
    from .. import models
    
    try:
        calibrated_slots = []
        async for session in get_session():
            result = await session.execute(
                select(models.slots).where(models.slots.c.polygon.isnot(None))
            )
            slots = result.fetchall()
            
            for slot in slots:
                calibrated_slots.append({
                    'slot_id': slot.slot_id,
                    'polygon': slot.polygon,
                    'zone_id': slot.zone_id,
                    'vehicle_type_hint': slot.vehicle_type_hint
                })
            
            break  # Exit session loop
        
        return calibrated_slots
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving calibrated slots: {str(e)}")


@router.get("/slots-with-status")
async def get_slots_with_status_and_calibration(
    current_user = Depends(get_current_admin_user)
):
    """
    Get all parking slots with their status and calibration data
    """
    from sqlalchemy import text
    from ..db import get_session
    
    try:
        async for session in get_session():
            # Query to get slots with their calibration and status
            query = text("""
                SELECT 
                    s.slot_id,
                    s.zone_id,
                    s.polygon,
                    s.vehicle_type_hint,
                    ss.occupied,
                    ss.confidence,
                    ss.vehicle_type,
                    ss.last_seen,
                    ss.reserved_until,
                    ss.predicted_free_minutes,
                    ss.prediction_confidence
                FROM slots s
                LEFT JOIN slot_status ss ON s.slot_id = ss.slot_id
                ORDER BY s.slot_id
            """)
            
            result = await session.execute(query)
            rows = result.fetchall()
            
            slots = []
            for row in rows:
                slots.append(dict(row._mapping))
            
            break  # Exit session loop
        
        return slots
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving slots with status: {str(e)}")


@router.delete("/calibrate-slot/{slot_id}")
async def remove_slot_calibration(
    slot_id: str,
    current_user = Depends(get_current_admin_user)
):
    """
    Remove calibration for a parking slot (set polygon to null)
    """
    from sqlalchemy import update
    from ..db import get_session
    from .. import models
    
    try:
        async for session in get_session():
            # Update the slot to remove the polygon (calibration)
            result = await session.execute(
                update(models.slots)
                .where(models.slots.c.slot_id == slot_id)
                .values(polygon=None)
            )
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"Slot {slot_id} not found")
            
            await session.commit()
            break  # Exit session loop
        
        return {"message": f"Calibration removed for slot {slot_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing slot calibration: {str(e)}")


@router.post("/process-image")
async def process_parking_image(
    file: UploadFile = File(...),
    spot_id: str = Form(...),
    current_user = Depends(get_current_admin_user)  # Only admin can process images manually
):
    """
    Process a parking lot image to detect vehicle occupancy
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image data
        contents = await file.read()
        
        # Initialize detector (in production, this would be a singleton)
        detector = cv_processor.ParkingSpotDetector()
        
        # Process the image using database configuration
        result = await detector.process_parking_image_with_db(contents, spot_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@router.post("/detect-occupancy")
async def detect_occupancy_webcam(
    spot_id: str,
    camera_url: str = None,  # Optional camera URL for remote cameras
    current_user = Depends(get_current_admin_user)
):
    """
    Detect parking spot occupancy using webcam or remote camera
    """
    try:
        # In a real implementation, this would connect to a webcam or IP camera
        # For now, we'll simulate the detection process
        
        # This would typically:
        # 1. Connect to camera at camera_url
        # 2. Capture frame
        # 3. Process with CV module
        # 4. Return detection results
        
        # For simulation, return a sample result
        return {
            "slot_id": spot_id,
            "occupied": False,
            "confidence": 0.95,
            "vehicle_type": "car",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Camera connection and detection would happen here"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to camera: {str(e)}")


@router.post("/update-slot-from-camera")
async def update_slot_from_camera(
    file: UploadFile = File(...),
    spot_id: str = Form(...),
    current_user = Depends(get_current_admin_user)
):
    """
    Process image from camera and update parking slot status directly
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image data
        contents = await file.read()
        
        # Initialize detector
        detector = cv_processor.ParkingSpotDetector()
        
        # Process the image using database configuration
        result = await detector.process_parking_image_with_db(contents, spot_id)
        
        # Import necessary modules to update the database
        from sqlalchemy import select, text
        from ..db import get_session
        from .. import models
        import redis.asyncio as aioredis
        from ..core import settings
        from ..cache import set_slot_status, invalidate_slot_list
        from ..websocket import notify_slot_update
        from ..audit import log_slot_update
        from ..exceptions import SlotNotFoundException
        
        # Update the database with the new status
        async for session in get_session():
            # Check if the slot exists
            slot_result = await session.execute(
                select(models.slots).where(models.slots.c.slot_id == result['slot_id'])
            )
            slot = slot_result.fetchone()
            
            if not slot:
                raise SlotNotFoundException(f"Slot {result['slot_id']} not found")
            
            # Insert slot event
            from sqlalchemy import text as sql_text
            await session.execute(
                sql_text("""
                INSERT INTO slot_events (slot_id, event_type, meta, source)
                VALUES (:slot_id, :event_type, :meta, :source)
                """), {
                    'slot_id': result['slot_id'],
                    'event_type': 'entry' if result['occupied'] else 'exit',
                    'meta': {'confidence': result['confidence'], 'vehicle_type': result['vehicle_type']},
                    'source': 'camera'
                }
            )
            
            # Update slot status
            await session.execute(sql_text("""
            INSERT INTO slot_status (slot_id, occupied, confidence, vehicle_type, last_seen, updated_at)
            VALUES (:slot_id, :occupied, :confidence, :vehicle_type, now(), now())
            ON CONFLICT (slot_id) DO UPDATE
              SET occupied = EXCLUDED.occupied,
                  confidence = EXCLUDED.confidence,
                  vehicle_type = EXCLUDED.vehicle_type,
                  last_seen = EXCLUDED.last_seen,
                  updated_at = now()
            """), {
                'slot_id': result['slot_id'],
                'occupied': result['occupied'],
                'confidence': result['confidence'],
                'vehicle_type': result['vehicle_type']
            })
            await session.commit()
            
            # Update cache with new status
            slot_status = {
                'slot_id': result['slot_id'],
                'occupied': result['occupied'],
                'confidence': result['confidence'],
                'vehicle_type': result['vehicle_type'],
                'last_seen': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            await set_slot_status(result['slot_id'], slot_status)
            
            # Invalidate the slot list cache since we changed a slot status
            await invalidate_slot_list()

            # Send WebSocket notification about the slot update
            await notify_slot_update(result['slot_id'], slot_status)
            
            # Log the slot update in audit logs
            await log_slot_update(session, current_user.id if current_user else None, result['slot_id'], None)

            # Push to redis prediction queue
            r = aioredis.from_url(settings.REDIS_URL)
            await r.lpush('predict_queue', result['slot_id'])
            
            break  # Exit the session loop
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing camera image update: {str(e)}")


@router.post("/calibrate-slot")
async def calibrate_slot(
    file: UploadFile = File(...),
    slot_id: str = Form(...),
    x: int = Form(...),
    y: int = Form(...),
    width: int = Form(...),
    height: int = Form(...),
    current_user = Depends(get_current_admin_user)
):
    """
    Calibrate a parking slot by defining its position in an image
    This allows administrators to map parking spots in camera images
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read and validate image
        contents = await file.read()
        import cv2
        import numpy as np
        
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Store slot configuration in the database
        from sqlalchemy import select, update, insert
        from ..db import get_session
        from .. import models
        
        async for session in get_session():
            # Check if slot exists, if not create it
            slot_result = await session.execute(
                select(models.slots).where(models.slots.c.slot_id == slot_id)
            )
            existing_slot = slot_result.fetchone()
            
            # Define the slot area as a polygon (rectangle in this case)
            # Format: [top-left, top-right, bottom-right, bottom-left]
            polygon = [
                [x, y],                    # Top-left
                [x + width, y],            # Top-right
                [x + width, y + height],   # Bottom-right
                [x, y + height]            # Bottom-left
            ]
            
            if existing_slot:
                # Update existing slot
                await session.execute(
                    update(models.slots)
                    .where(models.slots.c.slot_id == slot_id)
                    .values(polygon=polygon)
                )
            else:
                # Create new slot
                await session.execute(
                    insert(models.slots)
                    .values(
                        slot_id=slot_id,
                        polygon=polygon,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )
            
            await session.commit()
            break  # Exit session loop
        
        return {
            "slot_id": slot_id,
            "polygon": polygon,
            "message": f"Slot {slot_id} calibrated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calibrating slot: {str(e)}")


@router.post("/process-live-camera-feed")
async def process_live_camera_feed(
    camera_url: str = Form(...),
    spot_id: str = Form(...),
    current_user = Depends(get_current_admin_user)
):
    """
    Process live camera feed to detect parking spot occupancy
    This would connect to a live camera feed, capture a frame, and process it
    """
    import cv2
    import numpy as np
    from io import BytesIO
    
    try:
        # Connect to camera feed
        cap = cv2.VideoCapture(camera_url)
        
        if not cap.isOpened():
            raise HTTPException(status_code=500, detail="Could not open camera feed")
        
        # Capture a single frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise HTTPException(status_code=500, detail="Could not capture frame from camera")
        
        # Encode frame as bytes
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        # Initialize detector
        detector = cv_processor.ParkingSpotDetector()
        
        # Process the image using the calibrated slot from the database
        result = detector.process_parking_image(frame_bytes, spot_id)
        
        # Update the database with the new status (reuse the same logic as the file upload endpoint)
        from sqlalchemy import select, text
        from ..db import get_session
        from .. import models
        import redis.asyncio as aioredis
        from ..core import settings
        from ..cache import set_slot_status, invalidate_slot_list
        from ..websocket import notify_slot_update
        from ..audit import log_slot_update
        from ..exceptions import SlotNotFoundException
        
        # Update the database with the new status
        async for session in get_session():
            # Check if the slot exists
            slot_result = await session.execute(
                select(models.slots).where(models.slots.c.slot_id == result['slot_id'])
            )
            slot = slot_result.fetchone()
            
            if not slot:
                raise SlotNotFoundException(f"Slot {result['slot_id']} not found")
            
            # Insert slot event
            from sqlalchemy import text as sql_text
            await session.execute(
                sql_text("""
                INSERT INTO slot_events (slot_id, event_type, meta, source)
                VALUES (:slot_id, :event_type, :meta, :source)
                """), {
                    'slot_id': result['slot_id'],
                    'event_type': 'entry' if result['occupied'] else 'exit',
                    'meta': {'confidence': result['confidence'], 'vehicle_type': result['vehicle_type']},
                    'source': 'camera_feed'
                }
            )
            
            # Update slot status
            await session.execute(sql_text("""
            INSERT INTO slot_status (slot_id, occupied, confidence, vehicle_type, last_seen, updated_at)
            VALUES (:slot_id, :occupied, :confidence, :vehicle_type, now(), now())
            ON CONFLICT (slot_id) DO UPDATE
              SET occupied = EXCLUDED.occupied,
                  confidence = EXCLUDED.confidence,
                  vehicle_type = EXCLUDED.vehicle_type,
                  last_seen = EXCLUDED.last_seen,
                  updated_at = now()
            """), {
                'slot_id': result['slot_id'],
                'occupied': result['occupied'],
                'confidence': result['confidence'],
                'vehicle_type': result['vehicle_type']
            })
            await session.commit()
            
            # Update cache with new status
            slot_status = {
                'slot_id': result['slot_id'],
                'occupied': result['occupied'],
                'confidence': result['confidence'],
                'vehicle_type': result['vehicle_type'],
                'last_seen': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            await set_slot_status(result['slot_id'], slot_status)
            
            # Invalidate the slot list cache since we changed a slot status
            await invalidate_slot_list()

            # Send WebSocket notification about the slot update
            await notify_slot_update(result['slot_id'], slot_status)
            
            # Log the slot update in audit logs
            await log_slot_update(session, current_user.id if current_user else None, result['slot_id'], None)

            # Push to redis prediction queue
            r = aioredis.from_url(settings.REDIS_URL)
            await r.lpush('predict_queue', result['slot_id'])
            
            break  # Exit the session loop
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing live camera feed: {str(e)}")

