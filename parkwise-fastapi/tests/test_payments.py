import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import PaymentCreate
import json


def test_create_payment_unauthenticated(client):
    """Test creating a payment without authentication"""
    payment_data = {
        "booking_id": "test_booking_123",
        "amount": 15.50
    }
    
    response = client.post("/payments/", json=payment_data)
    # Should return 401 due to authentication requirement
    assert response.status_code == 401


def test_create_payment_invalid_amount(client):
    """Test creating a payment with invalid amount"""
    payment_data = {
        "booking_id": "test_booking_123",
        "amount": -10.00  # Negative amount
    }
    
    response = client.post("/payments/", json=payment_data)
    # Should return validation error
    assert response.status_code == 422


def test_create_payment_zero_amount(client):
    """Test creating a payment with zero amount"""
    payment_data = {
        "booking_id": "test_booking_123",
        "amount": 0.00  # Zero amount
    }
    
    response = client.post("/payments/", json=payment_data)
    # Should return validation error
    assert response.status_code == 422


def test_create_payment_valid_data(client):
    """Test creating a payment with valid data"""
    payment_data = {
        "booking_id": "valid_booking_456",
        "amount": 25.75
    }
    
    response = client.post("/payments/", json=payment_data)
    # Should return 401 due to authentication or 404 for booking not found
    assert response.status_code in [401, 404]


def test_get_payments_unauthenticated(client):
    """Test getting payments without authentication"""
    response = client.get("/payments/")
    # Should return 401 due to authentication requirement
    assert response.status_code == 401


def test_get_payment_details_unauthenticated(client):
    """Test getting specific payment details without authentication"""
    response = client.get("/payments/test_payment_123")
    # Should return 401 due to authentication requirement
    assert response.status_code == 401