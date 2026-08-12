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
            print(f"No token in response. Keys found: {list(data.keys())}")
            print(data)
            return
        print("Auth success!")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    offer_id = "0b6d4ebf-5a52-495f-2d9e-08deebb04538"
    url = f"https://www.eldorado.gg/api/v1/currency-management/me/offers/{offer_id}"
    
    async with httpx.AsyncClient(headers=headers) as client:
        print(f"GET {url}")
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text)
            return
        
        offer_data = resp.json()
        offer = offer_data.get("offer", {})
        
        # Change price
        if "pricePerUnit" in offer:
            offer["pricePerUnit"]["amount"] = 31.98
            offer["pricePerUnit"]["currency"] = "USD"
        
        # Try PUT with details
        put_payload = {"details": offer}
        print(f"\nPUT {url}")
        print("Payload:", json.dumps(put_payload)[:200] + "...")
        put_resp = await client.put(url, json=put_payload)
        print(f"Status: {put_resp.status_code}")
        print(f"Response: {put_resp.text}")
        
        if put_resp.status_code != 200:
            # Try without details just in case
            print("\nTrying raw offer without details wrapper...")
            put_resp2 = await client.put(url, json=offer)
            print(f"Status: {put_resp2.status_code}")
            print(f"Response: {put_resp2.text}")

asyncio.run(run())
