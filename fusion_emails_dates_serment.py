#!/usr/bin/env python3
"""
FUSION EMAILS + DATES DE SERMENT
Croiser le fichier avec le maximum d'emails et celui avec 100% des dates de serment
"""

import pandas as pd
from datetime import datetime

def fusion_emails_dates():
    print("🔥 FUSION EMAILS + DATES DE SERMENT")
    print("=================================")
    
    # Fichier avec le maximum d'emails (3987)
    fichier_emails = 'LYON_ENRICHI_DIRECT_4141avocats_3987emails_20260511_182826.csv'
    
    # Fichier avec 100% des dates de serment
    fichier_dates = 'LYON_DATES_OPTIMISE_FINAL_4141avocats_4141dates_20260505_212058.csv'
    
    try:
        df_emails = pd.read_csv(fichier_emails)
        emails_count = len(df_emails[df_emails['email'].notna() & (df_emails['email'] != '')])
        print(f"✅ Fichier emails chargé: {len(df_emails)} avocats, {emails_count} emails")
    except FileNotFoundError:
        print(f"❌ Fichier emails non trouvé: {fichier_emails}")
        return None
    
    try:
        df_dates = pd.read_csv(fichier_dates)
        dates_count = len(df_dates[df_dates['date_serment'].notna() & (df_dates['date_serment'] != '')])
        print(f"✅ Fichier dates chargé: {len(df_dates)} avocats, {dates_count} dates de serment")
    except FileNotFoundError:
        print(f"❌ Fichier dates non trouvé: {fichier_dates}")
        return None
    
    print(f"\\n🔄 FUSION DES DONNÉES...")
    
    # Partir du fichier avec les emails comme base
    df_final = df_emails.copy()
    
    # S'assurer que la colonne date_serment existe
    if 'date_serment' not in df_final.columns:
        df_final['date_serment'] = ''
    
    # Fusionner les dates de serment par URL
    dates_ajoutees = 0
    
    for index, row in df_final.iterrows():
        url = row['url']
        
        # Trouver la ligne correspondante dans le fichier dates
        matching_rows = df_dates[df_dates['url'] == url]
        
        if not matching_rows.empty:
            date_row = matching_rows.iloc[0]
            
            # Ajouter la date de serment si elle n'existe pas ou est vide
            if pd.isna(df_final.at[index, 'date_serment']) or df_final.at[index, 'date_serment'] == '':
                if pd.notna(date_row['date_serment']) and str(date_row['date_serment']).strip() != '':
                    df_final.at[index, 'date_serment'] = date_row['date_serment']
                    dates_ajoutees += 1
    
    # Statistiques finales
    total_emails = len(df_final[df_final['email'].notna() & (df_final['email'] != '')])
    total_dates = len(df_final[df_final['date_serment'].notna() & (df_final['date_serment'] != '')])
    total_telephones = len(df_final[df_final['telephone'].notna() & (df_final['telephone'] != '')])
    
    # Sauvegarde finale
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fichier_final = f"LYON_COMPLET_FINAL_4141avocats_{total_emails}emails_{total_dates}dates_{timestamp}.csv"
    df_final.to_csv(fichier_final, index=False, encoding='utf-8')
    
    # Fichier emails uniquement pour vérification
    emails_uniques = df_final[df_final['email'].notna() & (df_final['email'] != '')]['email'].unique()
    emails_filename = f"emails_COMPLET_FINAL_{len(emails_uniques)}uniques_{timestamp}.txt"
    with open(emails_filename, 'w', encoding='utf-8') as f:
        for email in sorted(emails_uniques):
            f.write(f"{email}\\n")
    
    # Rapport final
    rapport = f"""
🏆 FUSION EMAILS + DATES DE SERMENT TERMINÉE !
=============================================

📊 DONNÉES FUSIONNÉES AVEC SUCCÈS:
  • Dates de serment ajoutées: +{dates_ajoutees}

📈 BASE DE DONNÉES FINALE COMPLÈTE:
  • Total avocats: {len(df_final)} (100.0%) ✅
  • Emails: {total_emails} ({total_emails/len(df_final)*100:.1f}%) 📧
  • Dates de serment: {total_dates} ({total_dates/len(df_final)*100:.1f}%) 📅
  • Téléphones: {total_telephones} ({total_telephones/len(df_final)*100:.1f}%) ☎️

📁 FICHIERS CRÉÉS:
  📄 CSV principal: {fichier_final}
  📧 Emails uniquement: {emails_filename}

🎯 OBJECTIF 95% EMAILS: {"✅ ATTEINT" if total_emails/len(df_final) >= 0.95 else "⚠️ NON ATTEINT"} ({total_emails/len(df_final)*100:.1f}%)
🎯 DATES DE SERMENT: {"✅ COMPLÈTES" if total_dates >= 4000 else "⚠️ INCOMPLÈTES"} ({total_dates} dates)

🎉 MISSION ACCOMPLIE !
Base de données COMPLÈTE du Barreau de Lyon avec emails ET dates de prestation de serment !
"""
    
    print(rapport)
    
    # Sauvegarde du rapport
    rapport_filename = f"RAPPORT_fusion_emails_dates_{timestamp}.txt"
    with open(rapport_filename, 'w', encoding='utf-8') as f:
        f.write(rapport)
    
    print(f"\\n📋 Rapport sauvegardé: {rapport_filename}")
    
    return fichier_final

if __name__ == "__main__":
    fusion_emails_dates()