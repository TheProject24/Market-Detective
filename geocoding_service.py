"""
Multi-provider geocoding service with automatic fallback.
Supports LocationIQ, OpenCage, Geoapify, Positionstack, and Nominatim.
"""
import os
import time
import logging
import requests
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

logger = logging.getLogger("MarketDetective.Geocoder")


class GeocodingService:
    """
    Multi-provider geocoding service with automatic fallback.
    Tries providers in order until one succeeds or all fail.
    """

    def __init__(self):
        # Load API keys from environment
        self.locationiq_key = os.getenv("LOCATIONIQ_API_KEY")
        self.opencage_key = os.getenv("OPENCAGE_API_KEY")
        self.geoapify_key = os.getenv("GEOAPIFY_API_KEY")
        self.positionstack_key = os.getenv("POSITIONSTACK_API_KEY")

        # Initialize Nominatim as last resort
        self.nominatim = Nominatim(user_agent="market_detective_scraper")

        # Track which providers are available
        self.providers = []
        if self.locationiq_key:
            self.providers.append("locationiq")
        if self.opencage_key:
            self.providers.append("opencage")
        if self.geoapify_key:
            self.providers.append("geoapify")
        if self.positionstack_key:
            self.providers.append("positionstack")
        self.providers.append("nominatim")  # Always available as fallback

        logger.info(f"Initialized geocoding service with providers: {', '.join(self.providers)}")

    def geocode(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocode an address using available providers with automatic fallback.

        Args:
            address: The address to geocode

        Returns:
            Tuple of (latitude, longitude) or (None, None) if all providers fail
        """
        if not address or address.strip() == "":
            logger.warning("Empty address provided for geocoding")
            return None, None

        # Enhance address with country for better results
        query = f"{address}, Nigeria"

        # Try each provider in order
        for provider in self.providers:
            try:
                lat, lon = self._geocode_with_provider(provider, query)
                if lat is not None and lon is not None:
                    logger.info(f"Successfully geocoded '{address}' using {provider}")
                    return lat, lon
            except Exception as e:
                logger.warning(f"Provider {provider} failed for '{address}': {e}")
                continue

        logger.error(f"All geocoding providers failed for address: {address}")
        return None, None

    def _geocode_with_provider(self, provider: str, query: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocode using a specific provider.

        Args:
            provider: Name of the provider to use
            query: The query string to geocode

        Returns:
            Tuple of (latitude, longitude) or (None, None) if failed
        """
        if provider == "locationiq":
            return self._geocode_locationiq(query)
        elif provider == "opencage":
            return self._geocode_opencage(query)
        elif provider == "geoapify":
            return self._geocode_geoapify(query)
        elif provider == "positionstack":
            return self._geocode_positionstack(query)
        elif provider == "nominatim":
            return self._geocode_nominatim(query)
        else:
            logger.error(f"Unknown provider: {provider}")
            return None, None

    def _geocode_locationiq(self, query: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode using LocationIQ API."""
        url = "https://us1.locationiq.com/v1/search"
        params = {
            "key": self.locationiq_key,
            "q": query,
            "format": "json",
            "limit": 1,
            "countrycodes": "ng"
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 429:
            raise Exception("Rate limit exceeded")

        response.raise_for_status()
        data = response.json()

        if data and len(data) > 0:
            return float(data[0]["lat"]), float(data[0]["lon"])

        return None, None

    def _geocode_opencage(self, query: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode using OpenCage API."""
        url = "https://api.opencagedata.com/geocode/v1/json"
        params = {
            "key": self.opencage_key,
            "q": query,
            "limit": 1,
            "no_annotations": 1,
            "countrycode": "ng"
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 429:
            raise Exception("Rate limit exceeded")

        response.raise_for_status()
        data = response.json()

        if data.get("results") and len(data["results"]) > 0:
            geometry = data["results"][0]["geometry"]
            return float(geometry["lat"]), float(geometry["lng"])

        return None, None

    def _geocode_geoapify(self, query: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode using Geoapify API."""
        url = "https://api.geoapify.com/v1/geocode/search"
        params = {
            "apiKey": self.geoapify_key,
            "text": query,
            "limit": 1,
            "filter": "countrycode:ng"
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 429:
            raise Exception("Rate limit exceeded")

        response.raise_for_status()
        data = response.json()

        if data.get("features") and len(data["features"]) > 0:
            coordinates = data["features"][0]["geometry"]["coordinates"]
            # Geoapify returns [lon, lat]
            return float(coordinates[1]), float(coordinates[0])

        return None, None

    def _geocode_positionstack(self, query: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode using Positionstack API."""
        url = "http://api.positionstack.com/v1/forward"
        params = {
            "access_key": self.positionstack_key,
            "query": query,
            "limit": 1,
            "country": "ng"
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 429:
            raise Exception("Rate limit exceeded")

        response.raise_for_status()
        data = response.json()

        if data.get("data") and len(data["data"]) > 0:
            result = data["data"][0]
            return float(result["latitude"]), float(result["longitude"])

        return None, None

    def _geocode_nominatim(self, query: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode using Nominatim (OpenStreetMap) - last resort due to rate limits."""
        try:
            # Nominatim requires 1 second between requests
            time.sleep(1)
            location = self.nominatim.geocode(query, timeout=10, country_codes="ng")
            if location:
                return location.latitude, location.longitude
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            raise Exception(f"Nominatim error: {e}")

        return None, None
