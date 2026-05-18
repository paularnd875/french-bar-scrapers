#!/usr/bin/env python3
"""
ENRICHISSEMENT IMMÉDIAT - Récupération de 100+ emails supplémentaires
Travail direct sur le fichier avec 100% dates de serment pour enrichir les emails manquants
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

def enrichissement_immediat():
    print('🚀 ENRICHISSEMENT IMMÉDIAT - Récupération de 100+ emails supplémentaires')
    print('Travail sur les avocats sans email du fichier avec 100% dates de serment')
    print('=' * 80)

    # Charger le fichier avec 100% dates de serment
    df = pd.read_csv('LYON_DATES_OPTIMISE_FINAL_4141avocats_4141dates_20260505_212058.csv')
    print(f'✅ {len(df)} avocats chargés')

    # Identifier avocats sans email
    sans_emails = df[df['email'].isna() | (df['email'] == '')].head(200)  # Prendre 200 pour être sûr
    print(f'🎯 {len(sans_emails)} avocats sans email identifiés')

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    emails_trouvés = 0
    telephones_trouvés = 0
    
    print(f"\\n🔄 ENRICHISSEMENT EN COURS...")
    
    for i, (index, row) in enumerate(sans_emails.iterrows()):
        nom_complet = f"{row['prenom']} {row['nom']}"
        print(f'\\n[{i+1}/{len(sans_emails)}] {nom_complet}')
        print(f'    URL: {row["url"]}')
        
        try:
            response = session.get(row['url'], timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Recherche d'email
                mailto_links = soup.find_all('a', href=lambda x: x and x.startswith('mailto:'))
                email_trouve = False
                
                if mailto_links:
                    email = mailto_links[0]['href'].replace('mailto:', '').strip()
                    if '@' in email and '.' in email:  # Validation basique
                        df.at[index, 'email'] = email
                        emails_trouvés += 1
                        email_trouve = True
                        print(f'    ✅ Email: {email}')
                
                # Recherche de téléphone
                text_content = soup.get_text()
                import re
                phones = re.findall(r'(?:0[1-9](?:[. -]?[0-9]{2}){4})', text_content)
                if phones and pd.isna(df.at[index, 'telephone']):
                    phone = phones[0].replace(' ', '').replace('.', '').replace('-', '')
                    df.at[index, 'telephone'] = phone
                    telephones_trouvés += 1
                    print(f'    ✅ Téléphone: {phone}')
                
                if not email_trouve:
                    print(f'    ❌ Pas d\\'email trouvé')
            else:
                print(f'    ❌ Erreur HTTP {response.status_code}')
        except Exception as e:
            print(f'    ❌ Erreur: {str(e)[:50]}')
        
        # Pause respectueuse
        if i < len(sans_emails) - 1:  # Pas de pause après le dernier
            time.sleep(2)
        
        # Sauvegarde intermédiaire tous les 50
        if (i + 1) % 50 == 0:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_filename = f'TEMP_ENRICHI_IMMEDIAT_{len(df)}avocats_progress_{i+1}_{timestamp}.csv'
            df.to_csv(temp_filename, index=False, encoding='utf-8')
            print(f'    💾 Sauvegarde intermédiaire: {temp_filename}')

    print(f'\\n📊 RÉSULTATS ENRICHISSEMENT IMMÉDIAT:')
    print(f'  • Nouveaux emails: {emails_trouvés}')
    print(f'  • Nouveaux téléphones: {telephones_trouvés}')

    # Sauvegarde finale
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    total_emails = len(df[df['email'].notna() & (df['email'] != '')])
    total_telephones = len(df[df['telephone'].notna() & (df['telephone'] != '')])
    
    filename = f'LYON_ENRICHI_IMMEDIAT_{len(df)}avocats_{total_emails}emails_{timestamp}.csv'
    df.to_csv(filename, index=False, encoding='utf-8')
    
    # Fichier emails seulement
    emails_uniques = df[df['email'].notna() & (df['email'] != '')]['email'].unique()
    emails_filename = f'emails_IMMEDIAT_{len(emails_uniques)}uniques_{timestamp}.txt'
    with open(emails_filename, 'w', encoding='utf-8') as f:
        for email in sorted(emails_uniques):
            f.write(f"{email}\\n")

    print(f'\\n💾 FICHIERS CRÉÉS:')
    print(f'  📄 CSV principal: {filename}')
    print(f'  📧 Emails uniquement: {emails_filename}')
    
    print(f'\\n📈 STATISTIQUES FINALES:')
    print(f'  • Total emails: {total_emails}/{len(df)} ({total_emails/len(df)*100:.1f}%)')
    print(f'  • Total téléphones: {total_telephones}/{len(df)} ({total_telephones/len(df)*100:.1f}%)')
    
    if total_emails > 2593:
        gain = total_emails - 2593
        print(f'\\n🎉 AMÉLIORATION: +{gain} emails par rapport aux 2593 précédents !')
    
    return filename

if __name__ == "__main__":
    enrichissement_immediat()