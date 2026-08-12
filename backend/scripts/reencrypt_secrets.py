import asyncio
import os
import sys
import argparse

# Inject the original fallback key so app.security doesn't crash on import
# and it initializes correctly with the old key for decryption purposes.
os.environ["ENCRYPTION_KEY"] = "3CDQw1FW49zj-QvOeQRQCPWrbCZmU4k33GOHBVaow1k="

# Ensure backend directory is in the path so we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from cryptography.fernet import Fernet
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User

_FALLBACK_KEY = b"3CDQw1FW49zj-QvOeQRQCPWrbCZmU4k33GOHBVaow1k="

async def main(dry_run=False):
    new_key = os.environ.get("NEW_ENCRYPTION_KEY")
    if not new_key or len(new_key) != 44:
        print("ERROR: NEW_ENCRYPTION_KEY environment variable is not set correctly or is not 44 chars.")
        return

    old_fernet = Fernet(_FALLBACK_KEY)
    new_fernet = Fernet(new_key.encode())
    
    if dry_run:
        print("--- DRY RUN MODE ---")
        
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
                    decrypted = old_fernet.decrypt(user.marketplace_client_secret_encrypted.encode()).decode()
                    if dry_run:
                        masked = decrypted[:3] + "***" + decrypted[-3:] if len(decrypted) > 6 else "***"
                        print(f"User {user.id} Client Secret: {masked}")
                    else:
                        user.marketplace_client_secret_encrypted = new_fernet.encrypt(decrypted.encode()).decode()
                    changed = True
                except Exception as e:
                    print(f"Failed to decrypt client_secret for user {user.id}: {e}")
                    
            # Re-encrypt api key
            if user.marketplace_api_key_encrypted:
                try:
                    decrypted = old_fernet.decrypt(user.marketplace_api_key_encrypted.encode()).decode()
                    if dry_run:
                        masked = decrypted[:3] + "***" + decrypted[-3:] if len(decrypted) > 6 else "***"
                        print(f"User {user.id} API Key: {masked}")
                    else:
                        user.marketplace_api_key_encrypted = new_fernet.encrypt(decrypted.encode()).decode()
                    changed = True
                except Exception as e:
                    print(f"Failed to decrypt api_key for user {user.id}: {e}")
                    
            if changed:
                session.add(user)
                updated_count += 1
                
        if updated_count > 0:
            if dry_run:
                print(f"Dry run complete. Would have updated {updated_count} user(s).")
            else:
                await session.commit()
                print(f"Successfully re-encrypted secrets for {updated_count} user(s).")
        else:
            print("No secrets needed re-encryption (either none exist, or they are already secured).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-encrypt secrets")
    parser.add_argument("--dry-run", action="store_true", help="Print masked decrypted values without saving")
    args = parser.parse_args()
    asyncio.run(main(args.dry_run))
