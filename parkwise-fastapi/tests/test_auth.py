import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security import verify_password, get_password_hash, create_access_token
from app.schemas import UserCreate
from sqlalchemy import text
import json


def test_register_user(client):
    """Test user registration"""
    user_data = {
        "email": "newuser@example.com",
        "password": "SecurePassword123!",
        "first_name": "New",
        "last_name": "User"
    }
    
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "refresh_token" in data


def test_register_user_invalid_password(client):
    """Test registration with invalid password"""
    user_data = {
        "email": "invalid@example.com",
        "password": "weak",  # Too short
        "first_name": "Invalid",
        "last_name": "User"
    }
    
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422  # Validation error


def test_login_user(client):
    """Test user login with valid credentials"""
    # First register a user
    register_data = {
        "email": "loginuser@example.com",
        "password": "SecurePassword123!",
        "first_name": "Login",
        "last_name": "User"
    }
    
    client.post("/auth/register", json=register_data)
    
    # Then try to login
    login_data = {
        "email": "loginuser@example.com",
        "password": "SecurePassword123!"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_user_invalid_credentials(client):
    """Test login with invalid credentials"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401


def test_password_hashing():
    """Test password hashing and verification"""
    password = "TestPassword123!"
    hashed = get_password_hash(password)
    
    assert password != hashed  # Password and hash should be different
    assert verify_password(password, hashed)  # Hash should verify successfully
    assert not verify_password("WrongPassword", hashed)  # Wrong password should fail


def test_token_creation():
    """Test JWT token creation"""
    data = {"sub": "test_user_id"}
    token = create_access_token(data)
    
    assert isinstance(token, str)
    assert len(token) > 0