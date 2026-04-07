import asyncio
import os
import requests
from playwright.async_api import async_playwright

# --- CONFIGURARE ---
# POD-ul tău din imagine
POD_CODE = "RO001E110447409"
TARGET_URL = "https://www.reteleelectrice.ro/intreruperi/"

# Acestea trebuie setate în GitHub -> Settings -> Secrets -> Actions
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    """Trimite notificare pe Telegram dacă datele sunt configurate."""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
            requests.post(url, data=data, timeout=10)
            print("✅ Notificare trimisă pe Telegram.")
        except Exception as e:
            print(f"❌ Eroare la trimiterea pe Telegram: {e}")
    else:
        print("⚠️ Notificarea Telegram a fost sărită (lipsă TOKEN sau CHAT_ID în Secrets).")

async def run():
    async with async_playwright() as p:
        # Lansăm browserul
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"Pas 1: Deschidem {TARGET_URL}")
            await page.goto(TARGET_URL, wait_until="networkidle")

            # Închidem bannerul de cookies dacă apare
            cookie_btn = page.locator("#onetrust-accept-btn-handler")
            if await cookie_btn.is_visible():
                await cookie_btn.click()
                await page.wait_for_timeout(1000)

            print(f"Pas 2: Introducem POD-ul {POD_CODE}")
            input_selector = "input[placeholder*='POD'], .form-control"
            await page.wait_for_selector(input_selector)
            await page.fill(input_selector, POD_CODE)

            print("Pas 3: Trimitem formularul (Enter)")
            await page.keyboard.press("Enter")

            # Așteptăm să se încarce fereastra pop-up (cea din poza ta)
            print("Pas 4: Verificăm rezultatul...")
            await page.wait_for_timeout(7000) 

            # Extragem tot textul de pe pagină
            content = await page.content()
            content_lower = content.lower()

            # Verificăm mesajul de "Totul e bine" (cel din captura ta de ecran)
            # Folosim fragmente cheie pentru a fi siguri
            ok_keywords = [
                "nu avem înregistrată nicio întrerupere",
                "nu sunt întreruperi",
                "nu am găsit nicio întrerupere"
            ]

            is_ok = any(key in content_lower for key in ok_keywords)

            if is_ok:
                print("✅ Status: Totul este OK. Nu sunt avarii raportate pentru acest POD.")
            else:
                # Dacă textul de confirmare lipsește, înseamnă că e avarie sau site-ul s-a blocat
                msg = f"⚠️ ALERTA CURENT: Posibilă problemă la POD {POD_CODE}! Site-ul NU confirmă starea OK. Verifică aici: {TARGET_URL}"
                print("🚨 Status: POSIBILĂ AVARIE DETECTATĂ!")
                send_telegram_msg(msg)

        except Exception as e:
            print(f"❌ Eroare în timpul execuției: {e}")
            # Salvăm o poză în caz de eroare (vizibilă în Artifacts pe GitHub)
            await page.screenshot(path="debug_screenshot.png")
        
        finally:
            await browser.close()
            print("Proces terminat.")

if __name__ == "__main__":
    asyncio.run(run())
