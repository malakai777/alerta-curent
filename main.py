import asyncio
import os
import requests # Make sure 'requests' is in your requirements.txt
from playwright.async_api import async_playwright

# Configuration
POD_CODE = "RO001E110447409"
TARGET_URL = "https://www.reteleelectrice.ro/intreruperi/"
# Get these from GitHub Secrets for security
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=data)
    else:
        print("Telegram configuration missing!")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            print(f"Pas 1: Deschidem {TARGET_URL}")
            await page.goto(TARGET_URL, wait_until="networkidle")

            print(f"Pas 2: Introducem POD-ul {POD_CODE}")
            await page.fill("input[placeholder*='POD'], .form-control", POD_CODE)

            print("Pas 3: Trimitem formularul")
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000) 

            content = await page.content()
            if "Nu sunt întreruperi" in content:
                print("Status: Totul e ok.")
            else:
                msg = "⚠️ Alerta Curent: A fost detectata o intrerupere pe strada ta!"
                print(msg)
                send_telegram_msg(msg)

        except Exception as e:
            print(f"Eroare: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
    
