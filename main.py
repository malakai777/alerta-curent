import asyncio
import os
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# --- CONFIGURARE ---
POD_CODE = "RO001E143159840"
ORAS_CAUTAT = "OTOPENI" # Majuscule, cum apare pe site
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
            # --- PARTEA 1: VERIFICARE PRIN POD ---
            print(f"Pas 1: Verificare POD {POD_CODE}")
            await page.goto(TARGET_URL, wait_until="load", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Inchide cookies
            try: await page.click("#onetrust-accept-btn-handler", timeout=3000)
            except: pass

            await page.locator("input[name='getinfo_pod']").first.fill(POD_CODE)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(7000) 

            content = await page.content()
            if not any(key in content.lower() for key in ["nu avem înregistrată nicio întrerupere", "nu sunt întreruperi"]):
                msg = f"🚨 ALERTA: Problema curenta detectata prin POD {POD_CODE}!"
                print(msg)
                send_telegram_msg(msg)

            # --- PARTEA 2: VERIFICARE PLANIFICATE (ILFOV / OTOPENI) ---
            print("Pas 2: Verificare Planificate Otopeni...")
            # Ne asiguram ca fereastra pop-up anterioara e inchisa
            try: await page.click(".modal-close, button[aria-label='Close']", timeout=2000)
            except: pass

            # Scroll pana la sectiunea de planificate (sau click pe butonul de sectiune daca exista)
            # Selectam filtrele automat bazat pe data curenta
            now = datetime.now()
            current_year = str(now.year)
            current_month = str(now.month) # 4 pentru Aprilie

            # Selectam Anul
            await page.select_option("select[name='year']", current_year)
            # Selectam Luna
            await page.select_option("select[name='month']", current_month)
            # Selectam Judetul (IF = Ilfov)
            await page.select_option("select[name='county']", "IF")
            
            # Click pe butonul de cautare din sectiunea de planificate
            # Nota: Selectorul 'button.btn-orange' poate fi comun, il cautam pe cel din sectiunea potrivita
            await page.locator("section >> button:has-text('Caută')").first.click()
            await page.wait_for_timeout(5000)

            # Verificam daca orasul si eventual strada apar in tabelul de rezultate
            tabel_html = await page.content()
            if ORAS_CAUTAT in tabel_html.upper():
                # Aici facem o verificare mai dura sa nu primim alerte de la vecini
                if "PUTNA" in tabel_html.upper():
                    msg_p = f"📅 ATENTIE: Lucrare PLANIFICATA gasita pentru Otopeni, Str. Putna in luna {current_month}!"
                    print(msg_p)
                    send_telegram_msg(msg_p)
                else:
                    print(f"Info: Exista lucrari in {ORAS_CAUTAT}, dar nu pe strada ta.")
            else:
                print(f"✅ Status: Nu sunt lucrari planificate in {ORAS_CAUTAT} luna aceasta.")

        except Exception as e:
            print(f"❌ Eroare: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
