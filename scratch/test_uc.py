import time
import undetected_chromedriver as uc
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run():
    print("Initializing undetected-chromedriver...")
    options = uc.ChromeOptions()
    options.headless = True
    # Often headless gets detected, let's try headless=True first, but Boligsiden might block it.
    
    driver = uc.Chrome(options=options)
    
    try:
        print("Navigating to boligsiden...")
        driver.get("https://www.boligsiden.dk/markedsindeks/udbud")
        
        # Wait for the table to appear (meaning we passed Cloudflare)
        print("Waiting for page load...")
        time.sleep(10)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print("--- BODY PREVIEW ---")
        print(body_text[:500])
        print("---------------------")
        
    except Exception as e:
        print("Error:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
