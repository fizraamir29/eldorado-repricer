import asyncio
import os
import httpx
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
        
        token = auth_resp.json().get("AccessToken")
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
        print(f"GET {url}")
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text)
            return
        
        offer_data = resp.json()
        print("GET Offer keys:", offer_data.keys())
        
        # Change the price slightly to test
        offer_data["pricePerUnit"]["amount"] = 31.98
        
        # PUT it back
        print(f"PUT {url}")
        put_resp = await client.put(url, json=offer_data)
        print(f"Status: {put_resp.status_code}")
        print(f"Response: {put_resp.text}")

asyncio.run(run())
