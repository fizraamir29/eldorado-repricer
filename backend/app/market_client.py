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


class OfferMissingError(MarketplaceAPIError):
    """Raised when the requested offer no longer exists on Eldorado."""
    pass

_GLOBAL_TOKEN_CACHE: Dict[str, Dict[str, Any]] = {}
_GLOBAL_TOKEN_LOCK = asyncio.Lock()


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

    async def get_access_token(self) -> str:
        """
        Obtains or returns an active Bearer access token.
        Caches the token in memory and automatically refreshes 60 seconds before expiration.
        """
        # If running legacy single API key mode without client_id
        if not self.client_id:
            return self.client_secret or ""
            
        cache_key = self.client_id

        now = time.time()
        cached = _GLOBAL_TOKEN_CACHE.get(cache_key)
        if cached and now < (cached["expires_at"] - 60):
            return cached["access_token"]

        async with _GLOBAL_TOKEN_LOCK:
            # Re-check inside lock
            now = time.time()
            cached = _GLOBAL_TOKEN_CACHE.get(cache_key)
            if cached and now < (cached["expires_at"] - 60):
                return cached["access_token"]

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

                    _GLOBAL_TOKEN_CACHE[cache_key] = {
                        "access_token": access_token,
                        "expires_at": time.time() + float(expires_in)
                    }
                    logger.info("Successfully acquired Eldorado Seller API Access Token for client %s (expires in %ss)", self.client_id[:8], expires_in)
                    return access_token

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
                    if self.client_id and self.client_id in _GLOBAL_TOKEN_CACHE:
                        del _GLOBAL_TOKEN_CACHE[self.client_id]
                    headers = await self._headers()

                resp.raise_for_status()
                if resp.status_code == 204 or not resp.content:
                    return {}
                return resp.json()

            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as exc:
                if isinstance(exc, httpx.HTTPStatusError):
                    last_error = f"HTTP {exc.response.status_code}: {exc.response.text}"
                else:
                    last_error = str(exc)
                wait = min(2 ** attempt, 30)
                logger.warning("Marketplace API call failed (attempt %s/%s): %s", attempt, self.max_retries, last_error)
                if attempt < self.max_retries:
                    await asyncio.sleep(wait)

        raise MarketplaceAPIError(f"Marketplace API call failed after {self.max_retries} attempts: {last_error}")

    async def get_competitor_offers(self, game_id: str, item_id: str) -> List[Dict[str, Any]]:
        """Fetch active competing seller offers for a given game/item."""
        
        # Check if it's a Currency Offer first
        try:
            my_curr = await self._request("GET", f"/api/v1/currency-management/me/offers/{item_id}")
            if my_curr and isinstance(my_curr, dict) and "offer" in my_curr:
                logger.info(f"Offer {item_id} is a Currency Offer!")

                offer_data = my_curr["offer"]
                game_id_val = offer_data.get("gameId")
                category_val = offer_data.get("category")
                
                if game_id_val and category_val:
                    groups_data = await self._request("GET", f"/api/v1/currency-management/offers/groups?gameId={game_id_val}&category={category_val}")
                    results = groups_data.get("results", [])
                    
                    my_attrs = offer_data.get("attributes", [])
                    my_attr_ids = {a.get("value", {}).get("id") for a in my_attrs if isinstance(a, dict) and a.get("value")}
                    
                    formatted_offers = []
                    for r in results:
                        o_data = r.get("offer", {})
                        u_data = r.get("user", {})
                        
                        their_attrs = o_data.get("attributes", [])
                        their_attr_ids = {a.get("value", {}).get("id") for a in their_attrs if isinstance(a, dict) and a.get("value")}
                        
                        # Exclude our own offer
                        if o_data.get("id") == item_id:
                            continue

                        if my_attr_ids and their_attr_ids and my_attr_ids != their_attr_ids:
                            continue
                            
                        price_data = o_data.get("pricePerUnitInUSD") or o_data.get("pricePerUnit")
                        amount = price_data.get("amount") if isinstance(price_data, dict) else None
                        
                        if amount is not None:
                            formatted_offers.append({"price": amount, "raw": r, "user": {"username": u_data.get("username")}})
                    logger.info(f"Currency offers found: {len(formatted_offers)}")
                    return formatted_offers
        except Exception as e:
            logger.warning(f"Failed during Currency Offer check for {item_id}: {repr(e)}")
            # Even if it failed, it might be a currency offer. We shouldn't blindly fall through 
            # if we know it's a currency offer, but if it 404s, it means it's not a currency offer.
            pass

        # Check if it's a Predefined Offer by looking at our active predefined offers
        try:
            my_predef_offers = await self._request("GET", "/api/predefinedOffers/user/me")
            if not isinstance(my_predef_offers, list):
                my_predef_offers = []
        except Exception:
            my_predef_offers = []
            
        is_predef = False
        real_item_id = None
        for offer in my_predef_offers:
            if offer.get("id") == item_id:
                is_predef = True
                item_obj = offer.get("item", {})
                real_item_id = item_obj.get("id")
                break
                
        if is_predef:
            if not real_item_id:
                raise OfferMissingError(f"Predefined offer {item_id} found but has no associated item ID.")
            try:
                data = await self._request("GET", f"/api/predefinedOffers/{real_item_id}/offers")
                results = data.get("results", [])
                
                formatted_offers = []
                for r in results:
                    offer_data = r.get("offer", {})
                    # Exclude our own offer
                    if offer_data.get("id") == real_item_id or offer_data.get("id") == item_id:
                        continue
                        
                    price_data = offer_data.get("pricePerUnit", {})
                    amount = price_data.get("amount")
                    if amount is not None:
                        formatted_offers.append({"price": amount, "raw": r})
                return formatted_offers
            except Exception as e:
                raise MarketplaceAPIError(f"Failed to fetch competitors for predefined item {real_item_id}: {e}")
                
        # If it's not predefined, it must be a Flexible Offer
        # We need the game UUID because Eldorado's flexibleOffers endpoint requires it.
        try:
            my_offers = await self._request("GET", "/api/flexibleOffers/user/me")
        except Exception as e:
            raise MarketplaceAPIError(f"Failed to fetch user flexible offers: {e}")
        if not isinstance(my_offers, list):
            my_offers = []
            
        real_game_id = None
        for my_offer in my_offers:
            if my_offer.get("id") == item_id:
                game_obj = my_offer.get("game")
                if isinstance(game_obj, dict):
                    real_game_id = game_obj.get("id")
                break
                
        if not real_game_id:
            # Cannot find the offer in our active flexible offers list. It might have been deleted or deactivated.
            raise OfferMissingError(f"Offer {item_id} is missing from active flexible offers on Eldorado.")

        params = {"gameId": real_game_id, "pageSize": 50}
        data = await self._request("GET", "/api/flexibleOffers", params=params)
        
        if isinstance(data, list):
            return [r for r in data if r.get("id") != item_id]
            
        results = data.get("results", [])
        return [r for r in results if r.get("id") != item_id]

    async def update_listing_price(self, listing_id: str, new_price: float) -> Dict[str, Any]:
        """Push a new price to our own listing via Eldorado Seller API."""
        payload = {
            "price": round(new_price, 2),
            "amount": round(new_price, 2),
            "currency": "USD"
        }
        
        # Check if Currency Offer FIRST
        try:
            my_curr = await self._request("GET", f"/api/v1/currency-management/me/offers/{listing_id}")
            if my_curr and isinstance(my_curr, dict) and "offer" in my_curr:
                c_payload = {"amount": round(new_price, 2)}
                return await self._request("PUT", f"/api/v1/currency-management/me/offers/{listing_id}/change-price", json=c_payload)
        except Exception:
            pass

        # Determine if it's predefined or flexible by checking our own active lists
        try:
            my_predef_offers = await self._request("GET", "/api/predefinedOffers/user/me")
            if not isinstance(my_predef_offers, list): my_predef_offers = []
        except Exception:
            my_predef_offers = []
            
        is_predef = False
        real_item_id = None
        for offer in my_predef_offers:
            if offer.get("id") == listing_id:
                is_predef = True
                real_item_id = offer.get("item", {}).get("id")
                break
                
        if is_predef:
            try:
                return await self._request("PUT", f"/api/predefinedOffers/user/me/{listing_id}/changePrice", json=payload)
            except Exception as e:
                raise MarketplaceAPIError(f"Failed to update predefined offer price: {e}")
                
        # If not predefined, assume flexible
        try:
            return await self._request("PUT", f"/api/flexibleOffers/user/me/{listing_id}/changePrice", json=payload)
        except Exception as e:
            raise MarketplaceAPIError(f"Failed to update flexible offer price: {e}")

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


