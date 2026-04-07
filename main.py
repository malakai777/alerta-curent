import os
import requests
from bs4 import BeautifulSoup

def trimite_test_telegram(mesaj):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": mesaj})

# 1. TEST INSTANT TELEGRAM
print("Incerc sa trimit mesaj de test pe Telegram...")
trimite_test_telegram("🚀 Robotul a pornit! Daca primesti asta, conexiunea cu Telegram e OK.")

# 2. VERIFICARE SITE
url_pagina = "https://www.reteleelectrice.ro/intreruperi/programate/"
print(f"Accesez pagina: {url_pagina}")

res = requests.get(url_pagina, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(res.text, 'html.parser')

# Cautam orice link care are .pdf in el
toate_linkurile = soup.find_all('a', href=True)
pdf_links = [l['href'] for l in toate_linkurile if ".pdf" in l['href'].lower()]

print(f"Am gasit in total {len(toate_linkurile)} link-uri pe pagina.")
print(f"Dintre care {len(pdf_links)} sunt PDF-uri.")

if len(pdf_links) > 0:
    print("PDF-uri gasite:")
    for p in pdf_links:
        print(f" -> {p}")
else:
    print("NU AM GASIT PDF-URI. Pagina pare goala pentru robot.")
    # Daca e goala, printam primele 300 caractere din codul sursa pentru diagnostic
    print("Sursa HTML (primele 300 caractere):")
    print(res.text[:300])
    
