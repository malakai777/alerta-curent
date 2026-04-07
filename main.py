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
    # 1. URL-ul paginii de baza
    url_pagina = "https://www.reteleelectrice.ro/intreruperi/programate/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url_pagina, headers=headers)
        # 2. Cautam link-ul de Ilfov (cel mai nou)
        links = re.findall(r'href=[\'"]?([^\'" >]+Ilfov[^\'" >]+\.pdf)', res.text)
        
        if not links:
            trimite_alerta("❌ Robotul nu a putut gasi link-ul PDF pe site. Verifica manual!")
            return

        pdf_url = links[0] if links[0].startswith('http') else "https://www.reteleelectrice.ro" + links[0]
        
        # 3. Descarcam si citim PDF-ul
        pdf_res = requests.get(pdf_url, headers=headers)
        with pdfplumber.open(io.BytesIO(pdf_res.content)) as pdf:
            gasit = False
            for page in pdf.pages:
                text = page.extract_text()
                if text and "putna" in text.lower():
                    gasit = True
                    break
            
            if gasit:
                trimite_alerta(f"⚠️ ATENȚIE! Strada Putna apare în tabelul de întreruperi!\nConsultă PDF-ul aici: {pdf_url}")
            else:
                # Mesaj de liniste (optional, il poti sterge daca vrei sa fie silentios cand e totul ok)
                trimite_alerta("✅ Verificare finalizată: Strada Putna NU apare în lista de întreruperi.")
                
    except Exception as e:
        trimite_alerta(f"❌ Eroare tehnica la rularea robotului: {str(e)}")

if __name__ == "__main__":
    verifica()
    
