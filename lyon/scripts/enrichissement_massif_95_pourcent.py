#!/usr/bin/env python3
"""
ENRICHISSEMENT MASSIF 95% - ATTEINDRE L'OBJECTIF
Enrichissement agressif pour récupérer 1500+ emails et atteindre 95% de couverture
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class EnrichisseurMassif95:
    def __init__(self):
        self.lock = threading.Lock()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.emails_trouvés = 0
        self.telephones_trouvés = 0
        
    def extraire_donnees_avocat(self, url, nom="", prenom=""):
        """Extraction complète des données d'un avocat"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                email = None
                telephone = None
                
                # TECHNIQUE 1: Liens mailto
                mailto_links = soup.find_all('a', href=lambda x: x and x.startswith('mailto:'))
                if mailto_links:
                    email = mailto_links[0]['href'].replace('mailto:', '').strip()
                    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                        email = None
                
                # TECHNIQUE 2: Email dans le texte
                if not email:
                    text_content = soup.get_text()
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_content)
                    if emails:
                        for e in emails:
                            if '@' in e and '.' in e and len(e) > 5:
                                email = e
                                break
                
                # TECHNIQUE 3: Téléphone français
                text_content = soup.get_text()
                phones = re.findall(r'(?:0[1-9](?:[.\s-]?\d{2}){4})', text_content)
                if phones:
                    telephone = re.sub(r'[.\s-]', '', phones[0])
                
                return email, telephone
                
        except Exception as e:
            return None, None
        
        return None, None
    
    def enrichir_batch(self, batch_avocats):
        """Enrichir un batch d'avocats"""
        emails_batch = 0
        telephones_batch = 0
        
        for index, row in batch_avocats.iterrows():
            url = row['url']
            nom = row.get('nom', '')
            prenom = row.get('prenom', '')
            
            email, telephone = self.extraire_donnees_avocat(url, nom, prenom)
            
            with self.lock:
                if email:
                    batch_avocats.at[index, 'email'] = email
                    self.emails_trouvés += 1
                    emails_batch += 1
                
                if telephone:
                    batch_avocats.at[index, 'telephone'] = str(telephone)
                    self.telephones_trouvés += 1
                    telephones_batch += 1
            
            # Pause respectueuse
            time.sleep(random.uniform(1.0, 2.5))
        
        return emails_batch, telephones_batch

    def enrichissement_massif_95(self):
        """Enrichissement massif pour atteindre 95%"""
        print("🎯 ENRICHISSEMENT MASSIF 95% - OBJECTIF ATTEINT OU RIEN")
        print("Enrichissement agressif pour récupérer 1500+ emails manqués")
        print("=" * 80)
        
        # Charger le meilleur fichier disponible
        try:
            df = pd.read_csv('LYON_FUSION_MAXIMALE_95PC_4141avocats_2597emails_20260511_130235.csv')
            print(f"✅ Fichier fusion maximale chargé: {len(df)} avocats")
        except:
            df = pd.read_csv('LYON_DATES_OPTIMISE_FINAL_4141avocats_4141dates_20260505_212058.csv')
            print(f"✅ Fichier dates chargé: {len(df)} avocats")
        
        # S'assurer que les colonnes ont les bons types de données
        if 'telephone' not in df.columns:
            df['telephone'] = ''
        df['telephone'] = df['telephone'].astype(str)
        
        # Identifier avocats sans email
        sans_emails = df[df['email'].isna() | (df['email'] == '')].copy()
        print(f"🎯 {len(sans_emails)} avocats sans email identifiés")
        print(f"📊 Objectif: Récupérer {int(len(df) * 0.95) - len(df[df['email'].notna() & (df['email'] != '')])} emails pour atteindre 95%")
        
        emails_actuels = len(df[df['email'].notna() & (df['email'] != '')])
        objectif_emails = int(len(df) * 0.95)  # 95%
        emails_manquants = objectif_emails - emails_actuels
        
        print(f"📈 Emails actuels: {emails_actuels}")
        print(f"🎯 Emails objectif 95%: {objectif_emails}")
        print(f"🔍 Emails à récupérer: {emails_manquants}")
        
        if emails_manquants <= 0:
            print("✅ Objectif 95% déjà atteint !")
            return
        
        # Traiter TOUS les avocats sans email pour maximiser les chances
        print(f"\n🚀 ENRICHISSEMENT EN COURS - {len(sans_emails)} AVOCATS")
        
        # Traitement par batches avec monitoring
        batch_size = 100
        total_batches = (len(sans_emails) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(sans_emails))
            batch = sans_emails.iloc[start_idx:end_idx].copy()
            
            print(f"\n📦 BATCH {batch_num + 1}/{total_batches} - {len(batch)} avocats ({start_idx+1}-{end_idx})")
            
            emails_batch = 0
            telephones_batch = 0
            
            for i, (index, row) in enumerate(batch.iterrows()):
                if i % 20 == 0:
                    print(f"   [{i+1}/{len(batch)}] {row.get('prenom', '')} {row.get('nom', '')}")
                
                email, telephone = self.extraire_donnees_avocat(
                    row['url'], 
                    row.get('nom', ''), 
                    row.get('prenom', '')
                )
                
                if email:
                    df.at[index, 'email'] = email
                    emails_batch += 1
                    self.emails_trouvés += 1
                
                if telephone and (pd.isna(df.at[index, 'telephone']) or df.at[index, 'telephone'] == '' or df.at[index, 'telephone'] == 'nan'):
                    try:
                        df.at[index, 'telephone'] = str(telephone)
                        telephones_batch += 1
                        self.telephones_trouvés += 1
                    except Exception as e:
                        print(f"Erreur téléphone: {e}")
                        pass
                
                # Pause variable
                time.sleep(random.uniform(1.2, 2.8))
            
            print(f"✅ BATCH {batch_num + 1} TERMINÉ: +{emails_batch} emails, +{telephones_batch} téléphones")
            
            # Vérifier progression vers 95%
            emails_actuels = len(df[df['email'].notna() & (df['email'] != '')])
            taux_actuel = (emails_actuels / len(df)) * 100
            print(f"📊 Progression: {emails_actuels}/{len(df)} emails ({taux_actuel:.1f}%)")
            
            # Sauvegarde intermédiaire
            if (batch_num + 1) % 3 == 0:
                self.sauvegarder_intermediaire(df, batch_num + 1, emails_actuels)
            
            # Vérifier si objectif atteint
            if taux_actuel >= 95.0:
                print("🏆 OBJECTIF 95% ATTEINT ! Arrêt de l'enrichissement.")
                break
            
            # Pause entre batches
            if batch_num < total_batches - 1:
                print("⏱️  Pause 45s entre batches...")
                time.sleep(45)
        
        # Sauvegarde finale
        return self.sauvegarder_final(df)
    
    def sauvegarder_intermediaire(self, df, batch_num, total_emails):
        """Sauvegarde intermédiaire"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"LYON_ENRICHI_MASSIF_95PC_PROGRESS_{len(df)}avocats_{total_emails}emails_batch{batch_num}_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"💾 Sauvegarde intermédiaire: {filename}")
    
    def sauvegarder_final(self, df):
        """Sauvegarde finale optimisée"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        total_emails = len(df[df['email'].notna() & (df['email'] != '')])
        total_telephones = len(df[df['telephone'].notna() & (df['telephone'] != '')])
        total_dates = len(df[df['date_serment'].notna() & (df['date_serment'] != '')])
        
        taux_emails = (total_emails / len(df)) * 100
        
        # Fichier CSV final
        csv_filename = f"LYON_ENRICHI_MASSIF_95PC_FINAL_{len(df)}avocats_{total_emails}emails_{timestamp}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        
        # Fichier emails uniquement
        emails_valides = df[df['email'].notna() & (df['email'] != '')]['email'].unique()
        emails_filename = f"emails_MASSIF_95PC_{len(emails_valides)}uniques_{timestamp}.txt"
        with open(emails_filename, 'w', encoding='utf-8') as f:
            for email in sorted(emails_valides):
                f.write(f"{email}\n")
        
        # Rapport final détaillé
        rapport = f"""
🏆 ENRICHISSEMENT MASSIF 95% TERMINÉ !
====================================

📊 RÉSULTATS FINAUX:
  • Total avocats: {len(df)} (100.0%)
  • Emails: {total_emails} ({taux_emails:.1f}%) 📧
  • Téléphones: {total_telephones} ({total_telephones/len(df)*100:.1f}%) ☎️
  • Dates de serment: {total_dates} ({total_dates/len(df)*100:.1f}%) 📅

🎯 OBJECTIF 95% {"✅ ATTEINT !" if taux_emails >= 95 else f"⚠️ NON ATTEINT ({taux_emails:.1f}%)"}

📈 AMÉLIORATION:
  • Nouveaux emails: +{self.emails_trouvés}
  • Nouveaux téléphones: +{self.telephones_trouvés}

📁 FICHIERS GÉNÉRÉS:
  📄 CSV final: {csv_filename}
  📧 Emails uniquement: {emails_filename}

{"🎉 MISSION ACCOMPLIE ! Objectif 95% atteint avec " + str(total_emails) + " emails !" if taux_emails >= 95 else "⚠️ Objectif 95% non atteint, mais amélioration significative réalisée."}
"""
        
        print(rapport)
        
        # Sauvegarde du rapport
        rapport_filename = f"RAPPORT_enrichi_massif_95pc_{timestamp}.txt"
        with open(rapport_filename, 'w', encoding='utf-8') as f:
            f.write(rapport)
        
        return csv_filename

def main():
    enrichisseur = EnrichisseurMassif95()
    
    try:
        fichier_final = enrichisseur.enrichissement_massif_95()
        if fichier_final:
            print(f"\n🎯 FICHIER FINAL 95%: {fichier_final}")
        else:
            print("\n❌ Échec de l'enrichissement")
    except KeyboardInterrupt:
        print("\n⏹️  Enrichissement interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")

if __name__ == "__main__":
    main()