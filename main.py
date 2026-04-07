import asyncio
import os
from playwright.async_api import async_playwright

# Configuration - Replace these with your actual details or GitHub Secrets
POD_CODE = "RO001E110447409"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TARGET_URL = "https://www.reteleelectrice.ro/intreruperi/"

async def run():
    async with async_playwright() as p:
        # Launch browser (headless for GitHub Actions)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()

        try:
            print(f"Step 1: Opening {TARGET_URL}")
            await page.goto(TARGET_URL, wait_until="networkidle")

            # Handle Cookie Banner if it exists
            if await page.locator("#onetrust-accept-btn-handler").is_visible():
                await page.click("#onetrust-accept-btn-handler")

            print(f"Step 2: Entering POD {POD_CODE}")
            # This selector is based on the current site structure
            input_selector = "input[placeholder*='POD'], .form-control"
            await page.wait_for_selector(input_selector)
            await page.fill(input_selector, POD_CODE)

            print("Step 3: Clicking the submit button")
            # This is the part that was likely failing. 
            # I've updated the selector to be more robust.
            submit_button = page.locator("button.btn-orange, button:has-text('Trimite')")
            
            if await submit_button.is_visible():
                await submit_button.click()
            else:
                # Fallback: press Enter if the button can't be clicked
                await page.keyboard.press("Enter")

            # Wait for results to load
            await page.wait_for_timeout(5000) 

            # Check for outage text
            content = await page.content()
            if "Nu sunt întreruperi" in content:
                print("Status: No outages found.")
            else:
                print("Status: Potential outage detected!")
                # Logic to send Telegram alert would go here

        except Exception as e:
            print(f"Error: {e}")
            # Take a screenshot for debugging in GitHub Actions
            await page.screenshot(path="debug_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
    
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(verifica_pod())
    
