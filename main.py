import asyncio
import os
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# --- CONFIGURARE ---
POD_CODE = "RO001E143159840"
ORAS_CAUTAT = "OTOPENI"
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
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 1000},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # --- PASUL 1: VERIFICARE AVARII (POD) ---
            print(f"Pas 1: Verificare POD {POD_CODE}")
            await page.goto(URL_PRINCIPAL, wait_until="domcontentloaded", timeout=60000)
            
            try: await page.click("#onetrust-accept-btn-handler", timeout=5000)
            except: pass

            input_pod = page.locator("input[name='getinfo_pod']").first
            await input_pod.fill(POD_CODE)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(7000)

            content = await page.content()
            if not any(key in content.lower() for key in ["nu avem înregistrată nicio întrerupere", "nu sunt întreruperi"]):
                if "deranjamente" in content.lower():
                    send_telegram_msg(f"🚨 ALERTĂ: Avarie curentă detectată la POD {POD_CODE}!")

            # --- PASUL 2: VERIFICARE PLANIFICATE ---
            print("Pas 2: Verificare Planificate (Navigare Directă)")
            await page.goto(URL_PLANIFICATE, wait_until="networkidle", timeout=60000)
            
            now = datetime.now()
            # REZOLVARE: Folosim .first sau selectoare ierarhice pentru a evita eroarea de "multiple elements"
            try:
                print(f"Selectăm filtrele pentru: {now.month}/{now.year}, Ilfov")
                
                # Selectăm Anul
                await page.locator("select[name='year']").first.select_option(str(now.year))
                # Selectăm Luna
                await page.locator("select[name='month']").first.select_option(str(now.month))
                # Selectăm Județul (IF = Ilfov)
                await page.locator("select[name='county']").first.select_option("IF")
                
                # Apăsăm butonul de Căutare (cel de lângă filtre)
                await page.locator("button:has-text('Caută')").first.click()
                await page.wait_for_timeout(7000)

                tabel_text = await page.inner_text("body")
                if ORAS_CAUTAT in tabel_text.upper() and "PUTNA" in tabel_text.upper():
                    send_telegram_msg(f"📅 PLANIFICATĂ: Lucrare detectată în Otopeni, Str. Putna!")
                else:
                    print(f"✅ Status: Nu sunt lucrări planificate în {ORAS_CAUTAT} pe strada ta.")
            
            except Exception as e:
                print(f"⚠️ Eroare la filtrare: {e}")

        except Exception as e:
            print(f"❌ Eroare generală: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
    send_telegram_msg(f"📅 PLANIFICATĂ: Lucrare detectată în Otopeni, Str. Putna!")
                else:
                    print("✅ Status: Nu sunt lucrări planificate pe strada ta.")
            except Exception as e:
                print(f"⚠️ Nu s-a putut filtra tabelul: {e}")

        except Exception as e:
            print(f"❌ Eroare generală: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
