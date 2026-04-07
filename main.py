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
            print(f"Pas 1: Navigăm la Planificate")
            await page.goto(URL_PLANIFICATE, wait_until="networkidle", timeout=60000)
            try: await page.click("#onetrust-accept-btn-handler", timeout=5000)
            except: pass

            now = datetime.now()
            luna_nume = ["Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", 
                         "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"][now.month - 1]

            # --- LOGICA DE FORȚARE A LUNII ---
            print(f"Pas 2: Încercăm să setăm luna {luna_nume}...")
            
            for incercare in range(3): # Încearcă de maxim 3 ori
                await page.locator('select[name="year"]').first.select_option(str(now.year))
                await page.wait_for_timeout(1000)
                await page.locator('select[name="month"]').first.select_option(label=luna_nume)
                await page.wait_for_timeout(1000)
                await page.locator('select[name="county"]').first.select_option(value="IF")
                await page.wait_for_timeout(2000)

                # Verificăm dacă selecția a rămas corectă
                luna_activa = await page.locator('select[name="month"]').first.evaluate("el => el.options[el.selectedIndex].text")
                if luna_activa == luna_nume:
                    print(f"✅ Succes! Luna a rămas setată pe {luna_nume}.")
                    break
                else:
                    print(f"⚠️ Tentativa {incercare + 1} eșuată (a sărit la {luna_activa}). Reîncercăm...")

            print("Pas 3: Apăsăm Caută")
            await page.locator("button:has-text('Caută')").first.click()
            await page.wait_for_timeout(10000)

            # Citim rezultatul final
            tabel_text = await page.inner_text("body")
            
            if ORAS_CAUTAT in tabel_text.upper() and STRADA_CAUTATA in tabel_text.upper():
                msg = f"📅 PLANIFICATĂ: Lucrare în Otopeni, Str. {STRADA_CAUTATA} detectată!"
                send_telegram_msg(msg)
                print("🚨 AM GĂSIT LUCRARE ÎN TABEL!")
            else:
                print(f"✅ Status: Nu sunt lucrări planificate pe {STRADA_CAUTATA} în {luna_nume}.")

        except Exception as e:
            print(f"❌ Eroare: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
