import asyncio
import re
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        print("Navigating to boligsiden search...")
        await page.goto("https://www.boligsiden.dk/tilsalg?municipality=K%C3%B8benhavn&itemType=Ejerlejlighed")
        await asyncio.sleep(5)
        
        # Accept cookies
        try:
            print("Accepting cookies...")
            await page.get_by_role("button", name=re.compile(r"Accepter og luk", re.IGNORECASE)).click(timeout=5000)
            await asyncio.sleep(2)
        except Exception as e:
            print("Cookie banner not clicked:", e)
        
        # Look for the result count, e.g. "Viser 1 - 30 af 2.400 resultater"
        try:
            body_text = await page.locator("body").inner_text()
            print("--- First 500 chars of body ---")
            print(body_text[:500])
            print("-------------------------------")
            
            # Let's use regex to find "af [number] resultater" or similar
            match = re.search(r"af ([\d\.]+) (boliger|resultater)", body_text, re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(".", "")
                print(f"SUCCESS! Found supply count: {count_str}")
            else:
                # print more text to debug
                print("Could not find regex match. Here is more text:")
                print(body_text[500:2000])
                
        except Exception as e:
            print("Error extracting text:", e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
