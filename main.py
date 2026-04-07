import asyncio
import os
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# --- CONFIGURARE ---
POD_CODE = "RO001E143159840"
ORAS_CAUTAT = "OTOPENI"
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
            viewport={'width': 1280, 'height': 1200},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"Pas 1: Verificare POD {POD_CODE}")
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=90000)
            
            # Acceptam cookies
            try: await page.click("#onetrust-accept-btn-handler", timeout=5000)
            except: pass

            # Introducem POD
            await page.locator("input[name='getinfo_pod']").first.fill(POD_CODE)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000) 

            # Verificam status curent
            content = await page.content()
            if not any(key in content.lower() for key in ["nu avem înregistrată nicio întrerupere", "nu sunt întreruperi"]):
                if "deranjamente" in content.lower():
                    send_telegram_msg(f"🚨 ALERTA: Problema curenta detectata la POD {POD_CODE}!")

            # --- PARTEA 2: PLANIFICATE (CU SCROLL SI ASTEPTARE) ---
            print("Pas 2: Cautam sectiunea de Planificate...")
            
            # Inchidem pop-up-ul de POD daca e deschis
            try: await page.keyboard.press("Escape")
            except: pass

            # Facem scroll pana jos ca sa se incarce filtrele
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)

            now = datetime.now()
            # Identificam selectoarele mai relaxat (dupa text sau tag)
            try:
                # Asteptam vizibilitatea oricarui select de pe pagina
                await page.wait_for_selector("select", timeout=20000)
                
                # Incercam sa selectam filtrele
                # Nota: Daca name='year' nu merge, cautam prin label
                await page.select_option("select", label=str(now.year), index=0) # An
                await page.select_option("select", index=1) # Luna (alegem a doua optiune de obicei)
                await page.select_option("select", value="IF") # Judet
                
                print("Filtre aplicate. Cautam...")
                await page.locator("button:has-text('Caută')").last.click()
                await page.wait_for_timeout(5000)

                final_content = await page.content()
                if ORAS_CAUTAT in final_content.upper() and "PUTNA" in final_content.upper():
                    send_telegram_msg(f"📅 PLANIFICATA: Lucrare gasita in Otopeni, Str. Putna!")
                else:
                    print("✅ Status: Nu sunt lucrari planificate pe strada ta.")

            except Exception as e:
                print(f"⚠️ Sectiunea de planificate nu a putut fi accesata: {e}")
                # Nu trimitem eroare pe Telegram aici ca sa nu te bazaim degeaba daca site-ul e lent

        except Exception as e:
            print(f"❌ Eroare generala: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
