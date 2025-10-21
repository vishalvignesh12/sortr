import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import io
import base64
from typing import List, Tuple, Dict, Optional
import asyncio
from datetime import datetime
import logging

class ParkingSpotDetector:
    """
    Computer Vision module for detecting parking spots and vehicles
    using YOLO object detection
    """
    
    def __init__(self, model_path: str = "yolov8n.pt", parking_spots: List[Dict] = None):
        """
        Initialize the parking spot detector
        
        Args:
            model_path: Path to YOLO model file
            parking_spots: List of parking spot coordinates in the image
        """
        self.model = YOLO(model_path)
        self.parking_spots = parking_spots or []
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck in COCO dataset
        self.logger = logging.getLogger(__name__)
        
    def set_parking_spots(self, spots: List[Dict]):
        """
        Set the parking spot configurations
        
        Args:
            spots: List of parking spot configurations
        """
        self.parking_spots = spots
    
    def add_parking_spot(self, spot_id: str, coordinates: List[int], angle: float = 0.0):
        """
        Add a new parking spot configuration
        
        Args:
            spot_id: Unique identifier for the parking spot
            coordinates: [x, y, width, height] or polygon coordinates
            angle: Angle of the parking spot (for angled parking)
        """
        spot_config = {
            'id': spot_id,
            'coordinates': coordinates,
            'angle': angle,
            'active': True
        }
        self.parking_spots.append(spot_config)
        
    def detect_vehicles_in_frame(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect vehicles in a single frame using YOLO
        
        Args:
            frame: Input image frame
            
        Returns:
            List of detected vehicles with bounding boxes and confidence
        """
        # Run YOLO detection
        results = self.model(frame, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    if cls in self.vehicle_classes and conf > 0.5:  # Only if confidence > 0.5
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        detections.append({
                            'class_id': cls,
                            'confidence': conf,
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'center': ((x1 + x2) / 2, (y1 + y2) / 2)
                        })
        
        return detections
    
    def is_parking_spot_occupied(self, spot_config: Dict, detections: List[Dict]) -> Tuple[bool, float, str]:
        """
        Determine if a parking spot is occupied based on vehicle detections
        
        Args:
            spot_config: Configuration for the parking spot (including coordinates)
            detections: List of detected vehicles from YOLO
            
        Returns:
            Tuple of (occupied, confidence, vehicle_type)
        """
        occupied = False
        highest_confidence = 0.0
        vehicle_type = "unknown"
        
        # Handle both rectangular (x, y, w, h) and polygon coordinates
        if 'polygon' in spot_config:
            # Use polygon coordinates
            spot_polygon = spot_config['polygon']
            for detection in detections:
                center_x, center_y = detection['center']
                if self._is_point_in_polygon(center_x, center_y, spot_polygon):
                    if detection['confidence'] > highest_confidence:
                        occupied = True
                        highest_confidence = detection['confidence']
                        
                        # Map class IDs to vehicle types
                        vehicle_types = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
                        vehicle_type = vehicle_types.get(detection['class_id'], "vehicle")
        else:
            # Use rectangular coordinates
            spot_coords = spot_config['coordinates']
            spot_x, spot_y, spot_w, spot_h = spot_coords
            spot_area = [(spot_x, spot_y), (spot_x + spot_w, spot_y + spot_h)]
            
            for detection in detections:
                # Check if detection center is within parking spot area
                center_x, center_y = detection['center']
                
                if (spot_area[0][0] <= center_x <= spot_area[1][0] and 
                    spot_area[0][1] <= center_y <= spot_area[1][1]):
                    
                    if detection['confidence'] > highest_confidence:
                        occupied = True
                        highest_confidence = detection['confidence']
                        
                        # Map class IDs to vehicle types
                        vehicle_types = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
                        vehicle_type = vehicle_types.get(detection['class_id'], "vehicle")
        
        return occupied, highest_confidence, vehicle_type
    
    def _is_point_in_polygon(self, x, y, polygon):
        """
        Check if a point is inside a polygon using ray casting algorithm
        
        Args:
            x, y: Point coordinates
            polygon: List of (x, y) coordinates defining the polygon
            
        Returns:
            True if point is inside the polygon, False otherwise
        """
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    async def process_parking_image_with_db(self, image_data: bytes, spot_id: str) -> Dict:
        """
        Process a parking lot image to detect occupancy status using database configuration
        
        Args:
            image_data: Raw image bytes
            spot_id: Unique identifier for the parking spot
            
        Returns:
            Dictionary with occupancy status and metadata
        """
        # Convert bytes to image
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise ValueError("Invalid image data")
        
        # Get detections
        detections = self.detect_vehicles_in_frame(frame)
        
        # Fetch spot configuration from database
        from sqlalchemy import select
        from ..db import get_session
        from .. import models
        
        spot_info = None
        async for session in get_session():
            slot_result = await session.execute(
                select(models.slots).where(models.slots.c.slot_id == spot_id)
            )
            slot = slot_result.fetchone()
            
            if slot:
                spot_info = {
                    'id': spot_id,
                    'polygon': slot.polygon,
                    'active': True
                }
            
            break  # Exit session loop
        
        if spot_info is None:
            raise ValueError(f"Parking spot {spot_id} not found in database")
        
        if spot_info['polygon'] is None:
            raise ValueError(f"Parking spot {spot_id} has not been calibrated")
        
        # Check if this spot is occupied using the polygon coordinates
        occupied, confidence, vehicle_type = self.is_parking_spot_occupied(
            spot_info, detections
        )
        
        # Additional processing for confidence calculation
        if not occupied:
            # If no vehicle detected in spot, confidence is based on absence
            confidence = max(0.8, 1.0 - (len(detections) * 0.05))  # Lower confidence if many vehicles nearby
        
        return {
            'slot_id': spot_id,
            'occupied': occupied,
            'confidence': round(float(confidence), 2),
            'vehicle_type': vehicle_type,
            'timestamp': datetime.utcnow().isoformat(),
            'detection_count': len(detections),
            'detection_details': detections
        }

    def process_parking_image(self, image_data: bytes, spot_id: str) -> Dict:
        """
        Process a parking lot image to detect occupancy status using internal configuration
        For backward compatibility and testing purposes
        
        Args:
            image_data: Raw image bytes
            spot_id: Unique identifier for the parking spot
            
        Returns:
            Dictionary with occupancy status and metadata
        """
        # Convert bytes to image
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise ValueError("Invalid image data")
        
        # Get detections
        detections = self.detect_vehicles_in_frame(frame)
        
        # Find the specific parking spot in internal configuration
        spot_info = None
        for spot in self.parking_spots:
            if spot['id'] == spot_id:
                spot_info = spot
                break
        
        if spot_info is None:
            raise ValueError(f"Parking spot {spot_id} not found in configuration")
        
        # Check if this spot is occupied
        occupied, confidence, vehicle_type = self.is_parking_spot_occupied(
            spot_info, detections
        )
        
        # Additional processing for confidence calculation
        if not occupied:
            # If no vehicle detected in spot, confidence is based on absence
            confidence = max(0.8, 1.0 - (len(detections) * 0.05))  # Lower confidence if many vehicles nearby
        
        return {
            'slot_id': spot_id,
            'occupied': occupied,
            'confidence': round(float(confidence), 2),
            'vehicle_type': vehicle_type,
            'timestamp': datetime.utcnow().isoformat(),
            'detection_count': len(detections),
            'detection_details': detections
        }
    
    def setup_parking_spots_from_image(self, image_path: str, spots_config: List[Dict]) -> None:
        """
        Set up parking spots based on a reference image with coordinates
        
        Args:
            image_path: Path to reference image
            spots_config: Configuration for parking spots
        """
        self.parking_spots = spots_config
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict], parking_spots: List[Dict] = None) -> np.ndarray:
        """
        Draw detections and parking spot boundaries on frame for visualization
        
        Args:
            frame: Input image frame
            detections: List of detections to draw
            parking_spots: Parking spot boundaries to draw
            
        Returns:
            Image frame with drawn annotations
        """
        output_frame = frame.copy()
        
        # Draw parking spots
        if parking_spots:
            for spot in parking_spots:
                x, y, w, h = spot['coordinates']
                cv2.rectangle(output_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(output_frame, spot['id'], (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Draw detections
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            conf = detection['confidence']
            
            cv2.rectangle(output_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(output_frame, f"Vehicle {conf:.2f}", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        return output_frame

class EdgeCVProcessor:
    """
    Edge processor that handles image processing and sends results to backend
    """
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.detector = ParkingSpotDetector()
        self.logger = logging.getLogger(__name__)
    
    async def process_and_send_update(self, image_data: bytes, spot_id: str):
        """
        Process an image and send the update to the backend API
        """
        try:
            # Process the image to get occupancy status
            result = self.detector.process_parking_image(image_data, spot_id)
            
            # In a real implementation, you would send this to the backend API
            # For now, we'll just return the processed result
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing image for spot {spot_id}: {str(e)}")
            raise e

# Example usage:
if __name__ == "__main__":
    # Initialize detector
    detector = ParkingSpotDetector()
    
    # Example parking spot configuration (in real usage, this would be loaded from DB/config)
    parking_spots = [
        {
            'id': 'spot_001',
            'coordinates': [100, 100, 80, 40],  # x, y, width, height
            'active': True
        },
        {
            'id': 'spot_002', 
            'coordinates': [200, 100, 80, 40],
            'active': True
        }
    ]
    
    detector.parking_spots = parking_spots
    
    print("Parking spot detector initialized")
    print("Ready to process parking lot images with YOLO detection")