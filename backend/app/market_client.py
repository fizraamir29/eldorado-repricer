"""
Marketplace API client for Eldorado.gg official Seller API.

This client implements Eldorado's official Client Credentials & Seller API Authentication flow:
1. POST /api/authentication/seller/token (exchange ClientId + ClientSecret for AccessToken)
2. Automatic token caching and auto-refresh (re-fetches when < 60s remaining on 900s token)
3. Authenticates seller endpoints with Authorization: Bearer <AccessToken>
4. Exponential backoff and safe rate-limiting on HTTP 429 to protect client seller accounts.
"""
import asyncio
import logging
import time
from typing import Optional, Dict, List, Any

# pyrefly: ignore [missing-import]
import httpx

from app.config import settings

logger = logging.getLogger("market_client")


class MarketplaceAPIError(Exception):
    pass


class EldoradoClient:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret or api_key
        self.base_url = settings.marketplace_base_url.rstrip("/")
        self.timeout = settings.marketplace_request_timeout_seconds
        self.max_retries = settings.marketplace_max_retries

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get_access_token(self) -> str:
        """
        Obtains or returns an active Bearer access token.
        Caches the token in memory and automatically refreshes 60 seconds before expiration.
        """
        # If running legacy single API key mode without client_id
        if not self.client_id:
            return self.client_secret or ""

        now = time.time()
        if self._access_token and now < (self._token_expires_at - 60):
            return self._access_token

        async with self._lock:
            # Re-check inside lock
            now = time.time()
            if self._access_token and now < (self._token_expires_at - 60):
                return self._access_token

            token_url = f"{self.base_url}/api/authentication/seller/token"
            payload = {
                "clientId": self.client_id,
                "clientSecret": self.client_secret,
            }

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(token_url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()

                    access_token = data.get("AccessToken") or data.get("access_token") or data.get("accessToken")
                    expires_in = data.get("ExpiresIn") or data.get("expires_in") or data.get("expiresIn", 900)

                    if not access_token:
                        raise MarketplaceAPIError("No AccessToken returned from Eldorado seller token endpoint")

                    self._access_token = access_token
                    self._token_expires_at = time.time() + float(expires_in)
                    logger.info("Successfully acquired Eldorado Seller API Access Token (expires in %ss)", expires_in)
                    return self._access_token

            except Exception as exc:
                logger.error("Failed to authenticate seller token with Eldorado: %s", exc)
                raise MarketplaceAPIError(f"Eldorado authentication failed: {exc}")

    async def _headers(self) -> Dict[str, str]:
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_error: Optional[Exception] = None

        headers = await self._headers()
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.request(method, url, headers=headers, **kwargs)

                if resp.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning("Rate limited by Eldorado API (429), waiting %ss before retry...", wait)
                    await asyncio.sleep(wait)
                    continue

                if resp.status_code == 401:
                    # Token might have been invalidated, force refresh
                    self._access_token = None
                    self._token_expires_at = 0.0
                    headers = await self._headers()

                resp.raise_for_status()
                if resp.status_code == 204 or not resp.content:
                    return {}
                return resp.json()

            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_error = exc
                wait = min(2 ** attempt, 30)
                logger.warning("Marketplace API call failed (attempt %s/%s): %s", attempt, self.max_retries, exc)
                await asyncio.sleep(wait)

        raise MarketplaceAPIError(f"Marketplace API call failed after {self.max_retries} attempts: {last_error}")

    async def get_competitor_offers(self, game_id: str, item_id: str) -> List[Dict[str, Any]]:
        """Fetch active competing seller offers for a given game/item."""
        # Found in Swagger: FlexibleOfferPublic
        # We pass gameId to filter
        params = {"gameId": game_id, "pageSize": 50}
        # In case the frontend passes the direct ID to search, we can use it.
        if item_id and item_id != "default":
            # If item_id looks like a GUID, we could query it directly, but searching the market is safer.
            pass
        
        data = await self._request("GET", "/api/flexibleOffers", params=params)
        if isinstance(data, list):
            return data
        return data.get("results", [])

    async def update_listing_price(self, listing_id: str, new_price: float) -> Dict[str, Any]:
        """Push a new price to our own listing via Eldorado Seller API."""
        # Found in Swagger: FlexibleOfferUserPrivate
        payload = {
            "price": round(new_price, 2),
            "amount": round(new_price, 2),
            "currency": "USD"
        }
        return await self._request("PUT", f"/api/flexibleOffersUser/me/{listing_id}/changePrice", json=payload)

    async def deliver_order(self, order_id: str, delivery_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Deliver an order as a seller via official Eldorado Seller API."""
        payload = delivery_data or {}
        return await self._request("PUT", f"/api/orders/me/{order_id}/deliver", json=payload)

    async def cancel_order(self, order_id: str, reason_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Cancel an order as a seller via official Eldorado Seller API."""
        payload = reason_data or {}
        return await self._request("PUT", f"/api/orders/me/{order_id}/cancel", json=payload)

    async def send_customer_greeting(self, order_id_or_chat_id: str, message: str) -> Dict[str, Any]:
        """Send auto-greeting message to a buyer."""
        payload = {"message": message}
        return await self._request("POST", f"/api/orders/me/{order_id_or_chat_id}/messages", json=payload)


