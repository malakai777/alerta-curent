import os
import asyncio
from playwright.async_api import async_playwright
import requests

def trimite_telegram(mesaj):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": mesaj}, timeout=10)
    except Exception as e:
        print(f"Eroare trimitere Telegram: {e}")

async def verifica_pod():
    # Datele tale de identificare
    pod_client = "RO001E110447409"
    url_site = "https://www.reteleelectrice.ro/intreruperi/"

    async with async_playwright() as p:
        # Lansăm browser-ul
        browser = await p.chromium.launch(headless=True)
        # Ne dăm drept un browser normal de Windows
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            print(f"Pas 1: Deschidem {url_site}")
            await page.goto(url_site, wait_until="networkidle", timeout=60000)
            
            # Pas 2: Găsim căsuța de POD
            # Folosim un selector care caută input-ul după placeholder
            input_selector = "input[placeholder*='POD']"
            await page.wait_for_selector(input_selector, timeout=20000)
            await page.fill(input_selector, pod_client)
            print(f"Pas 2: Am introdus POD-ul {pod_client}")
            
            # Pas 3: Click pe butonul portocaliu (Trimite)
            # Căutăm butonul după textul "Trimite"
            await page.click("button:has-text('Trimite'), .btn-orange")
            print("Pas 3: Am apăsat butonul de verificare.")
            
            # Pas 4: Așteptăm rezultatul (site-ul procesează cererea)
            await asyncio.sleep(10)
            
            # Pas 5: Citim ce scrie pe ecran
            # Luăm tot textul vizibil din pagină
            text_pagina = await page.inner_text("body")
            text_lower = text_pagina.lower()
            
            # Analizăm răspunsul
            if "nu sunt întreruperi" in text_lower or "nu există întreruperi" in text_lower:
                rezultat = f"✅ [VERIFICARE ACTIVĂ POD]\nCod: {pod_client}\nStatus: Totul este în regulă. Nu sunt întreruperi programate sau avarii găsite pentru acest cod."
            elif "mentenanță" in text_lower or "planificată" in text_lower or "avarie" in text_lower:
                rezultat = f"⚠️ [ALERTA CURENT]\nCod: {pod_client}\nStatus: ATENȚIE! Site-ul indică o lucrare sau o avarie în zona ta.\nVerifică detalii aici: {url_site}"
            else:
                # Dacă site-ul returnează altceva (ex: eroare de sistem)
                rezultat = f"ℹ️ [INFO POD]\nCod: {pod_client}\nRezultatul de pe site este neclar sau s-a schimbat formatul. Te rugăm să verifici manual: {url_site}"

            trimite_telegram(rezultat)

        except Exception as e:
            trimite_telegram(f"❌ [EROARE ROBOT]\nRobotul s-a blocat la navigare. Site-ul furnizorului ar putea fi picat sau blocat.\nDetalii: {str(e)}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(verifica_pod())
    
