import asyncio
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.models import User
from sqlalchemy import select
from app.security import decrypt_secret

async def main():
    async with AsyncSessionLocal() as session:
        r = await session.execute(select(User).limit(1))
        u = r.scalar_one_or_none()
        if u and u.marketplace_client_secret_encrypted:
            try:
                secret = decrypt_secret(u.marketplace_client_secret_encrypted)
                print(f"CLIENT_ID={u.marketplace_client_id}")
                print(f"SECRET={secret}")
            except Exception as e:
                print(f"Failed to decrypt: {e}")
        else:
            print("No secret found")

asyncio.run(main())
