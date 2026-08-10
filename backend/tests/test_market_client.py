# pyrefly: ignore [missing-import]
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
# pyrefly: ignore [missing-import]
import httpx
from app.market_client import EldoradoClient, MarketplaceAPIError


@pytest.mark.asyncio
async def test_eldorado_client_token_acquisition():
    client = EldoradoClient(client_id="test_client_id", client_secret="test_client_secret")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "AccessToken": "test_access_token_123",
        "ExpiresIn": 900,
        "TokenType": "Bearer",
    }
    mock_resp.raise_for_status = MagicMock()

    with patch.object(httpx.AsyncClient, "post", return_value=mock_resp) as mock_post:
        token = await client.get_access_token()
        assert token == "test_access_token_123"
        assert client._access_token == "test_access_token_123"
        assert client._token_expires_at > time.time()
        mock_post.assert_called_once()

        # Calling again should use cached token without additional network request
        token2 = await client.get_access_token()
        assert token2 == "test_access_token_123"
        assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_eldorado_client_deliver_order():
    client = EldoradoClient(client_id="test_client_id", client_secret="test_client_secret")
    client._access_token = "valid_token"
    client._token_expires_at = time.time() + 300

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"success": true}'
    mock_resp.json.return_value = {"success": True}
    mock_resp.raise_for_status = MagicMock()

    with patch.object(httpx.AsyncClient, "request", return_value=mock_resp) as mock_req:
        res = await client.deliver_order("order-999", {"notes": "delivered"})
        assert res == {"success": True}
        assert mock_req.call_args[1]["headers"]["Authorization"] == "Bearer valid_token"

