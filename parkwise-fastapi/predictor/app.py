from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import joblib, os, random
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI(title="Predictor")
MODEL_PATH = os.environ.get("MODEL_PATH", "/models/xgb_model.joblib")

class PredictReq(BaseModel):
    slot_id: str

@app.on_event("startup")
def load_model():
    global model, yolo_model
    try:
        model = joblib.load(MODEL_PATH)
    except Exception:
        model = None
    
    # Load YOLO model for computer vision
    try:
        yolo_model = YOLO("yolov8n.pt")  # You can also load a custom model
    except Exception:
        yolo_model = None

@app.post("/predict")
def predict(req: PredictReq):
    # If model missing, return a mock predictable result
    if model is None:
        return {"predicted_free_minutes": random.randint(1, 30), "confidence": round(random.uniform(0.6, 0.95), 2)}
    # For illustration: build a dummy feature vector — replace with real
    features = [1, 0, 12]  # replace with real engineered features
    pred = int(model.predict([features])[0])
    return {"predicted_free_minutes": pred, "confidence": 0.8}

@app.post("/detect-vehicles")
async def detect_vehicles(file: UploadFile = File(...)):
    """
    Detect vehicles in an uploaded image using YOLO
    """
    if yolo_model is None:
        return {"error": "YOLO model not loaded"}
    
    # Read image file
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"error": "Could not decode image"}
    
    # Perform YOLO detection
    results = yolo_model(img)
    
    detections = []
    for r in results:
        boxes = r.boxes
        if boxes is not None:
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # Only return vehicle detections (car, motorcycle, bus, truck)
                if cls in [2, 3, 5, 7] and conf > 0.5:  # car, motorcycle, bus, truck
                    detections.append({
                        "class_id": cls,
                        "confidence": conf,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)]
                    })
    
    return {"detections": detections, "count": len(detections)}

@app.get("/health")
def health():
    return {"status": "healthy", "yolo_loaded": yolo_model is not None, "xgb_loaded": model is not None}