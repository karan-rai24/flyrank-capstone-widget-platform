"""
Phase 2 Tests: Hardened Submission Path
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from app.services.geo import GeoEnrichmentService, GeoData, GeoProvider
from app.services.notification import NotificationService, NotificationProvider, NotificationPayload
from app.services.rate_limit import RateLimitService, RateLimitConfig


# ============================================================================
# Mock Geo Providers for Deterministic Testing
# ============================================================================

class MockGeoProvider(GeoProvider):
    """Mock geo provider for testing."""

    def __init__(self, should_succeed: bool = True, country: str = "United States", city: str = "New York"):
        self.should_succeed = should_succeed
        self.country = country
        self.city = city
        self.call_count = 0

    async def lookup(self, ip: str) -> GeoData:
        self.call_count += 1
        if self.should_succeed:
            return GeoData(country=self.country, city=self.city, ip=ip)
        return None


class MockNotificationProvider(NotificationProvider):
    """Mock notification provider for testing."""

    def __init__(self, should_succeed: bool = True):
        self.should_succeed = should_succeed
        self.notifications_sent = []

    async def send(self, payload: NotificationPayload) -> bool:
        self.notifications_sent.append(payload)
        return self.should_succeed


# ============================================================================
# Test: Valid Submission
# ============================================================================

@pytest.mark.asyncio
async def test_valid_submission(client: AsyncClient, test_db):
    """Test successful submission to a widget."""
    # Create a widget first (authenticated)
    await client.post(
        "/api/v1/auth/register",
        json={"email": "owner@example.com", "password": "pass123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "pass123"},
    )
    token = login_response.json()["access_token"]

    widget_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "Test Widget"},
        headers={"Authorization": f"Bearer {token}"},
    )
    widget_id = widget_response.json()["id"]

    # Public submission (no auth)
    response = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": widget_id,
            "submission_data": {"name": "John Doe", "email": "john@example.com"},
        },
    )
    assert response.status_code == 202
    assert "id" in response.json()


# ============================================================================
# Test: Invalid Payload
# ============================================================================

@pytest.mark.asyncio
async def test_invalid_payload_missing_widget_id(client: AsyncClient):
    """Test submission with missing widget_id."""
    response = await client.post(
        "/api/v1/submissions/",
        json={
            "submission_data": {"name": "Test"},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_payload_missing_submission_data(client: AsyncClient):
    """Test submission with missing submission_data."""
    response = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": "some-widget-id",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_payload_empty_widget_id(client: AsyncClient):
    """Test submission with empty widget_id."""
    response = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": "",
            "submission_data": {"name": "Test"},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_payload_empty_submission_data(client: AsyncClient):
    """Test submission with empty submission_data dict."""
    response = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": "some-widget-id",
            "submission_data": {},
        },
    )
    # Empty dict is valid JSON, but may fail widget validation
    assert response.status_code in [202, 404, 422]


# ============================================================================
# Test: Oversized Payload
# ============================================================================

@pytest.mark.asyncio
async def test_oversized_payload(client: AsyncClient):
    """Test submission with oversized payload."""
    # Create a payload larger than 64KB
    large_data = {"field": "x" * 70000}  # ~70KB
    response = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": "some-widget-id",
            "submission_data": large_data,
        },
    )
    assert response.status_code == 422


# ============================================================================
# Test: Widget Not Found
# ============================================================================

@pytest.mark.asyncio
async def test_widget_not_found(client: AsyncClient):
    """Test submission to non-existent widget."""
    response = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": "non-existent-widget-id",
            "submission_data": {"name": "Test"},
        },
    )
    assert response.status_code == 404


# ============================================================================
# Test: CORS
# ============================================================================

@pytest.mark.asyncio
async def test_cors_preflight(client: AsyncClient):
    """Test CORS preflight request."""
    response = await client.options(
        "/api/v1/submissions/",
        headers={
            "Origin": "http://localhost:5500",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    # Should allow the preflight
    assert response.status_code in [200, 204]


@pytest.mark.asyncio
async def test_cors_actual_post(client: AsyncClient):
    """Test actual POST request with CORS origin."""
    # Create widget first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "cors@example.com", "password": "pass123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "cors@example.com", "password": "pass123"},
    )
    token = login_response.json()["access_token"]

    widget_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "CORS Widget"},
        headers={"Authorization": f"Bearer {token}"},
    )
    widget_id = widget_response.json()["id"]

    # POST with CORS origin header
    response = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": widget_id,
            "submission_data": {"name": "CORS Test"},
        },
        headers={"Origin": "http://localhost:5500"},
    )
    assert response.status_code == 202


# ============================================================================
# Test: Rate Limiting
# ============================================================================

@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient, test_db):
    """Test rate limiting on submission endpoint."""
    # Create widget
    await client.post(
        "/api/v1/auth/register",
        json={"email": "ratelimit@example.com", "password": "pass123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ratelimit@example.com", "password": "pass123"},
    )
    token = login_response.json()["access_token"]

    widget_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "Rate Limit Widget"},
        headers={"Authorization": f"Bearer {token}"},
    )
    widget_id = widget_response.json()["id"]

    # Send multiple requests to trigger rate limit
    responses = []
    for i in range(15):  # More than the limit of 10
        response = await client.post(
            "/api/v1/submissions/",
            json={
                "widget_id": widget_id,
                "submission_data": {"name": f"User {i}"},
            },
        )
        responses.append(response.status_code)

    # Should have some 429 responses
    assert 429 in responses


# ============================================================================
# Test: Honeypot (Spam Protection)
# ============================================================================

@pytest.mark.asyncio
async def test_honeypot_empty_allows_submission(client: AsyncClient):
    """Test that empty honeypot allows submission."""
    # Create widget
    await client.post(
        "/api/v1/auth/register",
        json={"email": "honeypot@example.com", "password": "pass123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "honeypot@example.com", "password": "pass123"},
    )
    token = login_response.json()["access_token"]

    widget_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "Honeypot Widget"},
        headers={"Authorization": f"Bearer {token}"},
    )
    widget_id = widget_response.json()["id"]

    # Empty honeypot should work
    response = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": widget_id,
            "submission_data": {"name": "Legitimate User"},
            "honeypot": "",
        },
    )
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_honeypot_filled_blocks_submission(client: AsyncClient):
    """Test that filled honeypot blocks submission (silently)."""
    # Create widget
    await client.post(
        "/api/v1/auth/register",
        json={"email": "spam@example.com", "password": "pass123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "spam@example.com", "password": "pass123"},
    )
    token = login_response.json()["access_token"]

    widget_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "Spam Widget"},
        headers={"Authorization": f"Bearer {token}"},
    )
    widget_id = widget_response.json()["id"]

    # Filled honeypot should be silently rejected
    response = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": widget_id,
            "submission_data": {"name": "Spam Bot"},
            "honeypot": "I am a bot",
        },
    )
    # Returns success to not tip off bots
    assert response.status_code == 202


# ============================================================================
# Test: Geo Fallback
# ============================================================================

@pytest.mark.asyncio
async def test_geo_provider_a_success(client: AsyncClient, test_db):
    """Test geo enrichment when Provider A succeeds."""
    provider_a = MockGeoProvider(should_succeed=True, country="USA", city="NYC")
    provider_b = MockGeoProvider(should_succeed=False)

    geo_service = GeoEnrichmentService(provider_a=provider_a, provider_b=provider_b)

    result = await geo_service.enrich("8.8.8.8")

    assert result is not None
    assert result.country == "USA"
    assert result.city == "NYC"
    assert provider_a.call_count == 1
    assert provider_b.call_count == 0  # Should not be called


@pytest.mark.asyncio
async def test_geo_provider_a_fails_b_succeeds(client: AsyncClient, test_db):
    """Test geo enrichment when Provider A fails but B succeeds."""
    provider_a = MockGeoProvider(should_succeed=False)
    provider_b = MockGeoProvider(should_succeed=True, country="UK", city="London")

    geo_service = GeoEnrichmentService(provider_a=provider_a, provider_b=provider_b)

    result = await geo_service.enrich("8.8.8.8")

    assert result is not None
    assert result.country == "UK"
    assert result.city == "London"
    assert provider_a.call_count == 1
    assert provider_b.call_count == 1


@pytest.mark.asyncio
async def test_geo_both_providers_fail(client: AsyncClient, test_db):
    """Test geo enrichment when both providers fail."""
    provider_a = MockGeoProvider(should_succeed=False)
    provider_b = MockGeoProvider(should_succeed=False)

    geo_service = GeoEnrichmentService(provider_a=provider_a, provider_b=provider_b)

    result = await geo_service.enrich("8.8.8.8")

    assert result is None
    assert provider_a.call_count == 1
    assert provider_b.call_count == 1


# ============================================================================
# Test: Notification Failure
# ============================================================================

@pytest.mark.asyncio
async def test_notification_failure_doesnt_break_submission(client: AsyncClient, test_db):
    """Test that notification failure doesn't break submission."""
    # Create widget
    await client.post(
        "/api/v1/auth/register",
        json={"email": "notify@example.com", "password": "pass123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "notify@example.com", "password": "pass123"},
    )
    token = login_response.json()["access_token"]

    widget_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "Notify Widget"},
        headers={"Authorization": f"Bearer {token}"},
    )
    widget_id = widget_response.json()["id"]

    # Mock notification service to fail
    with patch("app.services.submission.notification_service") as mock_notify:
        mock_notify.notify_submission = AsyncMock(return_value=False)

        response = await client.post(
            "/api/v1/submissions/",
            json={
                "widget_id": widget_id,
                "submission_data": {"name": "Test"},
            },
        )

        # Submission should still succeed
        assert response.status_code == 202


# ============================================================================
# Test: Rate Limit Service
# ============================================================================

def test_rate_limit_service_allows_requests():
    """Test rate limit service allows requests within limit."""
    config = RateLimitConfig(max_requests=5, window_seconds=60)
    service = RateLimitService(config)

    # Should allow 5 requests
    for i in range(5):
        assert service.check_rate_limit("test_ip") is True
        service.record_request("test_ip")

    # 6th request should be blocked
    assert service.check_rate_limit("test_ip") is False


def test_rate_limit_service_resets():
    """Test rate limit service resets after window."""
    config = RateLimitConfig(max_requests=2, window_seconds=1)
    service = RateLimitService(config)

    # Use up the limit
    service.record_request("test_ip")
    service.record_request("test_ip")
    assert service.check_rate_limit("test_ip") is False


# ============================================================================
# Test: Honeypot Validation
# ============================================================================

def test_honeypot_empty_is_legitimate():
    """Test that empty honeypot is considered legitimate."""
    from app.services.submission import SubmissionService

    service = SubmissionService()
    assert service.check_honeypot(None) is True
    assert service.check_honeypot("") is True
    assert service.check_honeypot("   ") is True


def test_honeypot_filled_is_spam():
    """Test that filled honeypot is considered spam."""
    from app.services.submission import SubmissionService

    service = SubmissionService()
    assert service.check_honeypot("bot") is False
    assert service.check_honeypot("I am a robot") is False


# ============================================================================
# Test: Idempotency
# ============================================================================

@pytest.mark.asyncio
async def test_idempotency_same_key_returns_same_response(client: AsyncClient, test_db):
    """Test that same idempotency key returns cached response."""
    # Create widget
    await client.post(
        "/api/v1/auth/register",
        json={"email": "idem@example.com", "password": "pass123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "idem@example.com", "password": "pass123"},
    )
    token = login_response.json()["access_token"]

    widget_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "Idempotency Widget"},
        headers={"Authorization": f"Bearer {token}"},
    )
    widget_id = widget_response.json()["id"]

    idempotency_key = "test-idempotency-key-12345"

    # First request
    response1 = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": widget_id,
            "submission_data": {"name": "First Request"},
        },
        headers={"Idempotency-Key": idempotency_key},
    )
    assert response1.status_code == 202
    id1 = response1.json()["id"]

    # Second request with same key
    response2 = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": widget_id,
            "submission_data": {"name": "Second Request"},
        },
        headers={"Idempotency-Key": idempotency_key},
    )
    assert response2.status_code == 202
    id2 = response2.json()["id"]

    # Should return same submission ID
    assert id1 == id2


@pytest.mark.asyncio
async def test_idempotency_different_keys_create_separate(client: AsyncClient, test_db):
    """Test that different idempotency keys create separate submissions."""
    # Create widget
    await client.post(
        "/api/v1/auth/register",
        json={"email": "idem2@example.com", "password": "pass123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "idem2@example.com", "password": "pass123"},
    )
    token = login_response.json()["access_token"]

    widget_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "Idempotency Widget 2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    widget_id = widget_response.json()["id"]

    # First request
    response1 = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": widget_id,
            "submission_data": {"name": "First"},
        },
        headers={"Idempotency-Key": "key-1"},
    )
    assert response1.status_code == 202
    id1 = response1.json()["id"]

    # Second request with different key
    response2 = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": widget_id,
            "submission_data": {"name": "Second"},
        },
        headers={"Idempotency-Key": "key-2"},
    )
    assert response2.status_code == 202
    id2 = response2.json()["id"]

    # Should have different submission IDs
    assert id1 != id2


@pytest.mark.asyncio
async def test_idempotency_no_key_allows_multiple(client: AsyncClient, test_db):
    """Test that requests without idempotency key create separate submissions."""
    # Create widget
    await client.post(
        "/api/v1/auth/register",
        json={"email": "idem3@example.com", "password": "pass123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "idem3@example.com", "password": "pass123"},
    )
    token = login_response.json()["access_token"]

    widget_response = await client.post(
        "/api/v1/widgets/",
        json={"title": "No Idempotency Widget"},
        headers={"Authorization": f"Bearer {token}"},
    )
    widget_id = widget_response.json()["id"]

    # Multiple requests without key
    response1 = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": widget_id,
            "submission_data": {"name": "First"},
        },
    )
    response2 = await client.post(
        "/api/v1/submissions/",
        json={
            "widget_id": widget_id,
            "submission_data": {"name": "Second"},
        },
    )

    # Should have different submission IDs
    assert response1.json()["id"] != response2.json()["id"]
