import asyncio
import os
import httpx
from dotenv import load_dotenv

async def run_test():
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
        
        token = auth_resp.json().get("accessToken")
        headers = {"Authorization": f"Bearer {token}"}

        listing_id = "0b6d4ebf-5a52-495f-2d9e-08deebb04538"
        target_price = 31.99

        # Test payloads
        payloads = [
            {"name": "amount only", "url": f"/api/v1/currency-management/me/offers/{listing_id}/change-price", "payload": {"amount": target_price}},
            {"name": "price only", "url": f"/api/v1/currency-management/me/offers/{listing_id}/change-price", "payload": {"price": target_price}},
            {"name": "pricePerUnit object", "url": f"/api/v1/currency-management/me/offers/{listing_id}/change-price", "payload": {"pricePerUnit": {"amount": target_price, "currency": "USD"}}},
            {"name": "flexible style", "url": f"/api/v1/currency-management/me/offers/{listing_id}/change-price", "payload": {"price": target_price, "amount": target_price, "currency": "USD"}},
            {"name": "direct PUT", "url": f"/api/v1/currency-management/me/offers/{listing_id}", "payload": {"pricePerUnit": {"amount": target_price, "currency": "USD"}}},
        ]

        print(f"\nTesting payloads for listing {listing_id} at ${target_price}")
        for p in payloads:
            print(f"\n--- Testing: {p['name']} ---")
            print(f"PUT https://www.eldorado.gg{p['url']}")
            print(f"Payload: {p['payload']}")
            
            resp = await client.put(f"https://www.eldorado.gg{p['url']}", headers=headers, json=p['payload'])
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
            
            if resp.status_code == 200:
                print("SUCCESS!")
                break
            
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(run_test())
