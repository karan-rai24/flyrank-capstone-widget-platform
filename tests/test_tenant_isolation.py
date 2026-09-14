"""
Tenant isolation tests.

These tests verify that User A cannot access User B's widgets.
"""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def user_a_headers(client: AsyncClient) -> dict:
    """Get authentication headers for User A."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "usera@example.com",
            "password": "password123",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "usera@example.com",
            "password": "password123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def user_b_headers(client: AsyncClient) -> dict:
    """Get authentication headers for User B."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "userb@example.com",
            "password": "password456",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "userb@example.com",
            "password": "password456",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_user_a_cannot_read_user_b_widget(
    client: AsyncClient, user_a_headers: dict, user_b_headers: dict
):
    """User A cannot read User B's widget."""
    # User B creates a widget
    create_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "User B's Widget"},
        headers=user_b_headers,
    )
    widget_id = create_response.json()["id"]

    # User A tries to get User B's widget
    response = await client.get(
        f"/api/v1/widgets/{widget_id}",
        headers=user_a_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_user_a_cannot_update_user_b_widget(
    client: AsyncClient, user_a_headers: dict, user_b_headers: dict
):
    """User A cannot update User B's widget."""
    # User B creates a widget
    create_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "User B's Widget"},
        headers=user_b_headers,
    )
    widget_id = create_response.json()["id"]

    # User A tries to update User B's widget
    response = await client.patch(
        f"/api/v1/widgets/{widget_id}",
        json={"title": "Hacked Title"},
        headers=user_a_headers,
    )
    assert response.status_code == 404

    # Verify widget unchanged
    get_response = await client.get(
        f"/api/v1/widgets/{widget_id}",
        headers=user_b_headers,
    )
    assert get_response.json()["title"] == "User B's Widget"


@pytest.mark.asyncio
async def test_user_a_cannot_delete_user_b_widget(
    client: AsyncClient, user_a_headers: dict, user_b_headers: dict
):
    """User A cannot delete User B's widget."""
    # User B creates a widget
    create_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "User B's Widget"},
        headers=user_b_headers,
    )
    widget_id = create_response.json()["id"]

    # User A tries to delete User B's widget
    response = await client.delete(
        f"/api/v1/widgets/{widget_id}",
        headers=user_a_headers,
    )
    assert response.status_code == 404

    # Verify widget still exists
    get_response = await client.get(
        f"/api/v1/widgets/{widget_id}",
        headers=user_b_headers,
    )
    assert get_response.status_code == 200


@pytest.mark.asyncio
async def test_user_a_list_does_not_include_user_b_widgets(
    client: AsyncClient, user_a_headers: dict, user_b_headers: dict
):
    """User A's widget list does not include User B's widgets."""
    # User A creates a widget
    await client.post(
        "/api/v1/widgets/",
        json={"title": "User A's Widget"},
        headers=user_a_headers,
    )

    # User B creates a widget
    await client.post(
        "/api/v1/widgets/",
        json={"title": "User B's Widget"},
        headers=user_b_headers,
    )

    # User A lists widgets
    response = await client.get("/api/v1/widgets/", headers=user_a_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["widgets"][0]["title"] == "User A's Widget"
