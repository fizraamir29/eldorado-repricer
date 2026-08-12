import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

async def run():
    load_dotenv(".env")
    username = os.getenv("ELDORADO_USERNAME")
    password = os.getenv("ELDORADO_PASSWORD")
    
    if not username or not password:
        print("ERROR: Please add ELDORADO_USERNAME and ELDORADO_PASSWORD to your .env file")
        return

    print("Starting Playwright Login Test (Debugging)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Navigating to Eldorado Login...")
        await page.goto("https://www.eldorado.gg/login", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        title = await page.title()
        print(f"Login Page Title: {title}")
        
        # Take a screenshot to see what is actually on the screen
        await page.screenshot(path="login_debug.png")
        print("Saved login_debug.png")
        
        # Save HTML to a file so we can inspect it
        html = await page.content()
        with open("login_debug.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved login_debug.html")

        # Let's try to find ANY input fields
        inputs = await page.locator("input").count()
        print(f"Total <input> fields found on page: {inputs}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
