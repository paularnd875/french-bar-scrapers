#!/usr/bin/env python3
"""
FUSION MAXIMALE 95%+ - MATCHER TOUS LES FICHIERS DISPONIBLES
Combine TOUS les fichiers CSV disponibles pour atteindre 95%+ d'emails
"""

import pandas as pd
import glob
from datetime import datetime
import os

def fusion_maximale_95_pourcent():
    print("🎯 FUSION MAXIMALE 95%+ - MATCHER TOUS LES FICHIERS")
    print("Objectif : Combiner TOUS les CSV disponibles pour récupérer le maximum d'emails")
    print("=" * 80)
    
    # Fichier de base avec 100% dates de serment
    fichier_base = 'LYON_DATES_OPTIMISE_FINAL_4141avocats_4141dates_20260505_212058.csv'
    
    try:
        df_master = pd.read_csv(fichier_base)
        print(f"✅ Fichier master chargé: {len(df_master)} avocats, 100% dates de serment")
    except FileNotFoundError:
        # Fallback sur le fichier de base
        fichier_base = 'BARREAU_LYON_COMPLET_4141avocats_2593emails_20260505_165132.csv'
        df_master = pd.read_csv(fichier_base)
        print(f"✅ Fichier fallback chargé: {len(df_master)} avocats")
    
    # Trouver TOUS les fichiers CSV avec des emails
    patterns = [
        "*LYON*.csv",
        "*ENRICHI*.csv", 
        "*BARREAU*.csv",
        "*emails*.csv",
        "*avocats*.csv"
    ]
    
    fichiers_sources = []
    for pattern in patterns:
        fichiers = glob.glob(pattern)
        fichiers_sources.extend(fichiers)
    
    # Éliminer les doublons
    fichiers_sources = list(set(fichiers_sources))
    # Retirer le fichier master pour éviter la duplication
    fichiers_sources = [f for f in fichiers_sources if f != fichier_base]
    
    print(f"\n📁 FICHIERS SOURCES TROUVÉS ({len(fichiers_sources)}):")
    
    # Analyser chaque fichier source
    sources_valides = []
    for fichier in fichiers_sources:
        try:
            df_temp = pd.read_csv(fichier)
            if 'email' in df_temp.columns and 'url' in df_temp.columns:
                emails_count = len(df_temp[df_temp['email'].notna() & (df_temp['email'] != '')])
                if emails_count > 100:  # Seulement les fichiers avec plus de 100 emails
                    sources_valides.append({
                        'fichier': fichier,
                        'emails': emails_count,
                        'total': len(df_temp),
                        'taux': f"{emails_count/len(df_temp)*100:.1f}%"
                    })
                    print(f"  ✅ {fichier}: {emails_count} emails ({emails_count/len(df_temp)*100:.1f}%)")
                else:
                    print(f"  ⚠️ {fichier}: Seulement {emails_count} emails (ignoré)")
            else:
                print(f"  ❌ {fichier}: Pas de colonnes email/url")
        except Exception as e:
            print(f"  ❌ {fichier}: Erreur - {str(e)[:50]}")
    
    # Trier par nombre d'emails décroissant
    sources_valides.sort(key=lambda x: x['emails'], reverse=True)
    
    print(f"\n🔄 FUSION EN COURS - {len(sources_valides)} fichiers sources...")
    
    # Compteurs de fusion
    emails_fusionnes = 0
    telephones_fusionnes = 0
    specialisations_fusionnees = 0
    structures_fusionnees = 0
    adresses_fusionnees = 0
    
    # Fusionner chaque fichier source
    for i, source in enumerate(sources_valides, 1):
        fichier = source['fichier']
        print(f"\n📦 [{i}/{len(sources_valides)}] Fusion de: {fichier}")
        print(f"    📧 {source['emails']} emails disponibles")
        
        try:
            df_source = pd.read_csv(fichier)
            emails_ajoutés_ce_fichier = 0
            
            # Fusionner par URL
            for index, row_master in df_master.iterrows():
                url_master = row_master['url']
                
                # Trouver la ligne correspondante dans le fichier source
                matching_rows = df_source[df_source['url'] == url_master]
                
                if not matching_rows.empty:
                    row_source = matching_rows.iloc[0]
                    
                    # Email (priorité absolue)
                    if 'email' in df_source.columns:
                        if (pd.isna(df_master.at[index, 'email']) or df_master.at[index, 'email'] == '') and \
                           (pd.notna(row_source['email']) and str(row_source['email']).strip() != ''):
                            df_master.at[index, 'email'] = row_source['email']
                            emails_fusionnes += 1
                            emails_ajoutés_ce_fichier += 1
                    
                    # Téléphone
                    if 'telephone' in df_source.columns:
                        if (pd.isna(df_master.at[index, 'telephone']) or df_master.at[index, 'telephone'] == '') and \
                           (pd.notna(row_source['telephone']) and str(row_source['telephone']).strip() != ''):
                            df_master.at[index, 'telephone'] = row_source['telephone']
                            telephones_fusionnes += 1
                    
                    # Spécialisations
                    if 'specialisations' in df_source.columns:
                        if (pd.isna(df_master.at[index, 'specialisations']) or df_master.at[index, 'specialisations'] == '') and \
                           (pd.notna(row_source['specialisations']) and str(row_source['specialisations']).strip() != ''):
                            df_master.at[index, 'specialisations'] = row_source['specialisations']
                            specialisations_fusionnees += 1
                    
                    # Structure
                    if 'structure' in df_source.columns:
                        if (pd.isna(df_master.at[index, 'structure']) or df_master.at[index, 'structure'] == '') and \
                           (pd.notna(row_source['structure']) and str(row_source['structure']).strip() != ''):
                            df_master.at[index, 'structure'] = row_source['structure']
                            structures_fusionnees += 1
                    
                    # Adresse
                    if 'adresse' in df_source.columns:
                        if (pd.isna(df_master.at[index, 'adresse']) or df_master.at[index, 'adresse'] == '') and \
                           (pd.notna(row_source['adresse']) and str(row_source['adresse']).strip() != ''):
                            df_master.at[index, 'adresse'] = row_source['adresse']
                            adresses_fusionnees += 1
            
            print(f"    ✅ +{emails_ajoutés_ce_fichier} emails récupérés depuis ce fichier")
            
        except Exception as e:
            print(f"    ❌ Erreur: {str(e)[:100]}")
    
    # Statistiques finales
    total_emails = len(df_master[df_master['email'].notna() & (df_master['email'] != '')])
    total_telephones = len(df_master[df_master['telephone'].notna() & (df_master['telephone'] != '')])
    total_specialisations = len(df_master[df_master['specialisations'].notna() & (df_master['specialisations'] != '')])
    total_structures = len(df_master[df_master['structure'].notna() & (df_master['structure'] != '')])
    total_adresses = len(df_master[df_master['adresse'].notna() & (df_master['adresse'] != '')])
    total_dates = len(df_master[df_master['date_serment'].notna() & (df_master['date_serment'] != '')])
    
    taux_emails = (total_emails / len(df_master)) * 100
    
    # Sauvegarde finale
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fichier_final = f"LYON_FUSION_MAXIMALE_95PC_{len(df_master)}avocats_{total_emails}emails_{timestamp}.csv"
    df_master.to_csv(fichier_final, index=False, encoding='utf-8')
    
    # Fichier emails uniquement
    emails_uniques = df_master[df_master['email'].notna() & (df_master['email'] != '')]['email'].unique()
    emails_filename = f"emails_FUSION_MAXIMALE_{len(emails_uniques)}uniques_{timestamp}.txt"
    with open(emails_filename, 'w', encoding='utf-8') as f:
        for email in sorted(emails_uniques):
            f.write(f"{email}\n")
    
    # Rapport final
    rapport = f"""
🎉 FUSION MAXIMALE 95%+ TERMINÉE !
=================================

📊 DONNÉES FUSIONNÉES AVEC SUCCÈS:
  • Emails supplémentaires: +{emails_fusionnes}
  • Téléphones supplémentaires: +{telephones_fusionnes}
  • Spécialisations supplémentaires: +{specialisations_fusionnees}
  • Structures supplémentaires: +{structures_fusionnees}
  • Adresses supplémentaires: +{adresses_fusionnees}

📈 RÉSULTATS FINAUX MAXIMAUX:
  • Total avocats: {len(df_master)} (100.0%) ✅
  • Emails: {total_emails} ({taux_emails:.1f}%) 📧
  • Téléphones: {total_telephones} ({total_telephones/len(df_master)*100:.1f}%) ☎️
  • Spécialisations: {total_specialisations} ({total_specialisations/len(df_master)*100:.1f}%) 🎯
  • Structures: {total_structures} ({total_structures/len(df_master)*100:.1f}%) 🏢
  • Adresses: {total_adresses} ({total_adresses/len(df_master)*100:.1f}%) 📍
  • Dates de serment: {total_dates} ({total_dates/len(df_master)*100:.1f}%) 📅

📁 FICHIERS FINAUX:
  📄 CSV principal: {fichier_final}
  📧 Emails uniques: {emails_filename}

🎯 OBJECTIF 95% ATTEINT: {"✅ OUI" if taux_emails >= 95 else "⚠️ NON"} ({taux_emails:.1f}%)

✅ MISSION ACCOMPLIE !
Base de données MAXIMALE du Barreau de Lyon avec {total_emails} emails !
"""
    
    print(rapport)
    
    # Sauvegarde du rapport
    rapport_filename = f"RAPPORT_fusion_maximale_95pc_{timestamp}.txt"
    with open(rapport_filename, 'w', encoding='utf-8') as f:
        f.write(rapport)
    
    return fichier_final

if __name__ == "__main__":
    fusion_maximale_95_pourcent()