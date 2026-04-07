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
    # 1. URL-ul paginii de intreruperi
    url_pagina = "https://www.reteleelectrice.ro/intreruperi/programate/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url_pagina, headers=headers)
        # Cautam link-ul de Ilfov in codul sursa
        links = re.findall(r'href=[\'"]?([^\'" >]+Ilfov[^\'" >]+\.pdf)', res.text)
        
        if not links:
            trimite_alerta("❌ Nu am gasit link-ul PDF pe site. Verifica structura!")
            return

        pdf_url = links[0] if links[0].startswith('http') else "https://www.reteleelectrice.ro" + links[0]
        
        # 2. Descarcam PDF-ul
        pdf_res = requests.get(pdf_url, headers=headers)
        with pdfplumber.open(io.BytesIO(pdf_res.content)) as pdf:
            text_total = ""
            for page in pdf.pages:
                # Extragem textul si il curatam de caractere speciale
                p_text = page.extract_text() or ""
                text_total += p_text.lower() + " "
            
            # Curatam textul de semne de punctuatie si spatii extra
            text_total = re.sub(r'[^a-z0-9\s]', '', text_total)
            
            # 3. Cautare relaxata (cautam doar radacina "putna")
            # Am scos "otopeni" ca sa fim siguri ca nu ratam din cauza formatarii
            if "putna" in text_total:
                trimite_alerta(f"⚠️ ATENȚIE! Strada PUTNA a fost găsită în listă!\nLink PDF: {pdf_url}")
            else:
                trimite_alerta(f"✅ Verificare OK: Strada Putna nu apare în PDF-ul curent.\n(Am verificat aici: {pdf_url})")

    except Exception as e:
        trimite_alerta(f"❌ Eroare la citire: {str(e)}")

if __name__ == "__main__":
    verifica()
    
