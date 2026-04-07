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
    url_site = "https://www.reteleelectrice.ro/intreruperi/"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        page = await context.new_page()
        
        try:
            await page.goto(url_site, wait_until="networkidle")
            
            # Căutăm căsuța de POD
            input_selector = "input[placeholder*='POD']"
            await page.wait_for_selector(input_selector, timeout=15000)
            await page.fill(input_selector, pod)
            
            # Click pe butonul de trimitere
            await page.click("button:has-text('Trimite'), .btn-orange")
            
            # Așteptăm să apară rezultatul
            await asyncio.sleep(5)
            
            # Luăm textul de sub căsuța de căutare (unde apare de obicei răspunsul)
            # Extragem tot textul vizibil ca să fim siguri
            continut_text = await page.inner_text("body")
            
            # Curățăm textul să fie mai ușor de citit
            linii = [line.strip() for line in continut_text.split('\n') if len(line.strip()) > 5]
            rezultat_relevat = "\n".join(linii[:20]) # Luăm primele 20 de linii relevante

            trimite_telegram(f"🔍 Rezultat site pentru POD {pod}:\n\n{rezultat_relevat}")

        except Exception as e:
            trimite_telegram(f"❌ Robotul s-a blocat la introducerea POD-ului. Verifică manual: {url_site}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(verifica_pod())
    
