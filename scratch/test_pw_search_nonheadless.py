import asyncio
import re
from playwright.async_api import async_playwright

async def run():
    print("Launching visible browser to bypass Cloudflare...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        # Go to Ejerlejligheder in København
        await page.goto("https://www.boligsiden.dk/tilsalg?municipality=K%C3%B8benhavn&itemType=Ejerlejlighed")
        await asyncio.sleep(5)
        
        # Click cookie accept
        try:
            print("Accepting cookies...")
            await page.get_by_role("button", name=re.compile(r"Accepter og luk", re.IGNORECASE)).click(timeout=3000)
            await asyncio.sleep(2)
        except:
            pass
            
        print("Extracting supply count...")
        try:
            # The count is usually in a h1 or span, let's just grab the whole inner text
            body_text = await page.locator("body").inner_text()
            
            # Look for e.g. "Viser 1 - 30 af 2.450 resultater" or similar
            match = re.search(r"af ([\d\.]+) (boliger|resultater)", body_text, re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(".", "")
                print(f"--- SUCCESS ---")
                print(f"Udbudte Ejerlejligheder i København: {count_str}")
            else:
                print("Could not find regex. Here is the first 1000 chars of the page:")
                print(body_text[:1000])
        except Exception as e:
            print("Error:", e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
