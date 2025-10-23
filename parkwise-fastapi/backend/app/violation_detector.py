from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from . import models
import logging
import uuid

logger = logging.getLogger(__name__)

# Grace period for overstay violations (in minutes)
OVERSTAY_GRACE_PERIOD = 15


def calculate_severity_for_overstay(minutes_overdue: float) -> str:
    """
    Calculate severity level based on how long vehicle has overstayed

    Args:
        minutes_overdue: Number of minutes past the booking end time

    Returns:
        Severity level: 'low', 'medium', or 'high'
    """
    if minutes_overdue < 30:
        return 'low'
    elif minutes_overdue < 60:
        return 'medium'
    else:
        return 'high'


async def check_overstay_violation(
    slot_id: str,
    current_time: datetime,
    session: AsyncSession
) -> Optional[Dict]:
    """
    Check if a vehicle has overstayed its booking time

    Args:
        slot_id: Parking slot ID
        current_time: Current timestamp
        session: Database session

    Returns:
        Violation dict or None if no violation
    """
    try:
        # Query for active booking for this slot
        result = await session.execute(
            select(models.bookings).where(
                models.bookings.c.slot_id == slot_id,
                models.bookings.c.status.in_(['holding', 'confirmed'])
            ).order_by(models.bookings.c.hold_until.desc()).limit(1)
        )
        booking = result.fetchone()

        if not booking or not booking.hold_until:
            return None

        # Check if booking has expired (with grace period)
        grace_period = timedelta(minutes=OVERSTAY_GRACE_PERIOD)
        expiry_with_grace = booking.hold_until + grace_period

        if current_time > expiry_with_grace:
            # Check if slot is still occupied
            slot_status_result = await session.execute(
                select(models.slot_status).where(
                    models.slot_status.c.slot_id == slot_id
                )
            )
            slot_status = slot_status_result.fetchone()

            if slot_status and slot_status.occupied:
                # Calculate how long overdue
                time_overdue = current_time - booking.hold_until
                minutes_overdue = time_overdue.total_seconds() / 60

                severity = calculate_severity_for_overstay(minutes_overdue)

                return {
                    'violation_type': 'overstay',
                    'slot_id': slot_id,
                    'booking_id': str(booking.id),
                    'severity': severity,
                    'metadata': {
                        'expected_exit': booking.hold_until.isoformat(),
                        'minutes_overdue': round(minutes_overdue, 2),
                        'grace_period_minutes': OVERSTAY_GRACE_PERIOD
                    }
                }

        return None

    except Exception as e:
        logger.error(f"Error checking overstay violation for slot {slot_id}: {str(e)}")
        return None


async def check_wrong_vehicle_type_violation(
    slot_id: str,
    detected_vehicle_type: str,
    session: AsyncSession
) -> Optional[Dict]:
    """
    Check if detected vehicle type doesn't match slot's expected type

    Args:
        slot_id: Parking slot ID
        detected_vehicle_type: Vehicle type from YOLO detection
        session: Database session

    Returns:
        Violation dict or None if no violation
    """
    try:
        # Query slot configuration
        result = await session.execute(
            select(models.slots).where(models.slots.c.slot_id == slot_id)
        )
        slot = result.fetchone()

        if not slot or not slot.vehicle_type_hint:
            # No type hint configured, no violation
            return None

        # Check if detected type matches hint
        if detected_vehicle_type != slot.vehicle_type_hint:
            return {
                'violation_type': 'wrong_vehicle_type',
                'slot_id': slot_id,
                'vehicle_type': detected_vehicle_type,
                'expected_vehicle_type': slot.vehicle_type_hint,
                'severity': 'medium',
                'metadata': {
                    'detected': detected_vehicle_type,
                    'expected': slot.vehicle_type_hint
                }
            }

        return None

    except Exception as e:
        logger.error(f"Error checking vehicle type violation for slot {slot_id}: {str(e)}")
        return None


async def check_unauthorized_parking_violation(
    slot_id: str,
    license_plate: Optional[str],
    session: AsyncSession
) -> Optional[Dict]:
    """
    Check if vehicle is parked without a valid booking

    Args:
        slot_id: Parking slot ID
        license_plate: Detected license plate (if available)
        session: Database session

    Returns:
        Violation dict or None if no violation
    """
    try:
        # Check if slot has active booking
        result = await session.execute(
            select(models.bookings).where(
                models.bookings.c.slot_id == slot_id,
                models.bookings.c.status.in_(['holding', 'confirmed', 'active'])
            )
        )
        booking = result.fetchone()

        # Check if slot is occupied
        slot_status_result = await session.execute(
            select(models.slot_status).where(
                models.slot_status.c.slot_id == slot_id
            )
        )
        slot_status = slot_status_result.fetchone()

        if slot_status and slot_status.occupied and not booking:
            # Check if slot is configured as public parking (no booking required)
            slot_result = await session.execute(
                select(models.slots).where(models.slots.c.slot_id == slot_id)
            )
            slot = slot_result.fetchone()

            # Check metadata for public flag (if exists)
            if slot and isinstance(slot.polygon, dict):
                metadata = slot.polygon.get('metadata', {})
                if metadata.get('public', False):
                    return None

            return {
                'violation_type': 'unauthorized',
                'slot_id': slot_id,
                'license_plate': license_plate,
                'severity': 'high',
                'metadata': {
                    'reason': 'no_active_booking'
                }
            }

        return None

    except Exception as e:
        logger.error(f"Error checking unauthorized parking for slot {slot_id}: {str(e)}")
        return None


async def detect_all_violations_for_slot(
    slot_id: str,
    slot_data: Dict,
    session: AsyncSession
) -> List[Dict]:
    """
    Detect all violations for a specific parking slot

    Args:
        slot_id: Parking slot ID
        slot_data: Dict containing occupied status, vehicle_type, license_plate, etc.
        session: Database session

    Returns:
        List of violation dicts
    """
    violations = []
    current_time = datetime.utcnow()

    try:
        # Only check for violations if slot is occupied
        if not slot_data.get('occupied', False):
            return violations

        # Check for overstay violation
        overstay = await check_overstay_violation(slot_id, current_time, session)
        if overstay:
            # Add common fields
            overstay['zone_id'] = slot_data.get('zone_id')
            overstay['vehicle_type'] = slot_data.get('vehicle_type')
            overstay['license_plate'] = slot_data.get('license_plate')
            violations.append(overstay)

        # Check for wrong vehicle type violation
        if slot_data.get('vehicle_type'):
            wrong_type = await check_wrong_vehicle_type_violation(
                slot_id, slot_data['vehicle_type'], session
            )
            if wrong_type:
                wrong_type['zone_id'] = slot_data.get('zone_id')
                wrong_type['license_plate'] = slot_data.get('license_plate')
                violations.append(wrong_type)

        # Check for unauthorized parking violation
        unauthorized = await check_unauthorized_parking_violation(
            slot_id, slot_data.get('license_plate'), session
        )
        if unauthorized:
            unauthorized['zone_id'] = slot_data.get('zone_id')
            unauthorized['vehicle_type'] = slot_data.get('vehicle_type')
            violations.append(unauthorized)

        return violations

    except Exception as e:
        logger.error(f"Error detecting violations for slot {slot_id}: {str(e)}")
        return violations


async def record_violation(
    violation_dict: Dict,
    session: AsyncSession
) -> Optional[Dict]:
    """
    Record a violation in the database (or update existing)

    Args:
        violation_dict: Violation details
        session: Database session

    Returns:
        Recorded violation record or None on error
    """
    try:
        # Check if identical active violation already exists
        existing_result = await session.execute(
            select(models.violations).where(
                models.violations.c.slot_id == violation_dict['slot_id'],
                models.violations.c.violation_type == violation_dict['violation_type'],
                models.violations.c.status == 'active'
            )
        )
        existing = existing_result.fetchone()

        if existing:
            # Update detected_at timestamp (refresh the violation)
            await session.execute(
                update(models.violations)
                .where(models.violations.c.id == existing.id)
                .values(
                    detected_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    # Update metadata in case details changed
                    metadata=violation_dict.get('metadata')
                )
            )
            await session.commit()

            logger.info(f"Refreshed existing violation {existing.id} for slot {violation_dict['slot_id']}")

            return {
                'id': str(existing.id),
                'violation_type': existing.violation_type,
                'slot_id': existing.slot_id,
                'status': existing.status,
                'is_new': False
            }

        # Insert new violation
        violation_id = str(uuid.uuid4())
        await session.execute(
            insert(models.violations).values(
                id=violation_id,
                violation_type=violation_dict['violation_type'],
                slot_id=violation_dict['slot_id'],
                zone_id=violation_dict.get('zone_id'),
                license_plate=violation_dict.get('license_plate'),
                vehicle_type=violation_dict.get('vehicle_type'),
                expected_vehicle_type=violation_dict.get('expected_vehicle_type'),
                booking_id=violation_dict.get('booking_id'),
                severity=violation_dict['severity'],
                status='active',
                detected_at=datetime.utcnow(),
                notification_sent=False,
                metadata=violation_dict.get('metadata')
            )
        )

        # Log to audit trail
        await session.execute(
            insert(models.audit_logs).values(
                action='violation_detected',
                resource_type='violation',
                resource_id=violation_id,
                details={
                    'violation_type': violation_dict['violation_type'],
                    'slot_id': violation_dict['slot_id'],
                    'severity': violation_dict['severity']
                }
            )
        )

        await session.commit()

        logger.info(f"Recorded new {violation_dict['violation_type']} violation for slot {violation_dict['slot_id']}")

        return {
            'id': violation_id,
            'violation_type': violation_dict['violation_type'],
            'slot_id': violation_dict['slot_id'],
            'severity': violation_dict['severity'],
            'status': 'active',
            'is_new': True
        }

    except Exception as e:
        logger.error(f"Error recording violation: {str(e)}")
        await session.rollback()
        return None


async def resolve_violation(
    violation_id: str,
    resolved_by_user_id: str,
    notes: Optional[str],
    session: AsyncSession
) -> Optional[Dict]:
    """
    Mark a violation as resolved

    Args:
        violation_id: Violation ID (UUID)
        resolved_by_user_id: User ID of admin resolving
        notes: Resolution notes
        session: Database session

    Returns:
        Updated violation record or None on error
    """
    try:
        # Get violation
        result = await session.execute(
            select(models.violations).where(models.violations.c.id == violation_id)
        )
        violation = result.fetchone()

        if not violation:
            return None

        # Update status
        await session.execute(
            update(models.violations)
            .where(models.violations.c.id == violation_id)
            .values(
                status='resolved',
                resolved_at=datetime.utcnow(),
                resolved_by=resolved_by_user_id,
                resolution_notes=notes,
                updated_at=datetime.utcnow()
            )
        )

        # Log audit trail
        await session.execute(
            insert(models.audit_logs).values(
                user_id=resolved_by_user_id,
                action='resolve_violation',
                resource_type='violation',
                resource_id=violation_id,
                details={
                    'violation_type': violation.violation_type,
                    'slot_id': violation.slot_id,
                    'notes': notes
                }
            )
        )

        await session.commit()

        logger.info(f"Violation {violation_id} resolved by user {resolved_by_user_id}")

        return {
            'id': str(violation.id),
            'violation_type': violation.violation_type,
            'slot_id': violation.slot_id,
            'status': 'resolved',
            'resolved_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error resolving violation {violation_id}: {str(e)}")
        await session.rollback()
        return None


async def auto_resolve_violations_for_slot(
    slot_id: str,
    session: AsyncSession
) -> int:
    """
    Auto-resolve all active violations for a slot (when vehicle exits)

    Args:
        slot_id: Parking slot ID
        session: Database session

    Returns:
        Number of violations auto-resolved
    """
    try:
        # Find all active violations for this slot
        result = await session.execute(
            select(models.violations).where(
                models.violations.c.slot_id == slot_id,
                models.violations.c.status == 'active'
            )
        )
        violations = result.fetchall()

        if not violations:
            return 0

        count = 0
        for violation in violations:
            await session.execute(
                update(models.violations)
                .where(models.violations.c.id == violation.id)
                .values(
                    status='resolved',
                    resolved_at=datetime.utcnow(),
                    resolution_notes='Auto-resolved: vehicle exited',
                    updated_at=datetime.utcnow()
                )
            )

            # Log audit trail
            await session.execute(
                insert(models.audit_logs).values(
                    action='auto_resolve_violation',
                    resource_type='violation',
                    resource_id=str(violation.id),
                    details={
                        'violation_type': violation.violation_type,
                        'slot_id': slot_id,
                        'reason': 'vehicle_exited'
                    }
                )
            )

            count += 1

        await session.commit()

        logger.info(f"Auto-resolved {count} violations for slot {slot_id}")

        return count

    except Exception as e:
        logger.error(f"Error auto-resolving violations for slot {slot_id}: {str(e)}")
        await session.rollback()
        return 0
