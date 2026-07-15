import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        api_responses = []

        # Intercept network responses
        page.on("response", lambda response: asyncio.create_task(handle_response(response, api_responses)))
        
        print("Navigating to boligsiden...")
        await page.goto("https://www.boligsiden.dk/markedsindeks/udbud", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)  # wait for API calls to settle
        await browser.close()
        
        print(f"Captured {len(api_responses)} JSON API responses.")

async def handle_response(response, api_responses):
    try:
        if "application/json" in response.headers.get("content-type", "") and response.request.method == "GET":
            if "boligsiden" in response.url or "api" in response.url:
                json_data = await response.json()
                api_responses.append(json_data)
                # Print a snippet of the JSON if it looks relevant
                data_str = str(json_data)
                if "udbud" in data_str.lower() or "cases" in data_str.lower() or "series" in data_str.lower():
                    print(f"Found interesting API response from {response.url[:100]}! Size: {len(data_str)}")
    except Exception as e:
        pass

if __name__ == "__main__":
    asyncio.run(run())
