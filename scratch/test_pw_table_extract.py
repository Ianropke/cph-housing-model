import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        print("Navigating to boligsiden (non-headless)...")
        
        await page.goto("https://www.boligsiden.dk/markedsindeks/udbud")
        await asyncio.sleep(5)
        
        # Try to accept cookies
        try:
            print("Accepting cookies...")
            await page.get_by_role("button", name=r"(?i)(Accepter alle|Tillad alle|Acceptér alle)").click(timeout=5000)
            await asyncio.sleep(2)
        except Exception as e:
            print("No cookie banner found or could not click it.")
        
        # Read the table
        try:
            print("Extracting table data...")
            # We look for the main table container
            table_text = await page.locator("table").inner_text()
            print("--- TABLE DATA ---")
            print(table_text)
            print("------------------")
        except Exception as e:
            print("Could not find table:", e)
            body = await page.locator("body").inner_text()
            print("BODY FALLBACK:", body[:1000])
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
