import asyncio
from playwright.async_api import async_playwright

async def run():
    print("Starting Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        url = "https://www.eldorado.gg/"
        print(f"Navigating to {url}...")
        response = await page.goto(url, wait_until="domcontentloaded")
        
        print(f"Response Status: {response.status}")
        
        # Wait a bit to let Cloudflare load
        await page.wait_for_timeout(5000)
        
        title = await page.title()
        print(f"Page Title: {title}")
        
        # Take a screenshot to see if we hit a Captcha
        await page.screenshot(path="cloudflare_test.png")
        print("Screenshot saved to cloudflare_test.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
