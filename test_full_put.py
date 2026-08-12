import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("ELDORADO_TOKEN")
HEADERS = {
    "authorization": f"Bearer {TOKEN}",
    "content-type": "application/json",
    "accept": "application/json",
}

async def run():
    offer_id = "0b6d4ebf-5a52-495f-2d9e-08deebb04538"
    url = f"https://www.eldorado.gg/api/v1/currency-management/me/offers/{offer_id}"
    
    async with httpx.AsyncClient(headers=HEADERS) as client:
        # GET the full offer
        resp = await client.get(url)
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
