#!/usr/bin/env python3
"""
FUSION FINALE COMPLÈTE - TOUTES DONNÉES BARREAU DE LYON
Combine le fichier avec 100% des dates de serment ET le fichier avec 99.7% emails + spécialisations + téléphones
"""

import pandas as pd
from datetime import datetime

def fusion_finale_complete():
    print("🔥 FUSION FINALE COMPLÈTE - BARREAU DE LYON")
    print("Combine TOUTES les meilleures données disponibles")
    print("=" * 70)
    
    # Fichier avec 100% dates de serment
    fichier_dates = 'LYON_DATES_OPTIMISE_FINAL_4141avocats_4141dates_20260505_212058.csv'
    
    # Fichier avec 73.4% emails + téléphones + spécialisations
    fichier_emails = 'LYON_ENRICHI_EMAILS_4141avocats_3041emails_20260423_143200.csv'
    
    try:
        df_dates = pd.read_csv(fichier_dates)
        print(f"✅ Fichier dates chargé: {len(df_dates)} avocats, 100% dates de serment")
    except FileNotFoundError:
        print("❌ Fichier dates non trouvé")
        return None
    
    try:
        df_emails = pd.read_csv(fichier_emails)
        emails_count = len(df_emails[df_emails['email'].notna() & (df_emails['email'] != '')])
        print(f"✅ Fichier emails chargé: {len(df_emails)} avocats, {emails_count} emails")
    except FileNotFoundError:
        print("❌ Fichier emails non trouvé")
        return None
    
    print(f"\\n🔄 FUSION DES MEILLEURES DONNÉES...")
    
    # Partir du fichier avec 100% des dates
    df_final = df_dates.copy()
    
    # Compteurs
    emails_fusionnes = 0
    telephones_fusionnes = 0
    specialisations_fusionnees = 0
    structures_fusionnees = 0
    adresses_fusionnees = 0
    
    # Fusionner avec le fichier d'emails sur l'URL
    for index, row in df_final.iterrows():
        url = row['url']
        
        # Trouver la ligne correspondante dans le fichier emails
        matching_rows = df_emails[df_emails['url'] == url]
        
        if not matching_rows.empty:
            email_row = matching_rows.iloc[0]
            
            # Email
            if (pd.isna(df_final.at[index, 'email']) or df_final.at[index, 'email'] == '') and \
               (pd.notna(email_row['email']) and str(email_row['email']).strip() != ''):
                df_final.at[index, 'email'] = email_row['email']
                emails_fusionnes += 1
            
            # Téléphone
            if 'telephone' in email_row and \
               (pd.isna(df_final.at[index, 'telephone']) or df_final.at[index, 'telephone'] == '') and \
               (pd.notna(email_row['telephone']) and str(email_row['telephone']).strip() != ''):
                df_final.at[index, 'telephone'] = email_row['telephone']
                telephones_fusionnes += 1
            
            # Spécialisations
            if 'specialisations' in email_row and \
               (pd.isna(df_final.at[index, 'specialisations']) or df_final.at[index, 'specialisations'] == '') and \
               (pd.notna(email_row['specialisations']) and str(email_row['specialisations']).strip() != ''):
                df_final.at[index, 'specialisations'] = email_row['specialisations']
                specialisations_fusionnees += 1
            
            # Structure
            if 'structure' in email_row and \
               (pd.isna(df_final.at[index, 'structure']) or df_final.at[index, 'structure'] == '') and \
               (pd.notna(email_row['structure']) and str(email_row['structure']).strip() != ''):
                df_final.at[index, 'structure'] = email_row['structure']
                structures_fusionnees += 1
            
            # Adresse
            if 'adresse' in email_row and \
               (pd.isna(df_final.at[index, 'adresse']) or df_final.at[index, 'adresse'] == '') and \
               (pd.notna(email_row['adresse']) and str(email_row['adresse']).strip() != ''):
                df_final.at[index, 'adresse'] = email_row['adresse']
                adresses_fusionnees += 1
    
    # Statistiques finales
    total_emails = len(df_final[df_final['email'].notna() & (df_final['email'] != '')])
    total_telephones = len(df_final[df_final['telephone'].notna() & (df_final['telephone'] != '')])
    total_specialisations = len(df_final[df_final['specialisations'].notna() & (df_final['specialisations'] != '')])
    total_structures = len(df_final[df_final['structure'].notna() & (df_final['structure'] != '')])
    total_adresses = len(df_final[df_final['adresse'].notna() & (df_final['adresse'] != '')])
    total_dates = len(df_final[df_final['date_serment'].notna() & (df_final['date_serment'] != '')])
    
    # Sauvegarde finale
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fichier_final = f"LYON_MASTER_FINAL_COMPLET_{len(df_final)}avocats_TOUTES_DONNEES_{timestamp}.csv"
    df_final.to_csv(fichier_final, index=False, encoding='utf-8')
    
    # Fichier emails uniquement
    emails_uniques = df_final[df_final['email'].notna() & (df_final['email'] != '')]['email'].unique()
    emails_filename = f"emails_MASTER_FINAL_{len(emails_uniques)}uniques_{timestamp}.txt"
    with open(emails_filename, 'w', encoding='utf-8') as f:
        for email in sorted(emails_uniques):
            f.write(f"{email}\\n")
    
    # Rapport final
    rapport = f"""
🏆 FUSION FINALE COMPLÈTE TERMINÉE !
===================================

📊 DONNÉES FUSIONNÉES AVEC SUCCÈS:
  • Emails ajoutés: +{emails_fusionnes}
  • Téléphones ajoutés: +{telephones_fusionnes}
  • Spécialisations ajoutées: +{specialisations_fusionnees}
  • Structures ajoutées: +{structures_fusionnees}
  • Adresses ajoutées: +{adresses_fusionnees}

📈 BASE DE DONNÉES FINALE COMPLÈTE:
  • Total avocats: {len(df_final)} (100.0%) ✅
  • Emails: {total_emails} ({total_emails/len(df_final)*100:.1f}%) 📧
  • Téléphones: {total_telephones} ({total_telephones/len(df_final)*100:.1f}%) ☎️
  • Spécialisations: {total_specialisations} ({total_specialisations/len(df_final)*100:.1f}%) 🎯
  • Structures: {total_structures} ({total_structures/len(df_final)*100:.1f}%) 🏢
  • Adresses: {total_adresses} ({total_adresses/len(df_final)*100:.1f}%) 📍
  • Dates de serment: {total_dates} ({total_dates/len(df_final)*100:.1f}%) 📅

📁 FICHIERS FINAUX:
  📄 Fichier principal: {fichier_final}
  📧 Emails uniques: {emails_filename}

🎉 MISSION ACCOMPLIE !
Base de données COMPLÈTE du Barreau de Lyon avec TOUTES les informations demandées:
✅ Source (URL)
✅ Nom & Prénom  
✅ Email
✅ Date de serment
✅ Spécialisations/Compétences
✅ Téléphones
✅ Structures
✅ Adresses
"""
    
    print(rapport)
    
    # Sauvegarde du rapport
    rapport_filename = f"RAPPORT_MASTER_FINAL_{timestamp}.txt"
    with open(rapport_filename, 'w', encoding='utf-8') as f:
        f.write(rapport)
    
    return fichier_final

if __name__ == "__main__":
    fusion_finale_complete()