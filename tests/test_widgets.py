"""
Widget CRUD tests.
"""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Get authentication headers for a test user."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "widgetowner@example.com",
            "password": "password123",
        },
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "widgetowner@example.com",
            "password": "password123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_widget(client: AsyncClient, auth_headers: dict):
    """Test creating a widget."""
    response = await client.post(
        "/api/v1/widgets/",
        json={
            "title": "Test Widget",
            "description": "A test widget",
            "button_text": "Submit",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Widget"
    assert data["description"] == "A test widget"
    assert "id" in data
    assert "owner_id" in data


@pytest.mark.asyncio
async def test_list_widgets(client: AsyncClient, auth_headers: dict):
    """Test listing widgets."""
    # Create a widget first
    await client.post(
        "/api/v1/widgets/",
        json={"title": "Widget 1"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/widgets/",
        json={"title": "Widget 2"},
        headers=auth_headers,
    )

    # List widgets
    response = await client.get("/api/v1/widgets/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["widgets"]) == 2


@pytest.mark.asyncio
async def test_get_widget(client: AsyncClient, auth_headers: dict):
    """Test getting a specific widget."""
    # Create a widget
    create_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "Get Me Widget"},
        headers=auth_headers,
    )
    widget_id = create_response.json()["id"]

    # Get the widget
    response = await client.get(
        f"/api/v1/widgets/{widget_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Get Me Widget"


@pytest.mark.asyncio
async def test_update_widget(client: AsyncClient, auth_headers: dict):
    """Test updating a widget."""
    # Create a widget
    create_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "Original Title"},
        headers=auth_headers,
    )
    widget_id = create_response.json()["id"]

    # Update the widget
    response = await client.patch(
        f"/api/v1/widgets/{widget_id}",
        json={"title": "Updated Title"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_widget(client: AsyncClient, auth_headers: dict):
    """Test deleting a widget."""
    # Create a widget
    create_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "Delete Me Widget"},
        headers=auth_headers,
    )
    widget_id = create_response.json()["id"]

    # Delete the widget
    response = await client.delete(
        f"/api/v1/widgets/{widget_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(
        f"/api/v1/widgets/{widget_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_widget(client: AsyncClient, auth_headers: dict):
    """Test getting a widget that doesn't exist."""
    response = await client.get(
        "/api/v1/widgets/nonexistent-id",
        headers=auth_headers,
    )
    assert response.status_code == 404
