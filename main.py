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
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"Pas 1: Navigăm către {TARGET_URL}")
            # Folosim 'load' pentru stabilitate pe GitHub
            await page.goto(TARGET_URL, wait_until="load", timeout=60000)
            
            # Așteptăm să dispară eventualele ecrane de încărcare
            await page.wait_for_timeout(5000)

            # Acceptăm cookies rapid
            try:
                await page.click("#onetrust-accept-btn-handler", timeout=5000)
            except: pass

            print(f"Pas 2: Introducem POD {POD_CODE}")
            # REZOLVARE EROARE: Folosim .first pentru a alege prima căsuță de POD găsită
            input_field = page.locator("input[name='getinfo_pod']").first
            await input_field.wait_for(state="visible", timeout=15000)
            await input_field.fill(POD_CODE)

            print("Pas 3: Trimitem...")
            await page.keyboard.press("Enter")
            
            # Așteptăm să apară rezultatul (pop-up-ul alb)
            await page.wait_for_timeout(10000) 

            content = await page.content()
            content_lower = content.lower()

            # Cuvinte cheie care confirmă că TOTUL E BINE
            ok_keywords = [
                "nu avem înregistrată nicio întrerupere", 
                "nu sunt întreruperi",
                "nu am găsit nicio întrerupere"
            ]

            if any(key in content_lower for key in ok_keywords):
                print("✅ Status: OK (Fără avarii raportate)")
            else:
                # Verificăm dacă măcar am ajuns la rezultat
                if "deranjamente" in content_lower or "alimentarea cu energie" in content_lower:
                    msg = f"⚠️ ALERTA CURENT: Posibilă întrerupere detectată pentru POD {POD_CODE}! Verifică manual aici: {TARGET_URL}"
                    print("🚨 Status: POSIBILĂ AVARIE DETECTATĂ!")
                    send_telegram_msg(msg)
                else:
                    print("❓ Status: Pagina nu pare să fi încărcat rezultatul corect.")

        except Exception as e:
            print(f"❌ Eroare: {e}")
            await page.screenshot(path="debug.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
