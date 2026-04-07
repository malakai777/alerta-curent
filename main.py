import os
import requests
import pdfplumber
import io
import re

def trimite_alerta(mesaj):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": mesaj})

def verifica():
    # URL-ul unde stau "ascunse" link-urile de PDF
    url_pagina = "https://www.reteleelectrice.ro/intreruperi/programate/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        res = requests.get(url_pagina, headers=headers)
        # Căutăm orice link de tip PDF care conține "Ilfov" în tot codul paginii
        # Folosim o expresie regulată care găsește link-ul chiar dacă e îngropat în JavaScript
        matches = re.findall(r'/content/dam/retele-electrice/intreruperi/programate/[0-9/]+Ilfov\.pdf', res.text)
        
        if not matches:
            # Dacă nu găsește prin scanare, încercăm link-ul "prezis" pentru Aprilie 2026
            pdf_url = "https://www.reteleelectrice.ro/content/dam/retele-electrice/intreruperi/programate/2026/04/Ilfov.pdf"
        else:
            # Luăm ultimul link găsit (cel mai recent)
            pdf_url = "https://www.reteleelectrice.ro" + matches[-1]

        print(f"Verific PDF: {pdf_url}")
        
        pdf_res = requests.get(pdf_url, headers=headers)
        if pdf_res.status_code != 200:
            trimite_alerta(f"❌ Site-ul a blocat accesul la PDF sau link-ul s-a schimbat.\nÎncearcă manual: {pdf_url}")
            return

        with pdfplumber.open(io.BytesIO(pdf_res.content)) as pdf:
            found = False
            for page in pdf.pages:
                text = page.extract_text()
                # Căutare ultra-relaxată: doar cuvântul Putna
                if text and "putna" in text.lower():
                    found = True
                    break
            
            if found:
                trimite_alerta(f"⚠️ ATENȚIE! Strada PUTNA apare în PDF!\nSursa: {pdf_url}")
            else:
                trimite_alerta(f"✅ Verificare OK: Strada Putna NU apare în PDF-ul curent ({pdf_url.split('/')[-3]}/{pdf_url.split('/')[-2]}).")

    except Exception as e:
        trimite_alerta(f"❌ Eroare script: {str(e)}")

if __name__ == "__main__":
    verifica()
