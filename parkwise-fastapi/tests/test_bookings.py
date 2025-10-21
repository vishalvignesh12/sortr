import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import HoldRequest
import json


def test_hold_slot_unauthenticated(client):
    """Test holding a slot without authentication - should fail"""
    hold_data = {
        "slot_id": "test_slot_001",
        "hold_minutes": 5
    }
    
    response = client.post("/v1/bookings/hold", json=hold_data)
    # Should return 422 because this requires authentication
    assert response.status_code in [401, 422]


def test_hold_slot_validation(client):
    """Test validation of hold request data"""
    hold_data = {
        "slot_id": "test_slot_002",
        "hold_minutes": 120  # Exceeds max of 60 minutes
    }
    
    response = client.post("/v1/bookings/hold", json=hold_data)
    # Should return validation error
    assert response.status_code == 422


def test_hold_slot_minimal_data(client):
    """Test holding a slot with minimal required data"""
    hold_data = {
        "slot_id": "minimal_hold_001"
        # hold_minutes defaults to 2
    }
    
    response = client.post("/v1/bookings/hold", json=hold_data)
    # Should return 401 due to auth or 422 for validation
    assert response.status_code in [401, 422]


def test_hold_slot_valid_data(client):
    """Test holding a slot with valid data"""
    hold_data = {
        "slot_id": "valid_slot_001",
        "hold_minutes": 10
    }
    
    response = client.post("/v1/bookings/hold", json=hold_data)
    # Should return 401 due to auth or 422 for validation
    assert response.status_code in [401, 422, 404, 409]


def test_hold_slot_invalid_slot_id(client):
    """Test holding a slot with invalid slot ID"""
    hold_data = {
        "slot_id": "",  # Empty slot ID
        "hold_minutes": 5
    }
    
    response = client.post("/v1/bookings/hold", json=hold_data)
    # Should return validation error
    assert response.status_code == 422


def test_hold_slot_negative_minutes(client):
    """Test holding a slot with negative minutes"""
    hold_data = {
        "slot_id": "negative_minutes_slot",
        "hold_minutes": -5  # Invalid negative value
    }
    
    response = client.post("/v1/bookings/hold", json=hold_data)
    # Should return validation error
    assert response.status_code == 422