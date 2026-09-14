"""
Geo enrichment service with provider fallback chain.

Provider A: ip-api.com (free, no key required)
Provider B: ipapi.co (free, no key required)

Fallback: A fails → B fails → return None
"""
import httpx
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GeoData:
    """Geographical data from IP lookup."""
    country: Optional[str] = None
    city: Optional[str] = None
    ip: Optional[str] = None


class GeoProvider:
    """Base class for geo providers."""

    async def lookup(self, ip: str) -> Optional[GeoData]:
        raise NotImplementedError


class IPApiProvider(GeoProvider):
    """
    Provider A: ip-api.com
    Free tier: 45 requests/minute
    Endpoint: http://ip-api.com/json/{ip}
    """

    async def lookup(self, ip: str) -> Optional[GeoData]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"http://ip-api.com/json/{ip}",
                    params={"fields": "status,country,city,query"}
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "success":
                    return GeoData(
                        country=data.get("country"),
                        city=data.get("city"),
                        ip=data.get("query", ip)
                    )
                return None
        except Exception as e:
            logger.warning(f"ip-api.com failed for {ip}: {e}")
            return None


class IpapiCoProvider(GeoProvider):
    """
    Provider B: ipapi.co
    Free tier: 1,000 requests/day
    Endpoint: https://ipapi.co/{ip}/json/
    """

    async def lookup(self, ip: str) -> Optional[GeoData]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"https://ipapi.co/{ip}/json/")
                response.raise_for_status()
                data = response.json()

                if not data.get("error"):
                    return GeoData(
                        country=data.get("country_name"),
                        city=data.get("city"),
                        ip=data.get("ip", ip)
                    )
                return None
        except Exception as e:
            logger.warning(f"ipapi.co failed for {ip}: {e}")
            return None


class GeoEnrichmentService:
    """
    Geo enrichment service with fallback chain.

    Usage:
        service = GeoEnrichmentService()
        geo_data = await service.enrich("8.8.8.8")
    """

    def __init__(
        self,
        provider_a: Optional[GeoProvider] = None,
        provider_b: Optional[GeoProvider] = None,
    ):
        self.provider_a = provider_a or IPApiProvider()
        self.provider_b = provider_b or IpapiCoProvider()

    async def enrich(self, ip: str) -> Optional[GeoData]:
        """
        Attempt to enrich IP with geographical data.

        Fallback chain:
        1. Try Provider A (ip-api.com)
        2. If A fails, try Provider B (ipapi.co)
        3. If both fail, return None

        The submission must still be stored even if both providers fail.
        """
        if not ip or ip in ("127.0.0.1", "::1", "localhost"):
            # Skip geo lookup for localhost
            return None

        # Try Provider A
        result = await self.provider_a.lookup(ip)
        if result:
            logger.info(f"Geo lookup succeeded via ip-api.com for {ip}")
            return result

        # Provider A failed, try Provider B
        logger.info(f"ip-api.com failed for {ip}, trying ipapi.co")
        result = await self.provider_b.lookup(ip)
        if result:
            logger.info(f"Geo lookup succeeded via ipapi.co for {ip}")
            return result

        # Both providers failed
        logger.warning(f"Both geo providers failed for {ip}")
        return None


# Singleton instance for the application
geo_service = GeoEnrichmentService()
