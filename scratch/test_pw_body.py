import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating...")
        
        await page.goto("https://www.boligsiden.dk/markedsindeks/udbud", wait_until="domcontentloaded")
        await asyncio.sleep(5)  # Let javascript and data load
        
        # Print the text of the body to see what's actually there
        body_text = await page.locator("body").inner_text()
        print("--- BODY PREVIEW ---")
        print(body_text[:1000])
        print("---------------------")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
