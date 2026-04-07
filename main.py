import os
import requests
import pdfplumber
import io
import re

def trimite_alerta(mesaj):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": mesaj})
    print(f"DEBUG Telegram: {r.status_code}")

def verifica():
    print("--- START VERIFICARE ---")
    # Trimitem un test sa fim siguri ca botul merge
    trimite_alerta("🤖 Verificarea a început pentru strada Putna!")

    url_pagina = "https://www.reteleelectrice.ro/intreruperi/programate/"
    res = requests.get(url_pagina, headers={'User-Agent': 'Mozilla/5.0'})
    
    # Folosim REGEX ca sa gasim link-uri de Ilfov chiar daca sunt in JavaScript
    links = re.findall(r'href=[\'"]?([^\'" >]+Ilfov[^\'" >]+\.pdf)', res.text)
    
    if not links:
        print("Nu am gasit link-uri prin Regex. Incerc metoda clasica...")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True) if "Ilfov" in a['href']]

    if not links:
        trimite_alerta("❌ Nu am putut găsi link-ul PDF pe site. Structura s-a schimbat!")
        return

    pdf_url = links[0] if links[0].startswith('http') else "https://www.reteleelectrice.ro" + links[0]
    print(f"Citesc PDF: {pdf_url}")

    pdf_res = requests.get(pdf_url)
    with pdfplumber.open(io.BytesIO(pdf_res.content)) as pdf:
        found = False
        for page in pdf.pages:
            text = page.extract_text()
            if text and "putna" in text.lower() and "otopeni" in text.lower():
                trimite_alerta(f"⚠️ URGENȚĂ! Strada Putna (Otopeni) găsită în PDF!\nSursa: {pdf_url}")
                found = True
                break
        
        if not found:
            trimite_alerta("✅ Verificare completă: Strada Putna nu este afectată mâine.")

# ACEASTA ESTE LINIA CRITICA:
if __name__ == "__main__":
    verifica()
    
