import asyncio
import os
from playwright.async_api import async_playwright

# Configuration
POD_CODE = "RO001E110447409"
TARGET_URL = "https://www.reteleelectrice.ro/intreruperi/"

async def run():
    async with async_playwright() as p:
        # Launch browser (headless for GitHub Actions)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"Pas 1: Deschidem {TARGET_URL}")
            await page.goto(TARGET_URL, wait_until="networkidle")

            # Inchidem bannerul de cookies daca apare
            cookie_btn = page.locator("#onetrust-accept-btn-handler")
            if await cookie_btn.is_visible():
                await cookie_btn.click()

            print(f"Pas 2: Introducem POD-ul {POD_CODE}")
            input_selector = "input[placeholder*='POD'], .form-control"
            await page.wait_for_selector(input_selector)
            await page.fill(input_selector, POD_CODE)

            print("Pas 3: Trimitem formularul")
            submit_button = page.locator("button.btn-orange, button:has-text('Trimite')")
            
            if await submit_button.is_visible():
                await submit_button.click()
            else:
                await page.keyboard.press("Enter")

            # Asteptam rezultatele
            await page.wait_for_timeout(5000) 

            content = await page.content()
            if "Nu sunt întreruperi" in content:
                print("Status: Nu sunt intreruperi gasite.")
            else:
                print("Status: Posibila intrerupere detectata!")
                # Aici vine codul tau de alerta Telegram

        except Exception as e:
            print(f"Eroare: {e}")
            await page.screenshot(path="debug_error.png")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
