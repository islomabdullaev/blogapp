"""
Integration tests for authentication endpoints
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration"""
    user_data = {
        "email": "test@example.com",
        "full_name": "test user",
        "username": "testuser",
        "password": "testpass123",
    }

    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert "verification_token" in data
    assert "user_id" in data
    assert data["message"] == "User registered successfully. Please verify your email."


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Test registration with duplicate username"""
    user_data = {
        "email": "test@example.com",
        "full_name": "test user",
        "username": "testuser",
        "password": "testpass123",
    }

    # Register first user
    await client.post("/api/auth/register", json=user_data)

    # Try to register with same username
    user_data["email"] = "test2@example.com"
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Username already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email"""
    user_data = {
        "email": "test@example.com",
        "full_name": "test user",
        "username": "testuser",
        "password": "testpass123",
    }

    # Register first user
    await client.post("/api/auth/register", json=user_data)

    # Try to register with same email
    user_data["username"] = "testuser2"
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Email already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login"""
    user_data = {
        "email": "test@example.com",
        "full_name": "test user",
        "username": "testuser",
        "password": "testpass123",
    }

    # Register user
    register_response = await client.post("/api/auth/register", json=user_data)
    assert register_response.status_code == 201

    # Login
    login_data = {"email": "test@example.com", "password": "testpass123"}
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials"""
    login_data = {"email": "nonexistent@example.com", "password": "wrongpass"}
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_email(client: AsyncClient):
    """Test email verification"""
    user_data = {
        "email": "test@example.com",
        "full_name": "test user",
        "username": "testuser",
        "password": "testpass123",
    }

    # Register user
    register_response = await client.post("/api/auth/register", json=user_data)
    assert register_response.status_code == 201
    data = register_response.json()
    verification_token = data["verification_token"]

    # Verify email
    response = await client.post(f"/api/auth/verify-email/{verification_token}")
    assert response.status_code == 200
    assert "Email verified successfully" in response.json()["message"]


@pytest.mark.asyncio
async def test_verify_email_invalid_token(client: AsyncClient):
    """Test email verification with invalid token"""
    response = await client.post("/api/auth/verify-email/invalid_token")
    assert response.status_code == 404
    assert "Invalid verification token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_authenticated(client: AsyncClient):
    """Test getting current user when authenticated"""
    user_data = {
        "email": "test@example.com",
        "full_name": "test user",
        "username": "testuser",
        "password": "testpass123",
    }

    # Register and login
    await client.post("/api/auth/register", json=user_data)
    login_response = await client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Get current user
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/user/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_current_user_unauthenticated(client: AsyncClient):
    """Test getting current user without authentication"""
    response = await client.get("/api/user/me")
    assert response.status_code == 403
