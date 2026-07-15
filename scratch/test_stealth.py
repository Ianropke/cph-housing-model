import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await stealth(page)
        print("Navigating with stealth...")
        
        await page.goto("https://www.boligsiden.dk/markedsindeks/udbud", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        body_text = await page.locator("body").inner_text()
        print("--- BODY PREVIEW ---")
        print(body_text[:500])
        print("---------------------")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
