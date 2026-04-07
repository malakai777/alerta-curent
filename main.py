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
    # Luam data curenta pentru a "ghici" folderul
    acum = datetime.now()
    an = acum.year
    luna = acum.strftime("%m") # Va fi "04" pentru Aprilie
    
    # Aceasta este structura exacta de link pe care am vazut-o in pozele tale
    pdf_url = f"https://www.reteleelectrice.ro/content/dam/retele-electrice/intreruperi/programate/{an}/{luna}/Ilfov.pdf"
    
    print(f"Incerc descarcarea directa de la: {pdf_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/pdf'
    }

    try:
        response = requests.get(pdf_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + " "
                
                # Curatam textul de spatii extra si facem litere mici
                text_final = " ".join(full_text.split()).lower()
                
                if "putna" in text_final:
                    trimite_alerta(f"⚠️ ATENȚIE! Strada PUTNA a fost găsită în planificarea de Aprilie!\nSursa: {pdf_url}")
                else:
                    trimite_alerta(f"✅ Verificat: Strada Putna NU apare în PDF-ul de Ilfov pe luna {luna}/{an}.\nPDF scanat: {pdf_url}")
        else:
            # Daca e inceput de luna si folderul nu e inca creat
            trimite_alerta(f"ℹ️ Furnizorul nu a incarcat inca PDF-ul pentru {luna}/{an} la adresa standard.\nStatus: {response.status_code}")

    except Exception as e:
        trimite_alerta(f"❌ Eroare la procesarea PDF-ului: {str(e)}")

if __name__ == "__main__":
    verifica()
    
