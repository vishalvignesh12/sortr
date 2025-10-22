from pydantic import BaseModel, EmailStr, validator, field_validator
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
import re

# Authentication schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class User(BaseModel):
    id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# API Key Management schemas
class ApiKeyCreate(BaseModel):
    description: str
    expires_at: Optional[datetime] = None

class ApiKeyResponse(BaseModel):
    id: str
    api_key: str  # In real implementation, this would be masked
    description: str
    created_by: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    last_used: Optional[datetime]

class ApiKeyListResponse(BaseModel):
    id: str
    description: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    last_used: Optional[datetime]

# Geolocation schemas
class GeoPoint(BaseModel):
    lat: float
    lng: float

class GeoBounds(BaseModel):
    north_east: GeoPoint
    south_west: GeoPoint

class GeoSearchRequest(BaseModel):
    center: GeoPoint
    radius_meters: float = 1000  # Default to 1km radius
    limit: int = 50

class GeoUpdate(BaseModel):
    slot_id: str
    coordinates: GeoPoint
    polygon: Optional[dict] = None  # GeoJSON polygon

class SlotCalibration(BaseModel):
    slot_id: str
    x: int
    y: int
    width: int
    height: int

class SlotStatus(BaseModel):
    slot_id: str
    occupied: bool
    confidence: float
    vehicle_type: Optional[str] = None
    last_seen: Optional[datetime]
    reserved_until: Optional[datetime]
    predicted_free_minutes: Optional[int]
    prediction_confidence: Optional[float]

class HoldRequest(BaseModel):
    slot_id: str
    hold_minutes: int = 2
    user_id: Optional[str] = None
    
    @validator('hold_minutes')
    def validate_hold_minutes(cls, v):
        if v < 1 or v > 60:  # Max 1 hour hold
            raise ValueError('Hold minutes must be between 1 and 60')
        return v

class HoldResponse(BaseModel):
    booking_id: str
    hold_until: datetime

# Payment schemas
class PaymentCreate(BaseModel):
    booking_id: str
    amount: float
    
    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class PaymentResponse(BaseModel):
    id: str
    booking_id: str
    amount: float
    status: str
    transaction_id: Optional[str]

# Notification schemas
class NotificationCreate(BaseModel):
    user_id: Optional[str] = None
    type: str
    message: str
    
    @field_validator('type')
    def validate_notification_type(cls, v):
        valid_types = ['booking_confirmation', 'slot_available', 'reservation_expired', 'system_alert']
        if v not in valid_types:
            raise ValueError(f'Notification type must be one of: {", ".join(valid_types)}')
        return v
    
    @field_validator('message')
    def validate_message(cls, v):
        if not v or len(v) > 500:
            raise ValueError('Message must be between 1 and 500 characters')
        return v

class Notification(BaseModel):
    id: str
    type: str
    message: str
    is_read: bool
    sent_at: datetime

# Admin schemas
class AdminStats(BaseModel):
    total_users: int
    active_bookings: int
    available_slots: int
    occupied_slots: int

# Audit log schemas
class AuditLogCreate(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[dict] = None

# Slot with geolocation schemas
class SlotCreate(BaseModel):
    slot_id: str
    zone_id: Optional[str] = None
    coordinates: Optional[GeoPoint] = None
    polygon: Optional[dict] = None  # GeoJSON polygon
    vehicle_type_hint: Optional[str] = None

# Export schemas
class DataExportRequest(BaseModel):
    resource_type: str  # 'users', 'bookings', 'payments', 'slots'
    format: str = 'csv'  # 'csv', 'json', 'pdf'
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filters: Optional[dict] = None