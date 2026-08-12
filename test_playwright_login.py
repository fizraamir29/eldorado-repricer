import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

async def run():
    load_dotenv(".env")
    username = os.getenv("ELDORADO_USERNAME")
    password = os.getenv("ELDORADO_PASSWORD")

    print("Starting Playwright Login Test (Parsing Inputs)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Navigating to Eldorado Login...")
        await page.goto("https://www.eldorado.gg/login", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        # Let's inspect all input fields
        locators = await page.locator("input").all()
        print(f"\nFound {len(locators)} input fields. Inspecting them:")
        
        email_selector = None
        password_selector = None
        
        for i, loc in enumerate(locators):
            html = await loc.evaluate("el => el.outerHTML")
            name = await loc.get_attribute("name")
            type_attr = await loc.get_attribute("type")
            placeholder = await loc.get_attribute("placeholder")
            print(f"Input {i}: type='{type_attr}', name='{name}', placeholder='{placeholder}'")
            
            # Identify the likely email and password fields
            if type_attr == "email" or "email" in str(name).lower() or "email" in str(placeholder).lower():
                email_selector = f'input[name="{name}"]' if name else f'input[type="{type_attr}"]'
            if type_attr == "password" or "password" in str(name).lower() or "password" in str(placeholder).lower():
                password_selector = f'input[name="{name}"]' if name else f'input[type="{type_attr}"]'
                
        print(f"\nGuessed Email Selector: {email_selector}")
        print(f"Guessed Password Selector: {password_selector}")

        # If we found them, let's try to fill them!
        if email_selector and password_selector and username and password:
            print(f"\nTrying to login with guessed selectors...")
            await page.fill(email_selector, username)
            await page.fill(password_selector, password)
            print("Filled credentials!")
            
            # Find the login button (usually type=submit)
            await page.click("button[type='submit']")
            print("Clicked submit! Waiting 10 seconds...")
            await page.wait_for_timeout(10000)
            
            await page.goto("https://www.eldorado.gg/me/offers", wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            print(f"Final Page Title: {await page.title()}")
        else:
            print("\nCould not find valid selectors or missing credentials in .env")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
