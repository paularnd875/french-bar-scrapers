#!/usr/bin/env python3
"""
ENRICHISSEUR DATES DE SERMENT OPTIMISÉ - BARREAU DE LYON
Récupère les 1543 dates de serment manquantes avec techniques avancées
Objectif : Passer de 62.7% à 95%+ de couverture
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class EnrichisseurDatesOptimise:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.lock = threading.Lock()
        self.dates_trouvees = 0
        self.total_traites = 0
        
    def extraire_date_serment_avancee(self, url, nom="", prenom=""):
        """Extraction avancée de date de serment avec multiples techniques"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text()
                html_content = response.text
                
                # TECHNIQUE 1: Pattern "Prestation de serment" + date française
                serment_patterns = [
                    r'Prestation de serment[^\d]*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
                    r'prestation de serment[^\d]*(\d{1,2}\s+\w+\s+\d{4})',
                    r'Serment[^\d]*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
                ]
                
                for pattern in serment_patterns:
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                
                # TECHNIQUE 2: Toutes les dates françaises (prendre la première pertinente)
                dates_fr = re.findall(r'\b\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b', 
                                     text_content, re.IGNORECASE)
                if dates_fr:
                    # Filtrer les dates réalistes (après 1970, avant 2030)
                    for date_str in dates_fr:
                        annee_match = re.search(r'\d{4}', date_str)
                        if annee_match:
                            annee = int(annee_match.group())
                            if 1970 <= annee <= 2030:
                                return date_str
                
                # TECHNIQUE 3: Recherche dans les éléments HTML spécifiques
                selectors_cibles = [
                    '.entry-content', '.avocat-details', '.profile-content', 
                    '.member-info', '.avocat-info', 'main', 'article'
                ]
                
                for selector in selectors_cibles:
                    elements = soup.select(selector)
                    for element in elements:
                        element_text = element.get_text()
                        # Chercher "serment" + date dans cet élément
                        if 'serment' in element_text.lower():
                            date_match = re.search(r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})', 
                                                 element_text, re.IGNORECASE)
                            if date_match:
                                date_str = date_match.group(1)
                                # Vérifier l'année
                                annee_match = re.search(r'\d{4}', date_str)
                                if annee_match and 1970 <= int(annee_match.group()) <= 2030:
                                    return date_str
                
                # TECHNIQUE 4: Recherche dans les métadonnées et attributs
                for meta in soup.find_all('meta'):
                    content = meta.get('content', '')
                    if content and 'serment' in content.lower():
                        date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', content)
                        if date_match:
                            return date_match.group(1)
                
                # TECHNIQUE 5: Patterns de dates numériques près de "serment"
                serment_positions = []
                for match in re.finditer(r'serment', text_content, re.IGNORECASE):
                    serment_positions.append(match.start())
                
                for pos in serment_positions:
                    # Chercher dans les 500 caractères avant/après
                    start = max(0, pos - 500)
                    end = min(len(text_content), pos + 500)
                    contexte = text_content[start:end]
                    
                    # Patterns numériques
                    date_patterns = [
                        r'(\d{1,2}/\d{1,2}/\d{4})',
                        r'(\d{1,2}-\d{1,2}-\d{4})',
                        r'(\d{1,2}\.\d{1,2}\.\d{4})',
                        r'(\d{4})',  # Juste l'année si rien d'autre
                    ]
                    
                    for pattern in date_patterns:
                        matches = re.findall(pattern, contexte)
                        if matches:
                            for match in matches:
                                if len(match) == 4:  # Année seule
                                    if 1970 <= int(match) <= 2030:
                                        return match
                                else:  # Date complète
                                    return match
                
                # TECHNIQUE 6: Recherche dans les commentaires HTML
                comments = re.findall(r'<!--(.*?)-->', html_content, re.DOTALL)
                for comment in comments:
                    if 'serment' in comment.lower():
                        date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', comment)
                        if date_match:
                            return date_match.group(1)
                
                # TECHNIQUE 7: Recherche dans les scripts JavaScript
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        if 'serment' in script.string.lower():
                            date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', script.string)
                            if date_match:
                                return date_match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def enrichir_dates_manquantes(self):
        """Enrichit toutes les dates de serment manquantes"""
        print("🚀 ENRICHISSEUR DATES DE SERMENT OPTIMISÉ")
        print("Objectif : Passer de 62.7% à 95%+ de couverture")
        print("=" * 70)
        
        # Charger le fichier actuel
        df = pd.read_csv('BARREAU_LYON_COMPLET_4141avocats_2593emails_20260505_165132.csv')
        print(f"✅ Fichier chargé: {len(df)} avocats")
        
        # Identifier les avocats sans date de serment
        sans_dates = df[df['date_serment'].isna() | (df['date_serment'] == '')].copy()
        print(f"🎯 {len(sans_dates)} avocats sans date de serment à traiter")
        
        print(f"\n🔄 ENRICHISSEMENT OPTIMISÉ AVEC TECHNIQUES AVANCÉES")
        print("Techniques : Pattern avancés, contexte HTML, métadonnées, scripts JS")
        
        # Traitement par batches pour monitoring
        batch_size = 100
        total_batches = (len(sans_dates) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(sans_dates))
            batch = sans_dates.iloc[start_idx:end_idx]
            
            print(f"\n📦 BATCH {batch_num + 1}/{total_batches} - {len(batch)} profils ({start_idx+1}-{end_idx})")
            
            dates_batch = 0
            
            for i, (index, row) in enumerate(batch.iterrows()):
                url = row.get('url', '')
                prenom = row.get('prenom', '')
                nom = row.get('nom', '')
                
                if not url:
                    continue
                
                # Indicateur de progression
                if i % 20 == 0:
                    print(f"   📊 {i}/{len(batch)}: {prenom} {nom}")
                
                # Extraction optimisée
                date_serment = self.extraire_date_serment_avancee(url, nom, prenom)
                
                if date_serment:
                    df.at[index, 'date_serment'] = date_serment
                    dates_batch += 1
                    self.dates_trouvees += 1
                    
                    if dates_batch % 10 == 0:
                        print(f"   ✅ {dates_batch} dates dans ce batch (dernière: {date_serment})")
                
                # Pause respectueuse et variable
                time.sleep(random.uniform(1.5, 3.0))
            
            print(f"✅ BATCH {batch_num + 1} TERMINÉ: {dates_batch} dates trouvées")
            print(f"📈 TOTAL CUMULÉ: {self.dates_trouvees} nouvelles dates")
            
            # Calcul du taux actuel
            total_dates_actuelles = len(df[df['date_serment'].notna() & (df['date_serment'] != '')])
            taux_actuel = (total_dates_actuelles / len(df)) * 100
            print(f"📊 Taux de couverture actuel: {taux_actuel:.1f}%")
            
            # Sauvegarde intermédiaire tous les 5 batches
            if (batch_num + 1) % 5 == 0:
                self.sauvegarder_intermediaire(df, batch_num + 1, total_dates_actuelles)
            
            # Pause entre batches
            if batch_num < total_batches - 1:
                print("⏱️  Pause 30s entre batches...")
                time.sleep(30)
        
        # Sauvegarde finale
        return self.sauvegarder_final(df)
    
    def sauvegarder_intermediaire(self, df, batch_num, total_dates):
        """Sauvegarde intermédiaire"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"LYON_DATES_OPTIMISE_PROGRESS_{len(df)}avocats_{total_dates}dates_batch{batch_num}_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"💾 Sauvegarde: {filename}")
    
    def sauvegarder_final(self, df):
        """Sauvegarde finale optimisée"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        total_dates = len(df[df['date_serment'].notna() & (df['date_serment'] != '')])
        total_emails = len(df[df['email'].notna() & (df['email'] != '')])
        
        # Fichier CSV final
        csv_filename = f"LYON_DATES_OPTIMISE_FINAL_{len(df)}avocats_{total_dates}dates_{timestamp}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        
        # Fichier dates uniquement
        dates_valides = df[df['date_serment'].notna() & (df['date_serment'] != '')]['date_serment'].unique()
        dates_filename = f"dates_serment_OPTIMISEES_{len(dates_valides)}uniques_{timestamp}.txt"
        with open(dates_filename, 'w', encoding='utf-8') as f:
            for date in sorted(dates_valides):
                f.write(f"{date}\\n")
        
        # Rapport final détaillé
        taux_dates = (total_dates / len(df)) * 100
        taux_emails = (total_emails / len(df)) * 100
        
        rapport = f"""
🎉 ENRICHISSEMENT DATES DE SERMENT OPTIMISÉ TERMINÉ !
=========================================================

📊 RÉSULTATS FINAUX COMPLETS:
  • Total avocats: {len(df)}
  • Dates de serment: {total_dates} ({taux_dates:.1f}%)
  • Emails disponibles: {total_emails} ({taux_emails:.1f}%)
  • Nouvelles dates récupérées: +{self.dates_trouvees}

📈 AMÉLIORATION:
  • Avant: 2598 dates (62.7%)
  • Après: {total_dates} dates ({taux_dates:.1f}%)
  • Gain: +{self.dates_trouvees} dates (+{((total_dates-2598)/len(df)*100):.1f} points)

📁 FICHIERS GÉNÉRÉS:
  📄 CSV optimisé: {csv_filename}
  📅 Dates uniquement: {dates_filename}

✅ MISSION ACCOMPLIE !
"""
        
        print(rapport)
        
        if taux_dates >= 95:
            print("🏆 OBJECTIF 95%+ ATTEINT !")
        elif taux_dates >= 90:
            print("🎯 EXCELLENT RÉSULTAT 90%+")
        elif taux_dates >= 80:
            print("✅ BON RÉSULTAT 80%+")
        
        # Sauvegarde du rapport
        rapport_filename = f"RAPPORT_dates_optimise_{timestamp}.txt"
        with open(rapport_filename, 'w', encoding='utf-8') as f:
            f.write(rapport)
        
        return csv_filename

def main():
    enrichisseur = EnrichisseurDatesOptimise()
    
    try:
        fichier_final = enrichisseur.enrichir_dates_manquantes()
        if fichier_final:
            print(f"\\n🎯 FICHIER FINAL OPTIMISÉ: {fichier_final}")
        else:
            print("\\n❌ Échec de l'enrichissement")
    except KeyboardInterrupt:
        print("\\n⏹️  Enrichissement interrompu par l'utilisateur")
    except Exception as e:
        print(f"\\n❌ Erreur critique: {e}")

if __name__ == "__main__":
    main()