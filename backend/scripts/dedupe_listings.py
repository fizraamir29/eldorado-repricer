import asyncio
import os
import sys

# Ensure backend directory is in the path so we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models import Listing, AutomationRule, PriceHistory, Notification

async def main():
    print("Finding duplicate listings...")

    async with AsyncSessionLocal() as session:
        # Find duplicates: group by user_id and marketplace_listing_id having count > 1
        duplicates_query = (
            select(Listing.user_id, Listing.marketplace_listing_id)
            .group_by(Listing.user_id, Listing.marketplace_listing_id)
            .having(func.count(Listing.id) > 1)
        )
        
        result = await session.execute(duplicates_query)
        duplicate_groups = result.all()
        
        if not duplicate_groups:
            print("No duplicate listings found. Safe to run migration.")
            return

        print(f"Found {len(duplicate_groups)} duplicate groups to process.")
        
        for user_id, marketplace_listing_id in duplicate_groups:
            print(f"\nProcessing duplicates for marketplace_listing_id: {marketplace_listing_id}")
            
            # Fetch all listings in this group, ordered by created_at desc
            listings_query = (
                select(Listing)
                .where(Listing.user_id == user_id, Listing.marketplace_listing_id == marketplace_listing_id)
                .order_by(Listing.created_at.desc())
            )
            listings_result = await session.execute(listings_query)
            listings = listings_result.scalars().all()
            
            # Keep the oldest one (assuming it's the one the user configured originally)
            # Or perhaps the one where rule.min_price < current_price?
            # Let's keep the one that was created FIRST
            keep_listing = listings[-1]
            delete_listings = listings[:-1]
            
            print(f"  Keeping listing ID: {keep_listing.id} (created: {keep_listing.created_at})")
            
            for to_delete in delete_listings:
                print(f"  Deleting duplicate ID: {to_delete.id} (created: {to_delete.created_at})")
                await session.delete(to_delete)
                
        await session.commit()
        print("\nDeduplication complete! You can now safely run the unique constraint migration.")

if __name__ == "__main__":
    asyncio.run(main())
