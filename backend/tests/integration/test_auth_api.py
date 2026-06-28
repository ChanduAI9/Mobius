import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_register_and_login(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "integration@mobius.dev",
            "password": "integrationtest123",
            "display_name": "Integration Test",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "integration@mobius.dev"

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "integration@mobius.dev", "password": "integrationtest123"},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 403 or response.status_code == 401
