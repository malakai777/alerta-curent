import os
import requests

def trimite_alerta(mesaj):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": mesaj})

def verifica():
    # Link-ul pe care l-ai confirmat tu manual
    pdf_url = "https://www.reteleelectrice.ro/content/dam/retele-electrice/intreruperi/programate/2026/04/Ilfov.pdf"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }

    try:
        # Incercam sa vedem doar daca fisierul EXISTA si ce marime are
        r = requests.head(pdf_url, headers=headers, timeout=20)
        
        status = r.status_code
        lungime = r.headers.get('Content-Length', 'necunoscuta')
        tip = r.headers.get('Content-Type', 'necunoscut')

        if status == 200:
            trimite_alerta(f"✅ SUCES! Robotul poate vedea fișierul.\nMarime: {lungime} bytes\nTip: {tip}\nAcum incerc sa-l citesc...")
            # Daca status e 200, incercam descarcarea completa
            res_full = requests.get(pdf_url, headers=headers)
            if "putna" in res_full.text.lower(): # Cautare bruta in fluxul binar
                 trimite_alerta("⚠️ ATENTIE: Am gasit 'Putna' in codul sursa al PDF-ului!")
            else:
                 trimite_alerta("❌ Fisierul e vizibil, dar cautarea text a esuat. Trebuie alta metoda de citire.")
        else:
            trimite_alerta(f"🚫 BLOCAJ: Site-ul refuza accesul (Cod {status}).\nMotiv probabil: Protectie anti-bot sau regiune blocata.")

    except Exception as e:
        trimite_alerta(f"❌ Eroare la diagnostic: {str(e)}")

if __name__ == "__main__":
    verifica()
    
