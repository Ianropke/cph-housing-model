import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating...")
        
        # We don't wait for networkidle, just domcontentloaded
        await page.goto("https://www.boligsiden.dk/markedsindeks/udbud", wait_until="domcontentloaded")
        
        print("Waiting for table to render...")
        try:
            # Wait for any table
            await page.wait_for_selector("table", timeout=15000)
            print("Table rendered!")
            
            # Extract the text of the first table
            table_text = await page.locator("table").first.inner_text()
            print("--- TABLE PREVIEW ---")
            print(table_text[:500])
            print("---------------------")
        except Exception as e:
            print("Failed to find table:", e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
