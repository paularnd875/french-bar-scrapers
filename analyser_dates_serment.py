#!/usr/bin/env python3
"""
ANALYSEUR DATES DE SERMENT - BARREAU DE LYON
Analyse les statistiques complètes des dates de serment dans le fichier final
"""

import pandas as pd
import re
from collections import Counter

def analyser_dates_serment():
    print("📊 ANALYSE COMPLÈTE DES DATES DE SERMENT")
    print("Barreau de Lyon - Fichier final")
    print("=" * 60)
    
    # Charger le fichier
    try:
        df = pd.read_csv('BARREAU_LYON_COMPLET_4141avocats_2593emails_20260505_165132.csv')
        print(f"✅ Fichier chargé: {len(df)} avocats")
    except FileNotFoundError:
        print("❌ Fichier non trouvé")
        return
    
    # Analyser la colonne date_serment
    total_avocats = len(df)
    dates_non_nulles = df[df['date_serment'].notna() & (df['date_serment'] != '')]
    dates_vides = df[df['date_serment'].isna() | (df['date_serment'] == '')]
    
    nb_dates = len(dates_non_nulles)
    nb_vides = len(dates_vides)
    
    print(f"\n📈 STATISTIQUES GÉNÉRALES:")
    print(f"  • Total avocats: {total_avocats}")
    print(f"  • Dates de serment trouvées: {nb_dates}")
    print(f"  • Dates manquantes: {nb_vides}")
    print(f"  • Taux de couverture: {(nb_dates/total_avocats)*100:.1f}%")
    
    if nb_dates > 0:
        print(f"\n📅 ANALYSE DES DATES TROUVÉES:")
        
        # Extraire les années
        dates_list = dates_non_nulles['date_serment'].tolist()
        annees = []
        
        for date in dates_list:
            if pd.notna(date) and str(date).strip():
                # Extraire l'année (4 chiffres)
                match = re.search(r'\b(19|20)\d{2}\b', str(date))
                if match:
                    annees.append(int(match.group()))
        
        if annees:
            annees_counter = Counter(annees)
            annees_triees = sorted(annees_counter.items())
            
            print(f"  • Années de serment trouvées: {len(set(annees))} différentes")
            print(f"  • Année la plus ancienne: {min(annees)}")
            print(f"  • Année la plus récente: {max(annees)}")
            
            print(f"\n📊 RÉPARTITION PAR DÉCENNIE:")
            decennies = {}
            for annee in annees:
                decennie = (annee // 10) * 10
                decennies[decennie] = decennies.get(decennie, 0) + 1
            
            for decennie in sorted(decennies.keys()):
                nb = decennies[decennie]
                pourcentage = (nb / len(annees)) * 100
                print(f"  • {decennie}s: {nb} avocats ({pourcentage:.1f}%)")
            
            print(f"\n📅 TOP 10 ANNÉES LES PLUS FRÉQUENTES:")
            for annee, nb in sorted(annees_counter.items(), key=lambda x: x[1], reverse=True)[:10]:
                pourcentage = (nb / len(annees)) * 100
                print(f"  • {annee}: {nb} avocats ({pourcentage:.1f}%)")
    
    # Échantillon de dates
    print(f"\n🔍 ÉCHANTILLON DE DATES TROUVÉES:")
    echantillon = dates_non_nulles['date_serment'].head(10).tolist()
    for i, date in enumerate(echantillon, 1):
        print(f"  {i}. {date}")
    
    # Échantillon de profils sans date
    if nb_vides > 0:
        print(f"\n❌ ÉCHANTILLON DE PROFILS SANS DATE (sur {nb_vides}):")
        vides_echantillon = dates_vides[['nom', 'prenom', 'url']].head(5)
        for i, (_, row) in enumerate(vides_echantillon.iterrows(), 1):
            print(f"  {i}. {row['nom']} {row['prenom']}")
            print(f"     URL: {row['url']}")
    
    # Résumé final
    print(f"\n🎯 RÉSUMÉ FINAL:")
    if (nb_dates/total_avocats)*100 >= 95:
        print("🏆 EXCELLENT taux de couverture des dates de serment !")
    elif (nb_dates/total_avocats)*100 >= 80:
        print("🎯 BON taux de couverture des dates de serment")
    elif (nb_dates/total_avocats)*100 >= 60:
        print("⚠️ Taux de couverture MOYEN")
    else:
        print("❌ Taux de couverture FAIBLE")
    
    print(f"📊 Base de données finale Barreau de Lyon:")
    print(f"  • 4141 avocats (100%)")
    print(f"  • {len(df[df['email'].notna() & (df['email'] != '')])} emails ({(len(df[df['email'].notna() & (df['email'] != '')])/total_avocats)*100:.1f}%)")
    print(f"  • {nb_dates} dates de serment ({(nb_dates/total_avocats)*100:.1f}%)")

if __name__ == "__main__":
    analyser_dates_serment()