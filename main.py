import os
import requests
import pdfplumber
import io
import re

def trimite_alerta(mesaj):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mesaj}
    r = requests.post(url, json=payload)
    print(f"DEBUG Telegram Status: {r.status_code}")

def verifica():
    print("--- START VERIFICARE AGRESIVĂ ---")
    url_pagina = "https://www.reteleelectrice.ro/intreruperi/programate/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url_pagina, headers=headers)
        # Găsim link-ul de Ilfov
        links = re.findall(r'href=[\'"]?([^\'" >]+Ilfov[^\'" >]+\.pdf)', res.text)
        
        if not links:
            trimite_alerta("❌ Robotul nu a găsit link-ul PDF pe site.")
            return

        pdf_url = links[0] if links[0].startswith('http') else "https://www.reteleelectrice.ro" + links[0]
        print(f"Citesc PDF-ul: {pdf_url}")

        pdf_res = requests.get(pdf_url, headers=headers)
        with pdfplumber.open(io.BytesIO(pdf_res.content)) as pdf:
            text_total = ""
            for page in pdf.pages:
                # Extragem textul și eliminăm spațiile multiple sau semnele ciudate
                raw_text = page.extract_text() or ""
                text_total += " " + raw_text.replace("\n", " ")

            # Curățăm textul: scoatem spațiile extra și facem litere mici
            text_curat = " ".join(text_total.split()).lower()
            
            # Căutăm "putna" - folosim re.search pentru siguranță
            if re.search(r'putna', text_curat):
                print("SUCCES: Strada Putna a fost găsită!")
                trimite_alerta(f"⚠️ ATENȚIE! Strada PUTNA apare în lista de întreruperi!\nLink PDF: {pdf_url}")
            else:
                print("NOT FOUND: Strada nu apare în textul extras.")
                # Trimitem acest mesaj DOAR pentru a confirma că botul e viu
                trimite_alerta("✅ Robotul a verificat PDF-ul și NU a găsit strada Putna. Totul e OK!")

    except Exception as e:
        print(f"EROARE: {str(e)}")
        trimite_alerta(f"❌ Eroare tehnică: {str(e)}")

if __name__ == "__main__":
    verifica()
    
