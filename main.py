import asyncio
import os
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# --- CONFIGURARE ---
POD_CODE = "RO001E143159840"
ORAS_CAUTAT = "OTOPENI"
STRADA_CAUTATA = "PUTNA"
URL_PLANIFICATE = "https://www.reteleelectrice.ro/intreruperi-planificate"
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
        context = await browser.new_context(viewport={'width': 1280, 'height': 1000})
        page = await context.new_page()

        try:
            print(f"Pas 1: Navigăm direct la Planificate")
            await page.goto(URL_PLANIFICATE, wait_until="networkidle", timeout=60000)
            
            # Acceptăm cookies rapid
            try: await page.click("#onetrust-accept-btn-handler", timeout=5000)
            except: pass

            # Determinăm luna curentă (ex: Aprilie)
            now = datetime.now()
            luna_nume = ["Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", 
                         "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"][now.month - 1]

            print(f"Pas 2: Selectăm filtrele pentru {luna_nume} {now.year}")

            # Click pe An și selectăm
            await page.locator('select[name="year"]').first.select_option(str(now.year))
            await page.wait_for_timeout(1000)

            # Click pe Lună și selectăm luna curentă
            # Folosim label-ul (textul vizibil) pentru a fi siguri
            await page.locator('select[name="month"]').first.select_option(label=luna_nume)
            await page.wait_for_timeout(1000)

            # Click pe Județ și selectăm Ilfov
            await page.locator('select[name="county"]').first.select_option(value="IF")
            await page.wait_for_timeout(1000)

            print("Pas 3: Apăsăm Caută")
            # Căutăm butonul de căutare care aparține de filtre
            await page.locator("button:has-text('Caută')").first.click()
            
            # Așteptare lungă pentru ca tabelul să se actualizeze
            print("Așteptăm rezultatele...")
            await page.wait_for_timeout(10000)

            # Verificăm dacă tabelul conține datele noastre
            tabel_text = await page.inner_text("body")
            
            # Debug: printăm ce lună vede robotul în pagină acum
            if luna_nume.lower() in tabel_text.lower():
                print(f"✅ Robotul confirmă că vede date pentru luna {luna_nume}.")
            else:
                print(f"⚠️ Atenție: Site-ul pare să fi rămas pe o altă lună.")

            if ORAS_CAUTAT in tabel_text.upper() and STRADA_CAUTATA in tabel_text.upper():
                msg = f"📅 PLANIFICATĂ: Lucrare în Otopeni, Str. {STRADA_CAUTATA} detectată!"
                send_telegram_msg(msg)
                print("🚨 LUCRARE GĂSITĂ!")
            else:
                print(f"✅ Status: Nu sunt lucrări planificate pe {STRADA_CAUTATA} în {luna_nume}.")

        except Exception as e:
            print(f"❌ Eroare: {e}")
            await page.screenshot(path="eroare_planificate.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
