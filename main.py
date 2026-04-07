import os
import requests
import pdfplumber
import io
from datetime import datetime

def trimite_alerta(mesaj):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": mesaj})

def verifica():
    # Pasul 1: Construim link-ul exact pe care l-ai confirmat tu
    acum = datetime.now()
    pdf_url = f"https://www.reteleelectrice.ro/content/dam/retele-electrice/intreruperi/programate/{acum.year}/{acum.strftime('%m')}/Ilfov.pdf"
    
    # Pasul 2: Ne "deghizăm" robotul ca să nu fie respins
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Referer': 'https://www.reteleelectrice.ro/intreruperi/programate/',
        'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }

    try:
        # Prima dată vizităm pagina principală ca să luăm "cookie-urile" de acces
        session.get("https://www.reteleelectrice.ro/intreruperi/programate/", headers=headers, timeout=20)
        
        # Acum încercăm să descărcăm PDF-ul folosind aceleași permisiuni
        response = session.get(pdf_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                # Extragem tot textul din toate paginile
                text_complet = ""
                for page in pdf.pages:
                    text_complet += (page.extract_text() or "") + "\n"
                
                # Curățăm textul pentru o căutare sigură
                text_final = " ".join(text_complet.lower().split())
                
                if "putna" in text_final:
                    trimite_alerta(f"⚠️ ALERTĂ CURENT: Strada PUTNA apare în PDF-ul de Aprilie!\nSursa: {pdf_url}")
                else:
                    trimite_alerta(f"✅ Verificare reușită: Strada Putna NU apare în PDF-ul scanat ({acum.strftime('%m/%Y')}).")
        else:
            # Dacă site-ul tot dă eroare, trimitem link-ul ca să verifici tu cu un click
            trimite_alerta(f"ℹ️ Robotul a fost blocat de site (Eroare {response.status_code}).\nVerifică manual aici: {pdf_url}")

    except Exception as e:
        trimite_alerta(f"❌ Eroare tehnică: {str(e)}")

if __name__ == "__main__":
    verifica()
    
