from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from .. import models
from ..db import get_session
from ..security import get_current_user
from .. import occupancy_analytics
import logging

router = APIRouter(prefix="/v1/heatmaps", tags=["heatmaps"])
logger = logging.getLogger(__name__)


@router.get("/occupancy/hourly")
async def get_hourly_occupancy(
    date: str,
    zone_id: Optional[str] = None,
    hour: Optional[int] = None,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get hourly occupancy data for time slider

    Query parameters:
    - date: ISO date string (YYYY-MM-DD), e.g., "2024-01-15"
    - zone_id: Optional zone filter
    - hour: Optional specific hour 0-23 (if provided, returns only that hour)
    """
    try:
        # Parse date
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

        # Validate hour if provided
        if hour is not None and (hour < 0 or hour > 23):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hour must be between 0 and 23"
            )

        # Get hourly data
        hourly_data = await occupancy_analytics.aggregate_occupancy_by_hour(
            zone_id, date_obj, session
        )

        # If specific hour requested, return only that hour
        if hour is not None:
            if hour in hourly_data:
                return {
                    'date': date,
                    'zone_id': zone_id,
                    'hour': hour,
                    'slots': hourly_data[hour]
                }
            else:
                return {
                    'date': date,
                    'zone_id': zone_id,
                    'hour': hour,
                    'slots': []
                }

        # Return all hours
        return {
            'date': date,
            'zone_id': zone_id,
            'hours': hourly_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hourly occupancy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hourly occupancy: {str(e)}"
        )


@router.get("/occupancy/average")
async def get_average_occupancy(
    start_date: str,
    end_date: str,
    zone_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get average occupancy over a period

    Query parameters:
    - start_date: ISO date string (YYYY-MM-DD)
    - end_date: ISO date string (YYYY-MM-DD)
    - zone_id: Optional zone filter
    """
    try:
        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

        # Validate date range
        if end_dt < start_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )

        # Get period data
        slot_data = await occupancy_analytics.aggregate_occupancy_by_period(
            zone_id, start_dt, end_dt, session
        )

        return {
            'zone_id': zone_id,
            'period': {
                'start': start_date,
                'end': end_date
            },
            'slots': slot_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting average occupancy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get average occupancy: {str(e)}"
        )


@router.get("/zones")
async def list_zones(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    List all available zones for filtering
    """
    try:
        zones = await occupancy_analytics.get_available_zones(session)

        return {
            'zones': zones,
            'total': len(zones)
        }

    except Exception as e:
        logger.error(f"Error listing zones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list zones: {str(e)}"
        )


@router.get("/peak-times")
async def get_peak_times(
    zone_id: Optional[str] = None,
    days: int = 7,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get peak usage times for analytics insights

    Query parameters:
    - zone_id: Optional zone filter
    - days: Number of days to analyze (default: 7)
    """
    try:
        # Validate days parameter
        if days < 1 or days > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Days must be between 1 and 90"
            )

        # Get peak times analysis
        peak_data = await occupancy_analytics.get_peak_times(
            zone_id, days, session
        )

        return {
            'zone_id': zone_id,
            'analysis_period_days': days,
            **peak_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting peak times: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get peak times: {str(e)}"
        )
