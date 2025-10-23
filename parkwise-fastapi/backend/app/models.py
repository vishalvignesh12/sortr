from sqlalchemy import (
    Table, Column, String, Boolean, Integer, TIMESTAMP, JSON, text, MetaData, Index
)
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa

metadata = MetaData()

users = Table(
    'users', metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
    Column('email', String, unique=True, nullable=False),
    Column('hashed_password', String, nullable=False),
    Column('first_name', String, nullable=True),
    Column('last_name', String, nullable=True),
    Column('is_active', Boolean, default=True),
    Column('is_admin', Boolean, default=False),
    Column('created_at', TIMESTAMP, server_default=text('now()')),
    Column('updated_at', TIMESTAMP, server_default=text('now()')),
)

api_keys = Table(
    'api_keys', metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
    Column('api_key', String, unique=True, nullable=False),
    Column('description', String, nullable=True),
    Column('created_by', UUID(as_uuid=True), nullable=False),  # Admin who created it
    Column('created_at', TIMESTAMP, server_default=text('now()')),
    Column('expires_at', TIMESTAMP, nullable=True),  # Optional expiration
    Column('is_active', Boolean, default=True),
    Column('last_used', TIMESTAMP, nullable=True),
)



slots = Table(
    'slots', metadata,
    Column('slot_id', String, primary_key=True),
    Column('zone_id', String, nullable=True),
    Column('polygon', JSON, nullable=True),  # Store geolocation as polygon
    Column('vehicle_type_hint', String, nullable=True),
    Column('created_at', TIMESTAMP, server_default=text('now()')),
    Column('updated_at', TIMESTAMP, server_default=text('now()')),
)

slot_status = Table(
    'slot_status', metadata,
    Column('slot_id', String, sa.ForeignKey('slots.slot_id'), primary_key=True),
    Column('occupied', Boolean, default=False),
    Column('confidence', sa.Float, default=1.0),
    Column('vehicle_type', String, nullable=True),
    Column('last_seen', TIMESTAMP, server_default=text('now()')),
    Column('reserved_until', TIMESTAMP, nullable=True),
    Column('predicted_free_minutes', Integer, nullable=True),
    Column('prediction_confidence', sa.Float, nullable=True),
    Column('updated_at', TIMESTAMP, server_default=text('now()')),
)

slot_events = Table(
    'slot_events', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('slot_id', String, nullable=False),
    Column('event_type', String),
    Column('meta', JSON),
    Column('license_plate', String(20), nullable=True),  # Added for ANPR tracking
    Column('created_at', TIMESTAMP, server_default=text('now()')),
    Column('source', String, default='camera'),  # 'camera', 'user', 'system'
)

vehicle_plates = Table(
    'vehicle_plates', metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
    Column('license_plate', String(20), nullable=False),
    Column('slot_id', String, nullable=False),
    Column('zone_id', String, nullable=True),
    Column('vehicle_type', String, nullable=True),  # car, motorcycle, bus, truck
    Column('confidence', sa.Float, nullable=False),  # OCR confidence score
    Column('first_seen', TIMESTAMP, server_default=text('now()')),
    Column('last_seen', TIMESTAMP, server_default=text('now()')),
    Column('status', String, nullable=False, default='active'),  # 'active', 'exited'
    Column('image_path', String, nullable=True),  # Cropped plate image path
    Column('created_at', TIMESTAMP, server_default=text('now()')),
    Column('updated_at', TIMESTAMP, server_default=text('now()')),
)

# Indexes for vehicle_plates table
Index('idx_vehicle_plates_license_plate', vehicle_plates.c.license_plate)
Index('idx_vehicle_plates_status', vehicle_plates.c.status)
Index('idx_vehicle_plates_slot_id', vehicle_plates.c.slot_id)
Index('idx_vehicle_plates_license_status', vehicle_plates.c.license_plate, vehicle_plates.c.status)

bookings = Table(
    'bookings', metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
    Column('user_id', UUID(as_uuid=True), nullable=True),
    Column('slot_id', String, nullable=False),
    Column('status', String, default='holding'),
    Column('hold_until', TIMESTAMP, nullable=True),
    Column('created_at', TIMESTAMP, server_default=text('now()')),
    Column('updated_at', TIMESTAMP, server_default=text('now()')),
)

payments = Table(
    'payments', metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
    Column('user_id', UUID(as_uuid=True), nullable=False),
    Column('booking_id', UUID(as_uuid=True), nullable=False),
    Column('amount', sa.Float, nullable=False),
    Column('currency', String, default='USD'),
    Column('status', String, default='pending'),
    Column('payment_method', String, nullable=True),
    Column('transaction_id', String, nullable=True),
    Column('created_at', TIMESTAMP, server_default=text('now()')),
    Column('updated_at', TIMESTAMP, server_default=text('now()')),
)

notifications = Table(
    'notifications', metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
    Column('user_id', UUID(as_uuid=True), nullable=True),
    Column('type', String, nullable=False),  # 'booking_confirmation', 'slot_available', etc.
    Column('message', String, nullable=False),
    Column('is_read', Boolean, default=False),
    Column('sent_at', TIMESTAMP, server_default=text('now()')),
)

violations = Table(
    'violations', metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
    Column('violation_type', String, nullable=False),  # 'overstay', 'wrong_vehicle_type', 'unauthorized'
    Column('slot_id', String, nullable=False),
    Column('zone_id', String, nullable=True),
    Column('license_plate', String(20), nullable=True),  # From ANPR detection
    Column('vehicle_type', String, nullable=True),  # Detected vehicle type
    Column('expected_vehicle_type', String, nullable=True),  # For wrong_vehicle_type violations
    Column('booking_id', UUID(as_uuid=True), nullable=True),  # Link to booking for overstay
    Column('severity', String, nullable=False),  # 'low', 'medium', 'high'
    Column('status', String, nullable=False, default='active'),  # 'active', 'resolved', 'dismissed'
    Column('detected_at', TIMESTAMP, server_default=text('now()')),
    Column('resolved_at', TIMESTAMP, nullable=True),
    Column('resolved_by', UUID(as_uuid=True), nullable=True),  # Admin who resolved
    Column('resolution_notes', String, nullable=True),
    Column('notification_sent', Boolean, default=False),
    Column('metadata', JSON, nullable=True),  # Additional context
    Column('created_at', TIMESTAMP, server_default=text('now()')),
    Column('updated_at', TIMESTAMP, server_default=text('now()')),
)

# Indexes for violations table
Index('idx_violations_status', violations.c.status)
Index('idx_violations_slot_id', violations.c.slot_id)
Index('idx_violations_license_plate', violations.c.license_plate)
Index('idx_violations_status_detected', violations.c.status, violations.c.detected_at)
Index('idx_violations_type', violations.c.violation_type)

audit_logs = Table(
    'audit_logs', metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
    Column('user_id', UUID(as_uuid=True), nullable=True),
    Column('action', String, nullable=False),  # 'create_slot', 'update_booking', 'payment_process', etc.
    Column('resource_type', String, nullable=False),  # 'booking', 'slot', 'payment', etc.
    Column('resource_id', String, nullable=True),
    Column('details', JSON, nullable=True),  # Additional context about the action
    Column('ip_address', String, nullable=True),
    Column('user_agent', String, nullable=True),
    Column('created_at', TIMESTAMP, server_default=text('now()')),
)