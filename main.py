import asyncio
import os
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# --- CONFIGURARE ---
POD_CODE = "RO001E143159840"
ORAS_CAUTAT = "OTOPENI"
STRADA_CAUTATA = "PUTNA"
URL_PRINCIPAL = "https://www.reteleelectrice.ro/intreruperi/"
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
            # --- PASUL 1: AVARII (POD) ---
            print(f"Pas 1: Verificare POD {POD_CODE}")
            await page.goto(URL_PRINCIPAL, wait_until="domcontentloaded", timeout=60000)
            
            try:
                await page.locator("input[name='getinfo_pod']").first.fill(POD_CODE)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(5000)
                content = await page.content()
                if "nu avem înregistrată nicio întrerupere" not in content.lower() and "nu sunt întreruperi" not in content.lower():
                    send_telegram_msg(f"🚨 ALERTĂ: Avarie detectată la POD {POD_CODE}!")
            except: print("⚠️ Verificarea POD a eșuat, trecem la planificate.")

            # --- PASUL 2: PLANIFICATE ---
            print("Pas 2: Verificare Planificate Otopeni")
            await page.goto(URL_PLANIFICATE, wait_until="networkidle", timeout=60000)
            
            now = datetime.now()
            # Forțăm selecția filtrelor prin JavaScript (mult mai stabil)
            await page.evaluate(f"""() => {{
                const y = document.querySelector('select[name="year"]');
                const m = document.querySelector('select[name="month"]');
                const c = document.querySelector('select[name="county"]');
                if(y) y.value = "{now.year}";
                if(m) m.value = "{now.month}";
                if(c) c.value = "IF";
                y?.dispatchEvent(new Event('change'));
                m?.dispatchEvent(new Event('change'));
                c?.dispatchEvent(new Event('change'));
            }}""")

            await page.wait_for_timeout(2000)
            # Click pe butonul de căutare
            try:
                await page.locator("button:has-text('Caută')").first.click()
                await page.wait_for_timeout(10000) # Timp generos pentru tabel
                
                tabel_text = await page.inner_text("body")
                if ORAS_CAUTAT in tabel_text.upper() and STRADA_CAUTATA in tabel_text.upper():
                    send_telegram_msg(f"📅 PLANIFICATĂ: Lucrare în Otopeni, Str. {STRADA_CAUTATA}!")
                    print("🚨 AM GĂSIT LUCRARE!")
                else:
                    print(f"✅ Status: Nu sunt lucrări planificate pe {STRADA_CAUTATA}.")
            except Exception as e:
                print(f"❌ Nu am putut apăsa butonul Caută: {e}")

        except Exception as e:
            print(f"❌ Eroare generală: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
