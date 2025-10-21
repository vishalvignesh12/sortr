from sqlalchemy import (
    Table, Column, String, Boolean, Integer, TIMESTAMP, JSON, text, MetaData
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
    Column('created_at', TIMESTAMP, server_default=text('now()')),
    Column('source', String, default='camera'),  # 'camera', 'user', 'system'
)

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