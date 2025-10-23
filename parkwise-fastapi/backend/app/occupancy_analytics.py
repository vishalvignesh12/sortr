from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from . import models
from .cache import cache
import logging
import json

logger = logging.getLogger(__name__)


async def calculate_slot_occupancy_percentage(
    slot_id: str,
    start_time: datetime,
    end_time: datetime,
    session: AsyncSession
) -> float:
    """
    Calculate occupancy percentage for a slot within a time range

    Args:
        slot_id: Parking slot ID
        start_time: Start of time range
        end_time: End of time range
        session: Database session

    Returns:
        Occupancy percentage (0-100)
    """
    try:
        # Query slot_events for this time range
        result = await session.execute(
            select(models.slot_events).where(
                and_(
                    models.slot_events.c.slot_id == slot_id,
                    models.slot_events.c.created_at >= start_time,
                    models.slot_events.c.created_at <= end_time
                )
            ).order_by(models.slot_events.c.created_at.asc())
        )
        events = result.fetchall()

        if not events:
            # No events in this period - assume not occupied
            return 0.0

        # Calculate total time occupied
        total_minutes = (end_time - start_time).total_seconds() / 60
        occupied_minutes = 0.0

        # Track occupancy state changes
        is_occupied = False
        last_change_time = start_time

        for event in events:
            event_time = event.created_at

            # Check event type to determine state
            if event.event_type in ['vehicle_detected', 'entry', 'occupied']:
                if not is_occupied:
                    # Transitioning to occupied
                    is_occupied = True
                    last_change_time = event_time
            elif event.event_type in ['vehicle_left', 'exit', 'vacant']:
                if is_occupied:
                    # Was occupied, now vacant - add the occupied duration
                    duration = (event_time - last_change_time).total_seconds() / 60
                    occupied_minutes += duration
                    is_occupied = False
                    last_change_time = event_time

        # If still occupied at end of period, count remaining time
        if is_occupied:
            duration = (end_time - last_change_time).total_seconds() / 60
            occupied_minutes += duration

        # Calculate percentage
        if total_minutes > 0:
            percentage = (occupied_minutes / total_minutes) * 100
            return min(100.0, max(0.0, percentage))  # Clamp to 0-100
        else:
            return 0.0

    except Exception as e:
        logger.error(f"Error calculating occupancy for slot {slot_id}: {str(e)}")
        return 0.0


async def aggregate_occupancy_by_hour(
    zone_id: Optional[str],
    date: datetime,
    session: AsyncSession
) -> Dict[int, List[Dict]]:
    """
    Aggregate occupancy data by hour for a specific date

    Args:
        zone_id: Zone ID to filter (None for all zones)
        date: Specific date
        session: Database session

    Returns:
        Dict with keys 0-23 (hours), values are lists of {slot_id, occupancy_percentage}
    """
    try:
        # Check cache first
        cache_key = f"heatmap:{zone_id or 'all'}:{date.strftime('%Y-%m-%d')}"
        cached_data = await cache.get(cache_key)

        if cached_data:
            try:
                return json.loads(cached_data)
            except:
                pass  # Cache parse failed, regenerate

        # Get all slots for the zone
        query = select(models.slots)
        if zone_id:
            query = query.where(models.slots.c.zone_id == zone_id)

        result = await session.execute(query)
        slots = result.fetchall()

        # Build hourly data
        hourly_data = {}

        for hour in range(24):
            hour_start = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)

            slot_data = []

            for slot in slots:
                occupancy = await calculate_slot_occupancy_percentage(
                    slot.slot_id,
                    hour_start,
                    hour_end,
                    session
                )

                slot_data.append({
                    'slot_id': slot.slot_id,
                    'occupancy': round(occupancy, 1)
                })

            hourly_data[hour] = slot_data

        # Cache the result for 1 hour
        try:
            await cache.set(cache_key, json.dumps(hourly_data), expire=3600)
        except Exception as e:
            logger.warning(f"Failed to cache heatmap data: {str(e)}")

        return hourly_data

    except Exception as e:
        logger.error(f"Error aggregating hourly occupancy: {str(e)}")
        return {}


async def aggregate_occupancy_by_period(
    zone_id: Optional[str],
    start_date: datetime,
    end_date: datetime,
    session: AsyncSession
) -> List[Dict]:
    """
    Calculate average occupancy for each slot across a date range

    Args:
        zone_id: Zone ID to filter (None for all zones)
        start_date: Start of date range
        end_date: End of date range
        session: Database session

    Returns:
        List of {slot_id, occupancy_percentage (average), row, position}
    """
    try:
        # Get all slots for the zone
        query = select(models.slots)
        if zone_id:
            query = query.where(models.slots.c.zone_id == zone_id)

        result = await session.execute(query)
        slots = result.fetchall()

        slot_data = []

        for slot in slots:
            # Calculate occupancy for the entire period
            occupancy = await calculate_slot_occupancy_percentage(
                slot.slot_id,
                start_date,
                end_date,
                session
            )

            # Parse slot position from slot_id (e.g., "A1" -> row "A", position 1)
            row, position = parse_slot_position(slot.slot_id)

            slot_data.append({
                'slot_id': slot.slot_id,
                'occupancy': round(occupancy, 1),
                'row': row,
                'position': position
            })

        return slot_data

    except Exception as e:
        logger.error(f"Error aggregating period occupancy: {str(e)}")
        return []


def parse_slot_position(slot_id: str) -> tuple:
    """
    Parse slot position from slot_id

    Args:
        slot_id: Slot identifier (e.g., "A1", "B12", "ZONE1_A5")

    Returns:
        Tuple of (row: str, position: int)
    """
    try:
        # Handle formats like "A1", "B12"
        # Extract first letter as row, remaining digits as position
        import re
        match = re.match(r'([A-Za-z]+)(\d+)', slot_id)

        if match:
            row = match.group(1).upper()
            position = int(match.group(2))
            return (row, position)

        # Fallback: return slot_id as row, position 0
        return (slot_id, 0)

    except Exception as e:
        logger.warning(f"Failed to parse slot position from {slot_id}: {str(e)}")
        return (slot_id, 0)


async def get_slot_positions_with_occupancy(
    zone_id: Optional[str],
    occupancy_data: List[Dict],
    session: AsyncSession
) -> List[Dict]:
    """
    Enrich occupancy data with slot positioning information

    Args:
        zone_id: Zone ID to filter
        occupancy_data: List of occupancy data from aggregate_occupancy_by_period
        session: Database session

    Returns:
        List with additional polygon/positioning data
    """
    try:
        enriched_data = []

        for item in occupancy_data:
            slot_id = item['slot_id']

            # Get slot details
            result = await session.execute(
                select(models.slots).where(models.slots.c.slot_id == slot_id)
            )
            slot = result.fetchone()

            if slot:
                enriched_item = {
                    **item,
                    'zone_id': slot.zone_id,
                    'polygon': slot.polygon,
                    'vehicle_type_hint': slot.vehicle_type_hint
                }
                enriched_data.append(enriched_item)

        return enriched_data

    except Exception as e:
        logger.error(f"Error enriching slot positions: {str(e)}")
        return occupancy_data


async def get_peak_times(
    zone_id: Optional[str],
    days: int,
    session: AsyncSession
) -> Dict:
    """
    Analyze peak usage times over a period

    Args:
        zone_id: Zone ID to filter (None for all zones)
        days: Number of days to analyze
        session: Database session

    Returns:
        Dict with peak_hours, lowest_hours, peak_days, average_occupancy_by_hour
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get all slots for the zone
        query = select(models.slots)
        if zone_id:
            query = query.where(models.slots.c.zone_id == zone_id)

        result = await session.execute(query)
        slots = result.fetchall()

        # Calculate average occupancy for each hour across all days
        hourly_occupancy = {hour: [] for hour in range(24)}

        # For each day in the period
        current_date = start_date
        while current_date <= end_date:
            for hour in range(24):
                hour_start = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                hour_end = hour_start + timedelta(hours=1)

                # Calculate average occupancy across all slots for this hour
                hour_occupancies = []
                for slot in slots:
                    occ = await calculate_slot_occupancy_percentage(
                        slot.slot_id,
                        hour_start,
                        hour_end,
                        session
                    )
                    hour_occupancies.append(occ)

                if hour_occupancies:
                    avg_occ = sum(hour_occupancies) / len(hour_occupancies)
                    hourly_occupancy[hour].append(avg_occ)

            current_date += timedelta(days=1)

        # Calculate overall average for each hour
        average_occupancy_by_hour = {}
        for hour, occupancies in hourly_occupancy.items():
            if occupancies:
                average_occupancy_by_hour[hour] = round(sum(occupancies) / len(occupancies), 1)
            else:
                average_occupancy_by_hour[hour] = 0.0

        # Identify peak and lowest hours
        sorted_hours = sorted(average_occupancy_by_hour.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [h for h, _ in sorted_hours[:3]]
        lowest_hours = [h for h, _ in sorted_hours[-3:]]

        # TODO: Analyze peak days (would need day-of-week analysis)
        peak_days = ["Friday", "Monday"]  # Placeholder

        return {
            'peak_hours': peak_hours,
            'lowest_hours': lowest_hours,
            'peak_days': peak_days,
            'average_occupancy_by_hour': average_occupancy_by_hour
        }

    except Exception as e:
        logger.error(f"Error analyzing peak times: {str(e)}")
        return {
            'peak_hours': [],
            'lowest_hours': [],
            'peak_days': [],
            'average_occupancy_by_hour': {}
        }


async def get_available_zones(session: AsyncSession) -> List[Dict]:
    """
    Get list of all zones with slot counts

    Args:
        session: Database session

    Returns:
        List of zone objects with counts
    """
    try:
        # Get unique zones and count slots
        result = await session.execute(
            select(
                models.slots.c.zone_id,
                func.count(models.slots.c.slot_id).label('slot_count')
            ).group_by(models.slots.c.zone_id)
        )
        zones = result.fetchall()

        zone_list = []
        for zone in zones:
            if zone.zone_id:  # Skip null zones
                zone_list.append({
                    'zone_id': zone.zone_id,
                    'name': zone.zone_id.replace('_', ' ').title(),
                    'slot_count': zone.slot_count
                })

        return zone_list

    except Exception as e:
        logger.error(f"Error getting zones: {str(e)}")
        return []
