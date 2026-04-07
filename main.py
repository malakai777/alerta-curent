import requests
from bs4 import BeautifulSoup
import pdfplumber
import io

# Configurare
URL_PAGINA = "https://www.reteleelectrice.ro/intreruperi/programate/"
STRADA_CAUTATA = "Putna"
LOCALITATE = "Otopeni"
TELEGRAM_TOKEN = "TOKEN_UL_TAU"
TELEGRAM_CHAT_ID = "ID_UL_TAU"

def trimite_alerta(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={mesaj}"
    requests.get(url)

def verifica_intreruperi():
    response = requests.get(URL_PAGINA)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Căutăm toate link-urile către PDF-uri
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link['href']
        # Filtrăm PDF-ul de Ilfov (verifică structura numelui fisierului pe site)
        if "Ilfov" in href and ".pdf" in href:
            pdf_url = href if href.startswith('http') else "https://www.reteleelectrice.ro" + href
            
            # Descarcă PDF-ul în memorie
            pdf_file = requests.get(pdf_url)
            with pdfplumber.open(io.BytesIO(pdf_file.content)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if STRADA_CAUTATA.lower() in text.lower() and LOCALITATE.lower() in text.lower():
                        trimite_alerta(f"⚠️ ATENȚIE! Strada {STRADA_CAUTATA} din {LOCALITATE} apare în lista de întreruperi: {pdf_url}")
                        return

if __name__ == "__main__":
    try:
        verifica_intreruperi()
    except Exception as e:
        print(f"Eroare: {e}")
