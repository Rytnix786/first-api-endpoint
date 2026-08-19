# services/geo_service.py — 2-Tier Geo-Enrichment Fallback Chain

import logging
import httpx
from typing import Tuple, Optional

logger = logging.getLogger("GeoService")


class GeoService:
    def __init__(self, timeout_seconds: float = 3.0):
        self.timeout = timeout_seconds
        self.provider_a_enabled = True
        self.provider_b_enabled = True

    def enrich_ip(self, ip_address: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Enriches an IP address using a 2-tier fallback chain.
        Returns: (country: str, city: str, provider: str)
        Degrades gracefully to (None, None, None) if all providers fail.
        """
        # Handle local / private testing IPs
        if not ip_address or ip_address in ("127.0.0.1", "::1", "localhost", "testclient"):
            return "Local Dev", "Localhost", "local"

        # Tier 1: Try Provider A (ip-api.com)
        if self.provider_a_enabled:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(f"http://ip-api.com/json/{ip_address}")
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("status") == "success":
                            country = data.get("country", "Unknown")
                            city = data.get("city", "Unknown")
                            logger.info(f"Geo enrichment success via Provider A (ip-api.com): {city}, {country}")
                            return country, city, "ip-api.com"
            except Exception as e:
                logger.warning(f"Geo Provider A (ip-api.com) failed: {e}. Initiating Provider B fallback.")

        # Tier 2: Try Provider B (ipapi.co)
        if self.provider_b_enabled:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(f"https://ipapi.co/{ip_address}/json/")
                    if resp.status_code == 200:
                        data = resp.json()
                        country = data.get("country_name") or data.get("country") or "Unknown"
                        city = data.get("city", "Unknown")
                        logger.info(f"Geo enrichment success via Provider B (ipapi.co): {city}, {country}")
                        return country, city, "ipapi.co"
            except Exception as e:
                logger.warning(f"Geo Provider B (ipapi.co) failed: {e}. Gracefully degrading to null geo.")

        # Tier 3: Graceful Degradation (Degrade, Never Fail)
        logger.warning("All geo providers unavailable or disabled. Proceeding without geo data.")
        return None, None, None
