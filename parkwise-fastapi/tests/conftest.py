import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import get_session
from app.core import settings
from app.models import metadata
from app.schemas import UserCreate
from app.security import get_password_hash
import asyncio
import uuid

# Use a test database
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/parkwise_test"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

async def override_get_session():
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
def client():
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="module")
async def create_test_user():
    """Create a test user for authentication tests"""
    user_data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    return user_data

@pytest.fixture(scope="module")
async def authenticated_client(client, create_test_user):
    """Get an authenticated client"""
    # Register user
    response = client.post("/auth/register", json=create_test_user)
    assert response.status_code == 200
    
    # Login to get token
    login_data = {
        "email": create_test_user["email"],
        "password": create_test_user["password"]
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    return client