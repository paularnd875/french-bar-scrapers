#!/usr/bin/env python3
"""
Génère les fichiers finaux CSV avec toutes les informations des avocats
"""

import json
import csv
from datetime import datetime

def generer_fichiers_complets():
    # Charger les données
    with open('/Users/paularnould/blois_complet_partial_75_103359.json', 'r', encoding='utf-8') as f:
        lawyers_data = json.load(f)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. CSV PRINCIPAL avec toutes les informations importantes
    csv_principal = f"blois_FINAL_COMPLET_{timestamp}.csv"
    
    # Champs principaux à inclure
    main_fields = [
        'nom_complet', 'nom', 'prenom', 'civilite', 'titre',
        'email', 'telephone', 'fax', 
        'adresse_complete', 'ville', 'code_postal', 
        'site_web', 'annee_inscription', 'date_serment',
        'specialisations', 'domaines_competences',
        'cabinet', 'structure', 'langues', 'diplomes',
        'description_complete', 'coordonnees_completes', 'url'
    ]
    
    with open(csv_principal, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=main_fields)
        writer.writeheader()
        for lawyer in lawyers_data:
            row_data = {field: lawyer.get(field, '') for field in main_fields}
            writer.writerow(row_data)
    
    # 2. CSV EMAILS avec informations essentielles
    csv_emails = f"blois_EMAILS_COMPLET_{timestamp}.csv"
    
    with open(csv_emails, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'nom_complet', 'email', 'telephone', 'adresse_complete', 
            'specialisations', 'cabinet', 'annee_inscription', 'url'
        ])
        
        for lawyer in lawyers_data:
            if lawyer.get('email'):  # Seulement les avocats avec email
                writer.writerow([
                    lawyer.get('nom_complet', ''),
                    lawyer.get('email', ''),
                    lawyer.get('telephone', ''),
                    lawyer.get('adresse_complete', ''),
                    lawyer.get('specialisations', '')[:150],  # Limiter pour lisibilité
                    lawyer.get('cabinet', ''),
                    lawyer.get('annee_inscription', ''),
                    lawyer.get('url', '')
                ])
    
    # 3. JSON COMPLET
    json_complet = f"blois_FINAL_COMPLET_{timestamp}.json"
    with open(json_complet, 'w', encoding='utf-8') as f:
        json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
    
    # 4. Fichier texte emails uniquement
    txt_emails = f"blois_EMAILS_SEULEMENT_{timestamp}.txt"
    with open(txt_emails, 'w', encoding='utf-8') as f:
        for lawyer in lawyers_data:
            if lawyer.get('email'):
                f.write(f"{lawyer.get('email')}\n")
    
    # 5. Rapport statistique
    rapport = f"blois_RAPPORT_FINAL_{timestamp}.txt"
    
    # Statistiques
    total_lawyers = len(lawyers_data)
    with_email = sum(1 for l in lawyers_data if l.get('email'))
    with_phone = sum(1 for l in lawyers_data if l.get('telephone'))
    with_address = sum(1 for l in lawyers_data if l.get('adresse_complete'))
    with_specializations = sum(1 for l in lawyers_data if l.get('specialisations'))
    with_cabinet = sum(1 for l in lawyers_data if l.get('cabinet'))
    with_year = sum(1 for l in lawyers_data if l.get('annee_inscription'))
    
    with open(rapport, 'w', encoding='utf-8') as f:
        f.write("=== RAPPORT FINAL EXTRACTION BARREAU DE BLOIS ===\n\n")
        f.write(f"Date d'extraction: {datetime.now()}\n")
        f.write(f"URL source: https://avocats-blois.com/trouver-un-avocat/\n\n")
        
        f.write("=== STATISTIQUES GLOBALES ===\n")
        f.write(f"Total avocats extraits: {total_lawyers}\n")
        f.write(f"Avocats avec email: {with_email} ({with_email/total_lawyers*100:.1f}%)\n")
        f.write(f"Avocats avec téléphone: {with_phone} ({with_phone/total_lawyers*100:.1f}%)\n")
        f.write(f"Avocats avec adresse: {with_address} ({with_address/total_lawyers*100:.1f}%)\n")
        f.write(f"Avocats avec spécialisations: {with_specializations} ({with_specializations/total_lawyers*100:.1f}%)\n")
        f.write(f"Avocats avec cabinet/structure: {with_cabinet} ({with_cabinet/total_lawyers*100:.1f}%)\n")
        f.write(f"Avocats avec année inscription: {with_year} ({with_year/total_lawyers*100:.1f}%)\n")
        
        f.write(f"\n=== FICHIERS GÉNÉRÉS ===\n")
        f.write(f"1. {csv_principal} - CSV principal avec toutes les colonnes\n")
        f.write(f"2. {csv_emails} - CSV des avocats avec email + infos essentielles\n")
        f.write(f"3. {json_complet} - JSON complet avec tous les champs\n")
        f.write(f"4. {txt_emails} - Liste pure des emails\n")
        f.write(f"5. {rapport} - Ce rapport\n")
        
        f.write(f"\n=== LISTE DES AVOCATS AVEC EMAIL ({with_email}) ===\n")
        for i, lawyer in enumerate([l for l in lawyers_data if l.get('email')], 1):
            f.write(f"{i:2d}. {lawyer.get('nom_complet', 'N/A')} - {lawyer.get('email', 'N/A')}\n")
            if lawyer.get('specialisations'):
                f.write(f"    Spécialisations: {lawyer.get('specialisations', '')[:80]}...\n")
            if lawyer.get('telephone'):
                f.write(f"    Téléphone: {lawyer.get('telephone', '')}\n")
            f.write("\n")
    
    print(f"🎉 FICHIERS FINAUX GÉNÉRÉS !")
    print(f"📊 {total_lawyers} avocats traités")
    print(f"📧 {with_email} emails récupérés")
    print(f"\n📁 FICHIERS CRÉÉS :")
    print(f"   🎯 {csv_principal} (CSV principal)")
    print(f"   📧 {csv_emails} (CSV emails + infos)")
    print(f"   📊 {json_complet} (JSON complet)")
    print(f"   📝 {txt_emails} (Emails purs)")
    print(f"   📋 {rapport} (Rapport détaillé)")
    
    return csv_principal, csv_emails, json_complet, txt_emails, rapport

if __name__ == "__main__":
    generer_fichiers_complets()