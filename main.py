import os
import asyncio
from playwright.async_api import async_playwright
import requests

def trimite_telegram_cu_poza(mesaj, poza_path):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    # Trimitem textul
    url_text = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url_text, json={"chat_id": chat_id, "text": mesaj})
    
    # Trimitem poza
    url_poza = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(poza_path, "rb") as photo:
        requests.post(url_poza, data={"chat_id": chat_id}, files={"photo": photo})

async def verifica_pod():
    pod = "RO001E110447409"
    url_site = "https://www.reteleelectrice.ro/intreruperi/"
    poza_rezultat = "rezultat_pod.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Ne dăm drept un iPhone ca să primim varianta mobilă a site-ului (mai simplă)
        context = await browser.new_context(
            viewport={'width': 375, 'height': 812},
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
        )
        page = await context.new_page()
        
        try:
            print(f"Deschidem pagina...")
            await page.goto(url_site, wait_until="networkidle", timeout=60000)
            
            # Așteptăm căsuța de POD
            input_selector = "input[placeholder*='POD']"
            await page.wait_for_selector(input_selector, timeout=20000)
            
            # Scriem POD-ul
            await page.fill(input_selector, pod)
            
            # Apăsăm butonul "Trimite" (cel portocaliu din poza ta)
            await page.click("button:has-text('Trimite'), .btn-orange, input[type='submit']")
            
            # Așteptăm să se schimbe ceva pe ecran
            await asyncio.sleep(10)
            
            # Facem poza la ecranul cu rezultatul
            await page.screenshot(path=poza_rezultat, full_page=True)
            
            # Extragem textul vizibil pentru log
            text_rezultat = await page.inner_text("body")
            
            mesaj = f"📸 Iată ce am găsit pe site pentru POD {pod}:"
            trimite_telegram_cu_poza(mesaj, poza_rezultat)

        except Exception as e:
            # Dacă dă eroare, facem o poză la unde s-a blocat
            await page.screenshot(path="eroare.png")
            trimite_telegram_cu_poza(f"❌ Robotul s-a blocat. Vezi în poză unde era:", "eroare.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(verifica_pod())
    
