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
    pod = os.environ.get('COD_POD')
    url_site = "https://www.reteleelectrice.ro/intreruperi/programate/"

    async with async_playwright() as p:
        # Lansăm un browser invizibil
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Mergem pe site
            await page.goto(url_site, wait_until="networkidle")
            
            # Căutăm câmpul de căutare după POD (selectorul bazat pe placeholder)
            input_selector = "input[placeholder*='POD']"
            await page.wait_for_selector(input_selector, timeout=20000)
            
            # Scriem codul POD
            await page.fill(input_selector, pod)
            
            # Apăsăm Enter
            await page.keyboard.press("Enter")
            
            # Așteptăm câteva secunde să se încarce rezultatul interogării
            await asyncio.sleep(7)
            
            # Luăm textul de pe pagină după căutare
            continut = await page.content()
            
            # Verificăm dacă există mesaje de "nu sunt întreruperi"
            if "nu sunt întreruperi" in continut.lower() or "nu am găsit" in continut.lower():
                trimite_telegram(f"✅ POD {pod}: Nu sunt întreruperi programate identificate pe site.")
            else:
                # Dacă textul se schimbă, înseamnă că a găsit un tabel sau un mesaj de alertă
                trimite_telegram(f"⚠️ ATENȚIE! S-a găsit o modificare pe site pentru POD {pod}. Verifică urgent: {url_site}")

        except Exception as e:
            trimite_telegram(f"❌ Eroare la navigare: Site-ul este indisponibil sau structura s-a schimbat.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(verifica_pod())
  
