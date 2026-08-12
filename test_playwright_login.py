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

    print("Starting Playwright Login Test...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Using a realistic user agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Navigating to Eldorado Login...")
        await page.goto("https://www.eldorado.gg/login", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        print("Filling in credentials...")
        # Eldorado's login form uses name="email" and name="password"
        await page.fill('input[type="email"], input[name="email"]', username)
        await page.fill('input[type="password"], input[name="password"]', password)
        
        print("Clicking Login...")
        # Usually a button with type submit or text Login/Sign In
        await page.click('button[type="submit"]')
        
        print("Waiting 10 seconds for login to process...")
        await page.wait_for_timeout(10000)
        
        print("Navigating to My Offers page...")
        await page.goto("https://www.eldorado.gg/me/offers", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        title = await page.title()
        print(f"My Offers Page Title: {title}")
        
        print("Taking a screenshot to verify login was successful...")
        await page.screenshot(path="login_success.png")
        print("Screenshot saved to login_success.png! Check this image to see if we are logged in or if a Captcha stopped us.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
