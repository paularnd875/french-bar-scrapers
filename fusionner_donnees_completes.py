#!/usr/bin/env python3
"""
FUSIONNEUR DE DONNÉES COMPLÈTES - BARREAU DE LYON
Fusionne toutes les données disponibles pour créer le fichier final complet avec TOUTES les informations
"""

import pandas as pd
import glob
from datetime import datetime

def fusionner_donnees_completes():
    print("🔗 FUSIONNEUR DE DONNÉES COMPLÈTES - BARREAU DE LYON")
    print("Objectif : Créer le fichier final avec TOUTES les informations disponibles")
    print("=" * 80)
    
    # Fichier principal avec 100% des dates de serment
    fichier_dates = 'LYON_DATES_OPTIMISE_FINAL_4141avocats_4141dates_20260505_212058.csv'
    
    try:
        df_principal = pd.read_csv(fichier_dates)
        print(f"✅ Fichier principal chargé: {len(df_principal)} avocats avec dates complètes")
    except FileNotFoundError:
        print("❌ Fichier principal avec dates non trouvé")
        return None
    
    # Chercher les fichiers d'enrichissement avec le plus de données
    fichiers_enrichissement = []
    
    # Patterns de fichiers à chercher
    patterns = [
        'LYON_ENRICHI_*emails*.csv',
        'BARREAU_LYON_COMPLET_*.csv',
        '*enrichi*.csv',
        '*LYON*.csv'
    ]
    
    for pattern in patterns:
        fichiers = glob.glob(pattern)
        fichiers_enrichissement.extend(fichiers)
    
    # Éliminer les doublons et trier par taille de fichier
    fichiers_enrichissement = list(set(fichiers_enrichissement))
    fichiers_enrichissement = [f for f in fichiers_enrichissement if f != fichier_dates]
    
    print(f"\\n📁 FICHIERS D'ENRICHISSEMENT TROUVÉS:")
    for fichier in fichiers_enrichissement[:5]:  # Max 5 affichés
        try:
            df_temp = pd.read_csv(fichier)
            emails_count = len(df_temp[df_temp['email'].notna() & (df_temp['email'] != '')]) if 'email' in df_temp.columns else 0
            print(f"  • {fichier}: {len(df_temp)} avocats, {emails_count} emails")
        except:
            continue
    
    # Fusionner les données
    print(f"\\n🔄 FUSION DES DONNÉES EN COURS...")
    
    # Colonnes à enrichir (en plus de nom, prenom, url déjà présents)
    colonnes_target = ['email', 'telephone', 'specialisations', 'structure', 'adresse']
    
    emails_fusionnes = 0
    telephones_fusionnes = 0
    specialisations_fusionnees = 0
    structures_fusionnees = 0
    adresses_fusionnees = 0
    
    for fichier in fichiers_enrichissement:
        try:
            print(f"\\n📋 Traitement de: {fichier}")
            df_source = pd.read_csv(fichier)
            
            # Fusionner par URL (clé unique)
            for index, row_principal in df_principal.iterrows():
                url_principal = row_principal['url']
                
                # Trouver la ligne correspondante dans le fichier source
                row_source = df_source[df_source['url'] == url_principal]
                
                if not row_source.empty:
                    row_source = row_source.iloc[0]  # Prendre la première occurrence
                    
                    # Fusionner chaque colonne si vide dans le principal
                    for col in colonnes_target:
                        if col in df_source.columns:
                            # Si la valeur est vide dans le principal ET disponible dans la source
                            if (pd.isna(df_principal.at[index, col]) or df_principal.at[index, col] == '') and \
                               (pd.notna(row_source[col]) and str(row_source[col]).strip() != ''):
                                df_principal.at[index, col] = row_source[col]
                                
                                # Compteurs
                                if col == 'email' and row_source[col]:
                                    emails_fusionnes += 1
                                elif col == 'telephone' and row_source[col]:
                                    telephones_fusionnes += 1
                                elif col == 'specialisations' and row_source[col]:
                                    specialisations_fusionnees += 1
                                elif col == 'structure' and row_source[col]:
                                    structures_fusionnees += 1
                                elif col == 'adresse' and row_source[col]:
                                    adresses_fusionnees += 1
            
            print(f"   ✅ Données fusionnées depuis {fichier}")
                
        except Exception as e:
            print(f"   ❌ Erreur avec {fichier}: {str(e)[:50]}")
            continue
    
    # Statistiques finales
    total_emails = len(df_principal[df_principal['email'].notna() & (df_principal['email'] != '')])
    total_telephones = len(df_principal[df_principal['telephone'].notna() & (df_principal['telephone'] != '')])
    total_specialisations = len(df_principal[df_principal['specialisations'].notna() & (df_principal['specialisations'] != '')])
    total_structures = len(df_principal[df_principal['structure'].notna() & (df_principal['structure'] != '')])
    total_adresses = len(df_principal[df_principal['adresse'].notna() & (df_principal['adresse'] != '')])
    total_dates = len(df_principal[df_principal['date_serment'].notna() & (df_principal['date_serment'] != '')])
    
    # Sauvegarde du fichier fusionné final
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fichier_final = f"LYON_BASE_FINALE_COMPLETE_{len(df_principal)}avocats_TOUTES_DONNEES_{timestamp}.csv"
    df_principal.to_csv(fichier_final, index=False, encoding='utf-8')
    
    # Rapport final détaillé
    rapport = f"""
🎉 FUSION COMPLÈTE TERMINÉE !
============================

📊 DONNÉES FUSIONNÉES:
  • Emails supplémentaires: +{emails_fusionnes}
  • Téléphones supplémentaires: +{telephones_fusionnes}
  • Spécialisations supplémentaires: +{specialisations_fusionnees}
  • Structures supplémentaires: +{structures_fusionnees}
  • Adresses supplémentaires: +{adresses_fusionnees}

📈 STATISTIQUES FINALES:
  • Total avocats: {len(df_principal)} (100.0%)
  • Emails: {total_emails} ({total_emails/len(df_principal)*100:.1f}%)
  • Téléphones: {total_telephones} ({total_telephones/len(df_principal)*100:.1f}%)
  • Spécialisations: {total_specialisations} ({total_specialisations/len(df_principal)*100:.1f}%)
  • Structures: {total_structures} ({total_structures/len(df_principal)*100:.1f}%)
  • Adresses: {total_adresses} ({total_adresses/len(df_principal)*100:.1f}%)
  • Dates de serment: {total_dates} ({total_dates/len(df_principal)*100:.1f}%)

📁 FICHIER FINAL COMPLET:
  📄 {fichier_final}

✅ BASE DE DONNÉES COMPLÈTE BARREAU DE LYON PRÊTE !
Contient: Nom, Prénom, URL source, Email, Téléphone, Spécialisations, Structure, Adresse, Date de serment
"""
    
    print(rapport)
    
    # Sauvegarde du rapport
    rapport_filename = f"RAPPORT_fusion_complete_{timestamp}.txt"
    with open(rapport_filename, 'w', encoding='utf-8') as f:
        f.write(rapport)
    
    return fichier_final

if __name__ == "__main__":
    fusionner_donnees_completes()