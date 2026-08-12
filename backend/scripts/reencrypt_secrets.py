import asyncio
import os
import sys

# Ensure backend directory is in the path so we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from cryptography.fernet import Fernet
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User
from app.config import settings

_FALLBACK_KEY = b"3CDQw1FW49zj-QvOeQRQCPWrbCZmU4k33GOHBVaow1k="

async def main():
    new_key = os.environ.get("NEW_ENCRYPTION_KEY")
    if not new_key or len(new_key) != 44:
        print("ERROR: NEW_ENCRYPTION_KEY environment variable is not set correctly or is not 44 chars.")
        return

    old_fernet = Fernet(_FALLBACK_KEY)
    new_fernet = Fernet(new_key.encode())
    
    print(f"Re-encrypting database credentials to the new secure key...")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        updated_count = 0
        for user in users:
            changed = False
            
            # Re-encrypt client secret
            if user.marketplace_client_secret_encrypted:
                try:
                    # Check if it was encrypted with the old fallback key
                    decrypted = old_fernet.decrypt(user.marketplace_client_secret_encrypted.encode()).decode()
                    user.marketplace_client_secret_encrypted = new_fernet.encrypt(decrypted.encode()).decode()
                    changed = True
                except Exception:
                    # Might already be encrypted with the new key, or invalid.
                    pass
                    
            # Re-encrypt api key
            if user.marketplace_api_key_encrypted:
                try:
                    decrypted = old_fernet.decrypt(user.marketplace_api_key_encrypted.encode()).decode()
                    user.marketplace_api_key_encrypted = new_fernet.encrypt(decrypted.encode()).decode()
                    changed = True
                except Exception:
                    pass
                    
            if changed:
                session.add(user)
                updated_count += 1
                
        if updated_count > 0:
            await session.commit()
            print(f"Successfully re-encrypted secrets for {updated_count} user(s).")
        else:
            print("No secrets needed re-encryption (either none exist, or they are already secured).")

if __name__ == "__main__":
    asyncio.run(main())
