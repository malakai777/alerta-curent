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
    # Robotul selecteaza automat ANUL si LUNA curenta
    acum = datetime.datetime.now()
    an = acum.year
    luna = acum.strftime("%m") # Aprilie va fi "04"
    
    # Construim link-ul direct pe care il genereaza site-ul dupa selectia ta
    pdf_url = f"https://www.reteleelectrice.ro/content/dam/retele-electrice/intreruperi/programate/{an}/{luna}/Ilfov.pdf"
    
    print(f"DEBUG: Incerc sa descarc PDF-ul pentru {luna}/{an}: {pdf_url}")

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(pdf_url, headers=headers)
        
        # Daca PDF-ul exista (Status 200)
        if response.status_code == 200:
            with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                gasit = False
                for page in pdf.pages:
                    text = page.extract_text()
                    # Verificam daca apare "Putna" in textul paginii
                    if text and "putna" in text.lower():
                        gasit = True
                        break
                
                if gasit:
                    trimite_alerta(f"⚠️ ATENȚIE! Strada PUTNA apare în lista de întreruperi pe {luna}/{an}!\nDetalii PDF: {pdf_url}")
                else:
                    trimite_alerta(f"✅ Verificare OK: Strada Putna NU este pe lista în PDF-ul de Ilfov ({luna}/{an}).")
        else:
            # Daca luna s-a schimbat dar PDF-ul nou nu a aparut inca
            trimite_alerta(f"ℹ️ PDF-ul pentru luna {luna}/{an} nu a fost inca incarcat de furnizor.")

    except Exception as e:
        trimite_alerta(f"❌ Eroare tehnica: {str(e)}")

if __name__ == "__main__":
    verifica()
    
