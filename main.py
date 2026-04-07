import os
import requests
import pdfplumber
import io
from bs4 import BeautifulSoup
import datetime

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def trimite_alerta(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj}
    requests.post(url, json=payload)

def verifica():
    url_pagina = "https://www.reteleelectrice.ro/intreruperi/programate/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url_pagina, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Pasul 1: Găsim toate link-urile care duc la PDF-uri de Ilfov
    # Site-ul le listează de obicei pe toate, noi îl vrem pe cel mai nou
    links = [a['href'] for a in soup.find_all('a', href=True) if "Ilfov" in a['href']]
    
    if not links:
        print("Nu am găsit niciun PDF de Ilfov. Verifică dacă site-ul și-a schimbat structura.")
        return

    # Luăm primul link (de obicei cel de sus e cel mai recent)
    pdf_url = links[0] if links[0].startswith('http') else "https://www.reteleelectrice.ro" + links[0]
    print(f"Verific cel mai recent PDF găsit: {pdf_url}")

    # Pasul 2: Citim PDF-ul
    try:
        pdf_res = requests.get(pdf_url, headers=headers)
        with pdfplumber.open(io.BytesIO(pdf_res.content)) as pdf:
            found = False
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                # Căutăm strada Putna în Otopeni (case insensitive)
                if text and "putna" in text.lower() and "otopeni" in text.lower():
                    msg = f"⚠️ ALERTA CURENT OTOPENI!\nStrada Putna a fost găsită în planificarea de întreruperi.\nDetalii în PDF: {pdf_url}"
                    trimite_alerta(msg)
                    print(f"Am găsit strada la pagina {i+1}")
                    found = True
                    break # Ne oprim la prima găsire
            
            if not found:
                print("Strada Putna nu figurează în acest PDF.")
                # Opțional: trimite un mesaj de confirmare că scriptul a verificat dar e "curat"
                # trimite_alerta("✅ Verificare finalizată: Nicio întrerupere găsită pentru Strada Putna.")
                
    except Exception as e:
        print(f"Eroare la procesarea PDF-ului: {e}")

if __name__ == "__main__":
    verifica()
    
