import os
import requests
import pdfplumber
import io
import datetime

def trimite_alerta(mesaj):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": mesaj})

def verifica():
    # Construim link-ul direct bazat pe data curenta
    # Structura este: .../an/luna/Ilfov.pdf (luna cu 0 in fata daca e sub 10)
    acum = datetime.datetime.now()
    an = acum.year
    luna = acum.strftime("%m")
    
    pdf_url = f"https://www.reteleelectrice.ro/content/dam/retele-electrice/intreruperi/programate/{an}/{luna}/Ilfov.pdf"
    
    print(f"Incerc sa descarc PDF-ul: {pdf_url}")

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(pdf_url, headers=headers)
        
        if response.status_code != 200:
            trimite_alerta(f"❌ Nu am putut accesa PDF-ul direct la adresa: {pdf_url}\nCod eroare: {response.status_code}")
            return

        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            gasit = False
            for page in pdf.pages:
                text = page.extract_text()
                # Cautam "putna" fara sa ne pese de litere mari/mici
                if text and "putna" in text.lower():
                    gasit = True
                    break
            
            if gasit:
                trimite_alerta(f"⚠️ ATENȚIE! Strada PUTNA apare în lista de întreruperi!\nVerifică aici: {pdf_url}")
            else:
                trimite_alerta(f"✅ Verificare OK: Strada Putna NU apare în PDF-ul de Ilfov ({luna}/{an}).")

    except Exception as e:
        trimite_alerta(f"❌ Eroare neprevazuta: {str(e)}")

if __name__ == "__main__":
    verifica()
    
