import os
import asyncio
from playwright.async_api import async_playwright
import requests

def trimite_telegram(mesaj):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": mesaj})

async def verifica_pod():
    pod = "RO001E110447409"
    # URL-ul corect indicat de tine
    url_site = "https://www.reteleelectrice.ro/intreruperi/"

    async with async_playwright() as p:
        # Lansăm browserul cu setări care să evite detectarea ca robot
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            print(f"Accesăm {url_site}...")
            await page.goto(url_site, wait_until="networkidle", timeout=60000)
            
            # Așteptăm să apară câmpul de căutare POD
            # Folosim un selector mai flexibil care caută după placeholder sau ID
            input_selector = "input[placeholder*='POD'], input#pod-search, .search-input"
            await page.wait_for_selector(input_selector, timeout=30000)
            
            # Introducem codul POD
            await page.fill(input_selector, pod)
            print(f"Am introdus POD: {pod}")
            
            # Apăsăm Enter pentru a căuta
            await page.keyboard.press("Enter")
            
            # Așteptăm ca site-ul să proceseze cererea și să afișeze rezultatul
            await asyncio.sleep(8)
            
            # Capturăm textul rezultat de pe pagină
            # Căutăm în zona unde site-ul afișează de obicei statusul (ex: "Nu sunt întreruperi")
            text_pagina = await page.content()
            text_pagina_lower = text_pagina.lower()

            if "nu sunt întreruperi" in text_pagina_lower or "nu există întreruperi" in text_pagina_lower:
                trimite_telegram(f"✅ POD {pod}: Verificare reușită. Nu sunt întreruperi active sau programate pe site.")
            elif "mentenanță" in text_pagina_lower or "planificată" in text_pagina_lower or "avarie" in text_pagina_lower:
                trimite_telegram(f"⚠️ ALERTĂ POD {pod}: Site-ul indică o întrerupere (planificată sau avarie)! Verifică aici: {url_site}")
            else:
                # Dacă textul nu conține nici confirmarea de OK, nici o eroare clară, trimitem un mesaj de verificare manuală
                trimite_telegram(f"ℹ️ Verificare POD {pod}: Rezultatul de pe site este neclar. Te rugăm să verifici manual: {url_site}")

        except Exception as e:
            trimite_telegram(f"❌ Robotul nu a putut finaliza verificarea pe noul URL. Motiv: Structura site-ului blochează accesul automat.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(verifica_pod())
    
