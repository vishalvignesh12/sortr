import cv2
import numpy as np
import easyocr
from PIL import Image
from typing import Optional, Tuple, Dict
import logging
import re
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Global EasyOCR reader instance (initialized once at startup)
_anpr_reader = None
_anpr_enabled = False


def initialize_anpr_reader(gpu: bool = True) -> bool:
    """
    Initialize EasyOCR Reader with English language support

    Args:
        gpu: Use GPU if available (cuda), fallback to CPU

    Returns:
        True if initialization successful, False otherwise
    """
    global _anpr_reader, _anpr_enabled

    try:
        logger.info("Initializing EasyOCR reader for ANPR...")
        _anpr_reader = easyocr.Reader(['en'], gpu=gpu)
        _anpr_enabled = True
        logger.info("ANPR initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ANPR: {str(e)}")
        _anpr_enabled = False
        return False


def is_anpr_enabled() -> bool:
    """Check if ANPR is initialized and enabled"""
    return _anpr_enabled and _anpr_reader is not None


def detect_license_plate_region(vehicle_crop: np.ndarray) -> Optional[np.ndarray]:
    """
    Detect license plate region within a cropped vehicle image using OpenCV

    Args:
        vehicle_crop: Cropped image of detected vehicle from YOLO

    Returns:
        Cropped license plate image region or None if not found
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2GRAY)

        # Apply bilateral filter to reduce noise while preserving edges
        blur = cv2.bilateralFilter(gray, 11, 17, 17)

        # Apply edge detection
        edges = cv2.Canny(blur, 30, 200)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Sort contours by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        plate_contour = None

        # Look for rectangular contours with plate-like aspect ratio
        for contour in contours:
            # Approximate the contour
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

            # License plates typically have 4 corners
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / float(h)

                # Typical license plate aspect ratio is between 2:1 and 5:1
                if 2.0 <= aspect_ratio <= 5.0:
                    # Check if area is reasonable (not too small)
                    area = cv2.contourArea(contour)
                    image_area = vehicle_crop.shape[0] * vehicle_crop.shape[1]

                    if area > (image_area * 0.01):  # At least 1% of vehicle image
                        plate_contour = approx
                        break

        if plate_contour is not None:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(plate_contour)

            # Add small padding
            padding = 5
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(vehicle_crop.shape[1] - x, w + 2 * padding)
            h = min(vehicle_crop.shape[0] - y, h + 2 * padding)

            # Crop the plate region
            plate_img = vehicle_crop[y:y+h, x:x+w]
            return plate_img

        return None

    except Exception as e:
        logger.error(f"Error detecting license plate region: {str(e)}")
        return None


def preprocess_plate_image(plate_img: np.ndarray) -> np.ndarray:
    """
    Preprocess license plate image for better OCR results

    Args:
        plate_img: Cropped license plate image

    Returns:
        Preprocessed image
    """
    try:
        # Convert to grayscale if not already
        if len(plate_img.shape) == 3:
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_img

        # Apply contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Apply bilateral filter for noise reduction
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        return thresh

    except Exception as e:
        logger.error(f"Error preprocessing plate image: {str(e)}")
        return plate_img


def extract_plate_text(plate_img: np.ndarray) -> Tuple[Optional[str], float]:
    """
    Extract text from license plate image using EasyOCR

    Args:
        plate_img: Cropped license plate image

    Returns:
        Tuple of (plate_text, confidence) or (None, 0.0) if no text found
    """
    global _anpr_reader

    if not is_anpr_enabled():
        logger.warning("ANPR not enabled, skipping plate text extraction")
        return None, 0.0

    try:
        # Preprocess the image
        preprocessed = preprocess_plate_image(plate_img)

        # Run EasyOCR on the plate image
        results = _anpr_reader.readtext(preprocessed, detail=1)

        if not results:
            return None, 0.0

        # Filter results by confidence threshold (>0.5)
        high_conf_results = [r for r in results if r[2] > 0.5]

        if not high_conf_results:
            return None, 0.0

        # Take the result with highest confidence
        best_result = max(high_conf_results, key=lambda x: x[2])
        text = best_result[1]
        confidence = best_result[2]

        # Post-process text: remove spaces, special chars, uppercase
        plate_text = text.upper()
        plate_text = re.sub(r'[^A-Z0-9]', '', plate_text)

        if len(plate_text) < 4:
            # Too short to be valid plate
            return None, 0.0

        return plate_text, confidence

    except Exception as e:
        logger.error(f"Error extracting plate text: {str(e)}")
        return None, 0.0


def validate_plate_format(plate_text: str) -> bool:
    """
    Validate license plate format

    Args:
        plate_text: Raw plate text from OCR

    Returns:
        True if valid format, False otherwise
    """
    if not plate_text:
        return False

    # Check length (4-10 characters typical for most plates)
    if len(plate_text) < 4 or len(plate_text) > 10:
        return False

    # Must be alphanumeric
    if not plate_text.isalnum():
        return False

    # Reject purely numeric (likely false positive)
    if plate_text.isdigit():
        return False

    # Reject single character
    if len(plate_text) == 1:
        return False

    return True


def process_vehicle_for_plate(
    vehicle_bbox: list,
    full_image: np.ndarray,
    vehicle_type: str,
    slot_id: str
) -> Optional[Dict]:
    """
    Process a detected vehicle to extract license plate information

    Args:
        vehicle_bbox: Vehicle bounding box from YOLO [x1, y1, x2, y2]
        full_image: Full camera frame
        vehicle_type: Detected vehicle type (car, motorcycle, bus, truck)
        slot_id: Parking slot ID

    Returns:
        Dict with keys {license_plate, confidence, plate_image_crop} or None if no plate detected
    """
    if not is_anpr_enabled():
        return None

    try:
        # Extract vehicle crop from full image
        x1, y1, x2, y2 = vehicle_bbox
        vehicle_crop = full_image[y1:y2, x1:x2]

        if vehicle_crop.size == 0:
            return None

        # Detect license plate region within vehicle crop
        plate_region = detect_license_plate_region(vehicle_crop)

        if plate_region is None:
            logger.debug(f"No license plate region detected for vehicle in slot {slot_id}")
            return None

        # Extract text from plate
        plate_text, confidence = extract_plate_text(plate_region)

        if plate_text is None:
            return None

        # Validate plate format
        if not validate_plate_format(plate_text):
            logger.debug(f"Invalid plate format: {plate_text}")
            # Apply confidence penalty for invalid format but still store
            confidence *= 0.7

        logger.info(f"Detected plate: {plate_text} (confidence: {confidence:.2f}) in slot {slot_id}")

        return {
            'license_plate': plate_text,
            'confidence': confidence,
            'plate_image_crop': plate_region,
            'vehicle_type': vehicle_type,
            'slot_id': slot_id
        }

    except Exception as e:
        logger.error(f"Error processing vehicle for plate: {str(e)}")
        return None


def save_plate_image(plate_image: np.ndarray, license_plate: str, upload_dir: str = "uploads/plates") -> Optional[str]:
    """
    Save cropped license plate image to disk

    Args:
        plate_image: Cropped plate image
        license_plate: License plate text
        upload_dir: Directory to save images

    Returns:
        Relative path to saved image or None if failed
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{license_plate}_{timestamp}.jpg"
        filepath = os.path.join(upload_dir, filename)

        # Save image
        cv2.imwrite(filepath, plate_image)

        return filepath

    except Exception as e:
        logger.error(f"Error saving plate image: {str(e)}")
        return None
