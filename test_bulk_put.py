import asyncio
import os
import httpx
from dotenv import load_dotenv

async def run():
    load_dotenv(".env")
    client_id = os.getenv("ELDORADO_CLIENT_ID")
    client_secret = os.getenv("ELDORADO_CLIENT_SECRET")

    # Authenticate
    print("Authenticating...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        auth_resp = await client.post(
            "https://www.eldorado.gg/api/authentication/seller/token",
            json={"clientId": client_id, "clientSecret": client_secret}
        )
        token = auth_resp.json().get("AccessToken")
        if not token:
            print("No token.")
            return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # "57" is the gameId for Pokemon Go
    url = "https://www.eldorado.gg/api/v1/currency-management/me/offers/bulk/57/change-price"
    
    # Let's try sending an empty object to see what fields it asks for!
    payloads = [
        {}, 
        [], 
        {"offers": []},
        [{"id": "0b6d4ebf-5a52-495f-2d9e-08deebb04538", "price": 31.98}]
    ]
    
    async with httpx.AsyncClient(headers=headers) as client:
        for p in payloads:
            print(f"\nPOST {url}")
            print(f"Payload: {p}")
            resp = await client.post(url, json=p)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")

asyncio.run(run())
