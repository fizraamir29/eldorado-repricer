import asyncio
import os
import httpx
import json
from dotenv import load_dotenv

async def run():
    load_dotenv(".env")
    client_id = os.getenv("ELDORADO_CLIENT_ID")
    client_secret = os.getenv("ELDORADO_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Missing ELDORADO_CLIENT_ID or ELDORADO_CLIENT_SECRET in .env")
        return

    # Authenticate
    print("Authenticating...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        auth_resp = await client.post(
            "https://www.eldorado.gg/api/authentication/seller/token",
            json={"clientId": client_id, "clientSecret": client_secret}
        )
        if auth_resp.status_code != 200:
            print(f"Auth failed: {auth_resp.status_code} {auth_resp.text}")
            return
        
        data = auth_resp.json()
        token = data.get("AccessToken") or data.get("access_token") or data.get("accessToken")
        
        if not token:
            print("No token in response")
            return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    offer_id = "0b6d4ebf-5a52-495f-2d9e-08deebb04538"
    url = f"https://www.eldorado.gg/api/v1/currency-management/me/offers/{offer_id}"
    
    async with httpx.AsyncClient(headers=headers) as client:
        # Try different payload structures based on details.Pricing error
        payloads = [
            # Test 1: Capital Pricing
            {"details": {"Pricing": {"pricePerUnit": {"amount": 31.98, "currency": "USD"}}}},
            # Test 2: Lowercase pricing
            {"details": {"pricing": {"pricePerUnit": {"amount": 31.98, "currency": "USD"}}}},
            # Test 3: Capital Pricing with amount directly
            {"details": {"Pricing": {"amount": 31.98, "currency": "USD"}}},
            # Test 4: Pricing with price directly
            {"details": {"Pricing": {"price": 31.98}}},
        ]
        
        for i, payload in enumerate(payloads):
            print(f"\n--- Testing Payload {i+1} ---")
            print("Payload:", json.dumps(payload))
            put_resp = await client.put(url, json=payload)
            print(f"Status: {put_resp.status_code}")
            print(f"Response: {put_resp.text}")
            if put_resp.status_code == 200:
                print("SUCCESS!")
                break

asyncio.run(run())
