import csv
import io
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from .. import models
from ..schemas import DataExportRequest
from ..security import get_current_admin_user
from ..db import get_session
import uuid

router = APIRouter(prefix="/export")

@router.post("/")
async def export_data(
    export_request: DataExportRequest,
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Export data based on resource type and format
    Supported types: 'users', 'bookings', 'payments', 'slots', 'audit_logs'
    Supported formats: 'csv', 'json'
    """
    resource_type = export_request.resource_type.lower()
    export_format = export_request.format.lower()
    
    if export_format not in ['csv', 'json']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {export_format}. Supported formats: csv, json"
        )
    
    # Generate data based on resource type
    if resource_type == 'users':
        data = await _get_users_data(session, export_request)
    elif resource_type == 'bookings':
        data = await _get_bookings_data(session, export_request)
    elif resource_type == 'payments':
        data = await _get_payments_data(session, export_request)
    elif resource_type == 'slots':
        data = await _get_slots_data(session, export_request)
    elif resource_type == 'audit_logs':
        data = await _get_audit_logs_data(session, export_request)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported resource type: {resource_type}. Supported types: users, bookings, payments, slots, audit_logs"
        )
    
    # Format data based on requested format
    if export_format == 'csv':
        content = _generate_csv_content(data, resource_type)
        filename = f"parkwise_{resource_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        media_type = "text/csv"
    else:  # JSON
        content = json.dumps(data, default=str, indent=2)
        filename = f"parkwise_{resource_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        media_type = "application/json"
    
    # Create response with appropriate headers
    response = Response(content=content, media_type=media_type)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    
    return response

async def _get_users_data(session: AsyncSession, request: DataExportRequest):
    """Get users data for export"""
    query = select(models.users)
    
    # Apply date filters if provided
    if request.start_date:
        query = query.where(models.users.c.created_at >= request.start_date)
    if request.end_date:
        query = query.where(models.users.c.created_at <= request.end_date)
    
    # Apply additional filters if provided
    if request.filters:
        for field, value in request.filters.items():
            if hasattr(models.users.c, field):
                query = query.where(getattr(models.users.c, field) == value)
    
    query = query.order_by(models.users.c.created_at.desc())
    
    result = await session.execute(query)
    users = result.fetchall()
    
    # Convert to dictionary format
    users_data = []
    for user in users:
        users_data.append({
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        })
    
    return users_data

async def _get_bookings_data(session: AsyncSession, request: DataExportRequest):
    """Get bookings data for export"""
    query = select(models.bookings)
    
    # Apply date filters if provided
    if request.start_date:
        query = query.where(models.bookings.c.created_at >= request.start_date)
    if request.end_date:
        query = query.where(models.bookings.c.created_at <= request.end_date)
    
    # Apply additional filters if provided
    if request.filters:
        for field, value in request.filters.items():
            if hasattr(models.bookings.c, field):
                query = query.where(getattr(models.bookings.c, field) == value)
    
    query = query.order_by(models.bookings.c.created_at.desc())
    
    result = await session.execute(query)
    bookings = result.fetchall()
    
    # Convert to dictionary format
    bookings_data = []
    for booking in bookings:
        bookings_data.append({
            "id": str(booking.id),
            "user_id": str(booking.user_id) if booking.user_id else None,
            "slot_id": booking.slot_id,
            "status": booking.status,
            "hold_until": booking.hold_until.isoformat() if booking.hold_until else None,
            "created_at": booking.created_at.isoformat() if booking.created_at else None,
            "updated_at": booking.updated_at.isoformat() if booking.updated_at else None
        })
    
    return bookings_data

async def _get_payments_data(session: AsyncSession, request: DataExportRequest):
    """Get payments data for export"""
    query = select(models.payments)
    
    # Apply date filters if provided
    if request.start_date:
        query = query.where(models.payments.c.created_at >= request.start_date)
    if request.end_date:
        query = query.where(models.payments.c.created_at <= request.end_date)
    
    # Apply additional filters if provided
    if request.filters:
        for field, value in request.filters.items():
            if hasattr(models.payments.c, field):
                query = query.where(getattr(models.payments.c, field) == value)
    
    query = query.order_by(models.payments.c.created_at.desc())
    
    result = await session.execute(query)
    payments = result.fetchall()
    
    # Convert to dictionary format
    payments_data = []
    for payment in payments:
        payments_data.append({
            "id": str(payment.id),
            "user_id": str(payment.user_id),
            "booking_id": str(payment.booking_id),
            "amount": float(payment.amount),
            "currency": payment.currency,
            "status": payment.status,
            "payment_method": payment.payment_method,
            "transaction_id": payment.transaction_id,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "updated_at": payment.updated_at.isoformat() if payment.updated_at else None
        })
    
    return payments_data

async def _get_slots_data(session: AsyncSession, request: DataExportRequest):
    """Get slots data for export"""
    query = text("""
        SELECT s.slot_id, s.zone_id, s.polygon, s.vehicle_type_hint, s.created_at as slot_created_at,
               ss.occupied, ss.confidence, ss.vehicle_type, ss.last_seen, ss.reserved_until, 
               ss.predicted_free_minutes, ss.prediction_confidence, ss.updated_at as status_updated_at
        FROM slots s
        LEFT JOIN slot_status ss ON s.slot_id = ss.slot_id
        ORDER BY s.slot_id
    """)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    # Convert to dictionary format
    slots_data = []
    for row in rows:
        slot_dict = {
            "slot_id": row.slot_id,
            "zone_id": row.zone_id,
            "polygon": row.polygon,
            "vehicle_type_hint": row.vehicle_type_hint,
            "slot_created_at": row.slot_created_at.isoformat() if row.slot_created_at else None,
            "occupied": row.occupied,
            "confidence": float(row.confidence) if row.confidence else None,
            "vehicle_type": row.vehicle_type,
            "last_seen": row.last_seen.isoformat() if row.last_seen else None,
            "reserved_until": row.reserved_until.isoformat() if row.reserved_until else None,
            "predicted_free_minutes": row.predicted_free_minutes,
            "prediction_confidence": float(row.prediction_confidence) if row.prediction_confidence else None,
            "status_updated_at": row.status_updated_at.isoformat() if row.status_updated_at else None
        }
        slots_data.append(slot_dict)
    
    return slots_data

async def _get_audit_logs_data(session: AsyncSession, request: DataExportRequest):
    """Get audit logs data for export"""
    query = select(models.audit_logs)
    
    # Apply date filters if provided
    if request.start_date:
        query = query.where(models.audit_logs.c.created_at >= request.start_date)
    if request.end_date:
        query = query.where(models.audit_logs.c.created_at <= request.end_date)
    
    # Apply additional filters if provided
    if request.filters:
        for field, value in request.filters.items():
            if hasattr(models.audit_logs.c, field):
                query = query.where(getattr(models.audit_logs.c, field) == value)
    
    query = query.order_by(models.audit_logs.c.created_at.desc())
    
    result = await session.execute(query)
    audit_logs = result.fetchall()
    
    # Convert to dictionary format
    audit_logs_data = []
    for log in audit_logs:
        audit_logs_data.append({
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    return audit_logs_data

def _generate_csv_content(data, resource_type):
    """Generate CSV content from data"""
    if not data:
        return ""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    
    for row in data:
        # Handle special data types
        clean_row = {}
        for key, value in row.items():
            if isinstance(value, (datetime,)):
                clean_row[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                clean_row[key] = json.dumps(value)
            else:
                clean_row[key] = value
        writer.writerow(clean_row)
    
    content = output.getvalue()
    output.close()
    
    return content