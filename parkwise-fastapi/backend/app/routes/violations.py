from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from .. import models
from ..db import get_session
from ..security import get_current_user, get_current_admin_user
from .. import violation_detector
import logging

router = APIRouter(prefix="/v1/violations", tags=["violations"])
logger = logging.getLogger(__name__)


class ResolveViolationRequest(BaseModel):
    resolution_notes: Optional[str] = None


class DismissViolationRequest(BaseModel):
    dismissal_reason: str


@router.get("")
async def list_violations(
    status_filter: Optional[str] = 'active',
    violation_type: Optional[str] = None,
    severity: Optional[str] = None,
    zone_id: Optional[str] = None,
    slot_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = 'detected_at',
    sort_order: str = 'desc',
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    List all violations with filtering and pagination

    Admins see all violations, regular users see only their own
    """
    try:
        # Build query
        query = select(models.violations).offset(offset).limit(limit)

        # Apply filters
        if status_filter:
            query = query.where(models.violations.c.status == status_filter)

        if violation_type:
            query = query.where(models.violations.c.violation_type == violation_type)

        if severity:
            query = query.where(models.violations.c.severity == severity)

        if zone_id:
            query = query.where(models.violations.c.zone_id == zone_id)

        if slot_id:
            query = query.where(models.violations.c.slot_id == slot_id)

        # If not admin, filter to user's bookings only
        if not current_user.is_admin:
            # Get user's booking IDs
            user_bookings = await session.execute(
                select(models.bookings.c.id).where(
                    models.bookings.c.user_id == str(current_user.id)
                )
            )
            booking_ids = [str(b.id) for b in user_bookings.fetchall()]

            if booking_ids:
                query = query.where(models.violations.c.booking_id.in_(booking_ids))
            else:
                # User has no bookings, return empty
                return {
                    'total': 0,
                    'offset': offset,
                    'limit': limit,
                    'violations': []
                }

        # Apply sorting
        if sort_by == 'detected_at':
            order_col = models.violations.c.detected_at
        elif sort_by == 'severity':
            order_col = models.violations.c.severity
        else:
            order_col = models.violations.c.detected_at

        if sort_order == 'asc':
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        result = await session.execute(query)
        violations = result.fetchall()

        # Convert to list of dicts
        violations_list = []
        for v in violations:
            violations_list.append({
                'id': str(v.id),
                'violation_type': v.violation_type,
                'slot_id': v.slot_id,
                'zone_id': v.zone_id,
                'license_plate': v.license_plate,
                'vehicle_type': v.vehicle_type,
                'expected_vehicle_type': v.expected_vehicle_type,
                'booking_id': str(v.booking_id) if v.booking_id else None,
                'severity': v.severity,
                'status': v.status,
                'detected_at': v.detected_at.isoformat() if v.detected_at else None,
                'resolved_at': v.resolved_at.isoformat() if v.resolved_at else None,
                'resolved_by': str(v.resolved_by) if v.resolved_by else None,
                'resolution_notes': v.resolution_notes,
                'notification_sent': v.notification_sent,
                'metadata': v.metadata
            })

        return {
            'total': len(violations_list),
            'offset': offset,
            'limit': limit,
            'violations': violations_list
        }

    except Exception as e:
        logger.error(f"Error listing violations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list violations: {str(e)}"
        )


@router.get("/{violation_id}")
async def get_violation_details(
    violation_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get detailed information for specific violation
    """
    try:
        # Get violation
        result = await session.execute(
            select(models.violations).where(models.violations.c.id == violation_id)
        )
        violation = result.fetchone()

        if not violation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Violation not found"
            )

        # Check authorization (non-admin can only view their own)
        if not current_user.is_admin:
            if violation.booking_id:
                booking_result = await session.execute(
                    select(models.bookings).where(models.bookings.c.id == violation.booking_id)
                )
                booking = booking_result.fetchone()

                if not booking or str(booking.user_id) != str(current_user.id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to view this violation"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this violation"
                )

        # Get related slot info
        slot_result = await session.execute(
            select(models.slots).where(models.slots.c.slot_id == violation.slot_id)
        )
        slot = slot_result.fetchone()

        # Get related booking info if exists
        booking_info = None
        if violation.booking_id:
            booking_result = await session.execute(
                select(models.bookings).where(models.bookings.c.id == violation.booking_id)
            )
            booking = booking_result.fetchone()
            if booking:
                booking_info = {
                    'id': str(booking.id),
                    'user_id': str(booking.user_id),
                    'status': booking.status,
                    'hold_until': booking.hold_until.isoformat() if booking.hold_until else None
                }

        return {
            'id': str(violation.id),
            'violation_type': violation.violation_type,
            'slot_id': violation.slot_id,
            'zone_id': violation.zone_id,
            'license_plate': violation.license_plate,
            'vehicle_type': violation.vehicle_type,
            'expected_vehicle_type': violation.expected_vehicle_type,
            'booking_id': str(violation.booking_id) if violation.booking_id else None,
            'severity': violation.severity,
            'status': violation.status,
            'detected_at': violation.detected_at.isoformat() if violation.detected_at else None,
            'resolved_at': violation.resolved_at.isoformat() if violation.resolved_at else None,
            'resolved_by': str(violation.resolved_by) if violation.resolved_by else None,
            'resolution_notes': violation.resolution_notes,
            'notification_sent': violation.notification_sent,
            'metadata': violation.metadata,
            'slot_info': {
                'zone_id': slot.zone_id if slot else None,
                'vehicle_type_hint': slot.vehicle_type_hint if slot else None
            } if slot else None,
            'booking_info': booking_info
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting violation details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get violation details: {str(e)}"
        )


@router.post("/{violation_id}/resolve")
async def resolve_violation(
    violation_id: str,
    request: ResolveViolationRequest,
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin endpoint to mark violation as resolved
    """
    try:
        # Check if violation exists
        result = await session.execute(
            select(models.violations).where(models.violations.c.id == violation_id)
        )
        violation = result.fetchone()

        if not violation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Violation not found"
            )

        if violation.status == 'resolved':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Violation already resolved"
            )

        # Resolve the violation
        resolved_violation = await violation_detector.resolve_violation(
            violation_id,
            str(current_user.id),
            request.resolution_notes,
            session
        )

        if not resolved_violation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resolve violation"
            )

        return {
            'message': 'Violation resolved successfully',
            'violation': resolved_violation
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving violation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve violation: {str(e)}"
        )


@router.post("/{violation_id}/dismiss")
async def dismiss_violation(
    violation_id: str,
    request: DismissViolationRequest,
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin endpoint to dismiss false positive violations
    """
    try:
        from sqlalchemy import update, insert

        # Check if violation exists
        result = await session.execute(
            select(models.violations).where(models.violations.c.id == violation_id)
        )
        violation = result.fetchone()

        if not violation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Violation not found"
            )

        # Update status to dismissed
        await session.execute(
            update(models.violations)
            .where(models.violations.c.id == violation_id)
            .values(
                status='dismissed',
                resolved_at=datetime.utcnow(),
                resolved_by=str(current_user.id),
                resolution_notes=f"Dismissed: {request.dismissal_reason}",
                updated_at=datetime.utcnow()
            )
        )

        # Log audit trail
        await session.execute(
            insert(models.audit_logs).values(
                user_id=str(current_user.id),
                action='dismiss_violation',
                resource_type='violation',
                resource_id=violation_id,
                details={
                    'violation_type': violation.violation_type,
                    'slot_id': violation.slot_id,
                    'reason': request.dismissal_reason
                }
            )
        )

        await session.commit()

        logger.info(f"Violation {violation_id} dismissed by admin {current_user.email}")

        return {
            'message': 'Violation dismissed successfully',
            'violation_id': violation_id,
            'status': 'dismissed'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing violation: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dismiss violation: {str(e)}"
        )


@router.get("/stats/summary")
async def get_violation_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    zone_id: Optional[str] = None,
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get violation statistics for analytics (admin only)
    """
    try:
        # Build base query
        query = select(models.violations)

        # Apply filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(models.violations.c.detected_at >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(models.violations.c.detected_at <= end_dt)

        if zone_id:
            query = query.where(models.violations.c.zone_id == zone_id)

        result = await session.execute(query)
        violations = result.fetchall()

        # Calculate statistics
        total = len(violations)
        by_type = {'overstay': 0, 'wrong_vehicle_type': 0, 'unauthorized': 0}
        by_severity = {'low': 0, 'medium': 0, 'high': 0}
        by_status = {'active': 0, 'resolved': 0, 'dismissed': 0}

        resolution_times = []

        for v in violations:
            # Count by type
            if v.violation_type in by_type:
                by_type[v.violation_type] += 1

            # Count by severity
            if v.severity in by_severity:
                by_severity[v.severity] += 1

            # Count by status
            if v.status in by_status:
                by_status[v.status] += 1

            # Calculate resolution time
            if v.resolved_at and v.detected_at:
                time_diff = v.resolved_at - v.detected_at
                resolution_times.append(time_diff.total_seconds() / 3600)  # hours

        # Calculate average resolution time
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

        # Calculate resolution rate
        resolved_count = by_status['resolved']
        resolution_rate = (resolved_count / total * 100) if total > 0 else 0

        return {
            'total_violations': total,
            'by_type': by_type,
            'by_severity': by_severity,
            'by_status': by_status,
            'resolution_rate': round(resolution_rate, 2),
            'average_resolution_time_hours': round(avg_resolution_time, 2)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting violation stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get violation statistics: {str(e)}"
        )


@router.post("/check-slot/{slot_id}")
async def check_slot_violations(
    slot_id: str,
    current_user = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Manual violation check for specific slot (admin/testing)
    Returns preview without recording
    """
    try:
        # Get slot status
        slot_status_result = await session.execute(
            select(models.slot_status).where(models.slot_status.c.slot_id == slot_id)
        )
        slot_status = slot_status_result.fetchone()

        if not slot_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Slot {slot_id} not found"
            )

        # Get slot info
        slot_result = await session.execute(
            select(models.slots).where(models.slots.c.slot_id == slot_id)
        )
        slot = slot_result.fetchone()

        # Get plate if available
        plate_result = await session.execute(
            select(models.vehicle_plates).where(
                models.vehicle_plates.c.slot_id == slot_id,
                models.vehicle_plates.c.status == 'active'
            ).order_by(models.vehicle_plates.c.last_seen.desc()).limit(1)
        )
        plate = plate_result.fetchone()

        slot_data = {
            'occupied': slot_status.occupied,
            'vehicle_type': slot_status.vehicle_type,
            'license_plate': plate.license_plate if plate else None,
            'zone_id': slot.zone_id if slot else None
        }

        # Detect violations (preview mode - don't record)
        violations = await violation_detector.detect_all_violations_for_slot(
            slot_id, slot_data, session
        )

        return {
            'slot_id': slot_id,
            'slot_status': {
                'occupied': slot_status.occupied,
                'vehicle_type': slot_status.vehicle_type
            },
            'detected_violations': violations,
            'count': len(violations)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking slot violations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check slot violations: {str(e)}"
        )
