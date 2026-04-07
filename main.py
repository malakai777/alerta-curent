import asyncio
import os
import requests
from playwright.async_api import async_playwright

# --- CONFIGURARE ---
POD_CODE = "RO001E110447409"
TARGET_URL = "https://www.reteleelectrice.ro/intreruperi/"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
        except: pass

async def run():
    async with async_playwright() as p:
        # Lansăm browserul cu argumente extra pentru a evita detectarea
        browser = await p.chromium.launch(headless=True)
        
        # Creăm un context care imită un browser real de Windows
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()

        try:
            print(f"Pas 1: Navigăm către {TARGET_URL}")
            # Am schimbat wait_until la 'domcontentloaded' pentru a fi mai rapid și a evita timeout-ul
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
            
            # Așteptăm puțin să se încarce elementele vizuale
            await page.wait_for_timeout(3000)

            # Acceptăm cookies dacă apar
            try:
                cookie_btn = page.locator("#onetrust-accept-btn-handler")
                if await cookie_btn.is_visible(timeout=5000):
                    await cookie_btn.click()
            except: pass

            print(f"Pas 2: Introducem POD {POD_CODE}")
            input_field = page.locator("input[placeholder*='POD'], .form-control")
            await input_field.wait_for(state="visible", timeout=15000)
            await input_field.fill(POD_CODE)

            print("Pas 3: Trimitem...")
            await page.keyboard.press("Enter")
            
            # Așteptăm pop-up-ul de rezultat
            await page.wait_for_timeout(8000) 

            content = await page.content()
            content_lower = content.lower()

            ok_keywords = ["nu avem înregistrată nicio întrerupere", "nu sunt întreruperi"]

            if any(key in content_lower for key in ok_keywords):
                print("✅ Status: OK (Fără avarii)")
            else:
                msg = f"⚠️ ALERTA CURENT: Posibilă problemă la POD {POD_CODE}! Verifică: {TARGET_URL}"
                print("🚨 Status: POSIBILĂ AVARIE")
                send_telegram_msg(msg)

        except Exception as e:
            print(f"❌ Eroare: {e}")
            # Salvăm o poză să vedem de ce s-a blocat
            await page.screenshot(path="debug.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
    
