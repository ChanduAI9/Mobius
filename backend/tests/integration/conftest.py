import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client):
    email = "test@mobius.dev"
    password = "testpassword123"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    if reg.status_code == 201:
        token = reg.json()["access_token"]
    else:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
