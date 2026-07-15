import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # KEY: Not headless!
        page = await browser.new_page()
        print("Navigating to boligsiden (non-headless)...")
        
        await page.goto("https://www.boligsiden.dk/markedsindeks/udbud")
        
        print("Waiting 15 seconds to allow cloudflare to pass if needed...")
        await asyncio.sleep(15)
        
        body_text = await page.locator("body").inner_text()
        print("--- BODY PREVIEW ---")
        print(body_text[:500])
        print("---------------------")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
