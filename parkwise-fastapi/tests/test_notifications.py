import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import NotificationCreate
import json


def test_create_notification_unauthenticated(client):
    """Test creating a notification without authentication"""
    notification_data = {
        "type": "booking_confirmation",
        "message": "Your booking has been confirmed"
    }
    
    response = client.post("/notifications/", json=notification_data)
    # Should return 401 due to authentication requirement
    assert response.status_code == 401


def test_create_notification_invalid_type(client):
    """Test creating a notification with invalid type"""
    notification_data = {
        "type": "invalid_type",  # Not in allowed types
        "message": "This is an invalid notification"
    }
    
    response = client.post("/notifications/", json=notification_data)
    # Should return validation error
    assert response.status_code == 422


def test_create_notification_empty_message(client):
    """Test creating a notification with empty message"""
    notification_data = {
        "type": "booking_confirmation",
        "message": ""  # Empty message
    }
    
    response = client.post("/notifications/", json=notification_data)
    # Should return validation error
    assert response.status_code == 422


def test_create_notification_long_message(client):
    """Test creating a notification with too long message"""
    long_message = "A" * 600  # Exceeds 500 character limit
    notification_data = {
        "type": "booking_confirmation",
        "message": long_message
    }
    
    response = client.post("/notifications/", json=notification_data)
    # Should return validation error
    assert response.status_code == 422


def test_create_notification_valid_data(client):
    """Test creating a notification with valid data"""
    notification_data = {
        "type": "booking_confirmation",
        "message": "Your booking has been confirmed successfully"
    }
    
    response = client.post("/notifications/", json=notification_data)
    # Should return 401 due to authentication requirement
    assert response.status_code == 401


def test_get_user_notifications_unauthenticated(client):
    """Test getting user notifications without authentication"""
    response = client.get("/notifications/")
    # Should return 401 due to authentication requirement
    assert response.status_code == 401


def test_get_unread_notifications_unauthenticated(client):
    """Test getting unread notifications without authentication"""
    response = client.get("/notifications/unread")
    # Should return 401 due to authentication requirement
    assert response.status_code == 401


def test_mark_notification_read_unauthenticated(client):
    """Test marking notification as read without authentication"""
    response = client.put("/notifications/test_notification_123/read")
    # Should return 401 due to authentication requirement
    assert response.status_code == 401


def test_delete_notification_unauthenticated(client):
    """Test deleting notification without authentication"""
    response = client.delete("/notifications/test_notification_123")
    # Should return 401 due to authentication requirement
    assert response.status_code == 401