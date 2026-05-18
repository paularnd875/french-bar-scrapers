#!/usr/bin/env python3
"""
ENRICHISSEMENT SIMPLE DIRECT - Récupérer les emails manquants
Approche simple : partir de notre base de 2597 emails et récupérer les emails manquants
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime

def enrichir_emails_manquants():
    print("🎯 ENRICHISSEMENT SIMPLE DIRECT - Récupérer les emails manquants")
    print("=" * 70)
    
    # Charger notre fichier de base avec 2597 emails
    fichier_base = 'LYON_FUSION_MAXIMALE_95PC_4141avocats_2597emails_20260511_172929.csv'
    
    try:
        df = pd.read_csv(fichier_base)
        print(f"✅ Fichier de base chargé: {len(df)} avocats")
        
        emails_actuels = len(df[df['email'].notna() & (df['email'] != '')])
        print(f"📧 Emails actuels: {emails_actuels}")
        
    except FileNotFoundError:
        print("❌ Fichier de base non trouvé")
        return None
    
    # Identifier les avocats sans email
    sans_emails = df[df['email'].isna() | (df['email'] == '')].copy()
    print(f"🎯 {len(sans_emails)} avocats sans email à traiter")
    
    if len(sans_emails) == 0:
        print("✅ Tous les emails sont déjà présents !")
        return None
    
    # Configuration session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    emails_trouvés = 0
    
    print(f"\\n🚀 DÉMARRAGE ENRICHISSEMENT - {len(sans_emails)} avocats à traiter")
    print(f"Objectif: Passer de {emails_actuels} emails à 95%+ (3933+ emails)")
    
    for i, (index, row) in enumerate(sans_emails.iterrows()):
        nom_complet = f"{row['prenom']} {row['nom']}"
        
        print(f"\\n[{i+1}/{len(sans_emails)}] {nom_complet}")
        print(f"    URL: {row['url']}")
        
        try:
            response = session.get(row['url'], timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Technique 1: Liens mailto
                email_trouve = None
                mailto_links = soup.find_all('a', href=lambda x: x and x.startswith('mailto:'))
                
                if mailto_links:
                    email_brut = mailto_links[0]['href'].replace('mailto:', '').strip()
                    # Nettoyer l'email
                    if '@' in email_brut and '.' in email_brut and len(email_brut) > 5:
                        email_trouve = email_brut.split('?')[0]  # Enlever les paramètres
                
                # Technique 2: Email dans le texte si pas trouvé
                if not email_trouve:
                    texte_complet = soup.get_text()
                    emails_regex = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}', texte_complet)
                    
                    for email_candidat in emails_regex:
                        if '@' in email_candidat and '.' in email_candidat and len(email_candidat) > 5:
                            # Éviter les emails générique/inutiles
                            if not any(mot in email_candidat.lower() for mot in ['noreply', 'no-reply', 'example', 'test']):
                                email_trouve = email_candidat
                                break
                
                # Sauvegarder l'email trouvé
                if email_trouve:
                    df.at[index, 'email'] = email_trouve
                    emails_trouvés += 1
                    print(f"    ✅ Email: {email_trouve}")
                    
                    # Sauvegarde intermédiaire tous les 50
                    if emails_trouvés % 50 == 0:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        temp_file = f'LYON_ENRICHI_PROGRESS_{len(df)}avocats_{emails_actuels + emails_trouvés}emails_{timestamp}.csv'
                        df.to_csv(temp_file, index=False, encoding='utf-8')
                        print(f"    💾 Sauvegarde: +{emails_trouvés} emails")
                        
                else:
                    print(f"    ❌ Aucun email trouvé")
                    
            else:
                print(f"    ❌ Erreur HTTP {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Erreur: {str(e)[:50]}")
        
        # Pause respectueuse
        time.sleep(2)
        
        # Affichage progression
        if (i + 1) % 100 == 0:
            taux_actuel = ((emails_actuels + emails_trouvés) / len(df)) * 100
            print(f"\\n📊 PROGRESSION: {emails_trouvés} nouveaux emails trouvés")
            print(f"    Total: {emails_actuels + emails_trouvés}/{len(df)} ({taux_actuel:.1f}%)")
            
            if taux_actuel >= 95:
                print("🏆 OBJECTIF 95% ATTEINT ! Arrêt de l'enrichissement.")
                break
    
    # Sauvegarde finale
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    total_emails_final = emails_actuels + emails_trouvés
    taux_final = (total_emails_final / len(df)) * 100
    
    fichier_final = f'LYON_ENRICHI_DIRECT_{len(df)}avocats_{total_emails_final}emails_{timestamp}.csv'
    df.to_csv(fichier_final, index=False, encoding='utf-8')
    
    # Fichier emails uniquement
    emails_uniques = df[df['email'].notna() & (df['email'] != '')]['email'].unique()
    emails_filename = f'emails_DIRECT_{len(emails_uniques)}uniques_{timestamp}.txt'
    with open(emails_filename, 'w', encoding='utf-8') as f:
        for email in sorted(emails_uniques):
            f.write(f"{email}\\n")
    
    # Rapport final
    rapport = f"""
🎉 ENRICHISSEMENT SIMPLE DIRECT TERMINÉ !
======================================

📊 RÉSULTATS:
  • Emails de départ: {emails_actuels}
  • Nouveaux emails trouvés: +{emails_trouvés}
  • Total final: {total_emails_final} emails
  • Taux final: {taux_final:.1f}%

📁 FICHIERS CRÉÉS:
  📄 CSV principal: {fichier_final}
  📧 Emails uniquement: {emails_filename}

{"🏆 OBJECTIF 95% ATTEINT !" if taux_final >= 95 else f"📈 Progression vers 95% (manque {int(len(df) * 0.95) - total_emails_final} emails)"}
"""
    
    print(rapport)
    
    with open(f'RAPPORT_enrichissement_direct_{timestamp}.txt', 'w', encoding='utf-8') as f:
        f.write(rapport)
    
    return fichier_final

if __name__ == "__main__":
    enrichir_emails_manquants()