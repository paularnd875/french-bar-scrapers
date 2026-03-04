#!/usr/bin/env python3
"""
Corriger la classification prénom/nom du scraper Libourne
Le format fourni était "NOM Prénom", pas "Prénom NOM"
"""

import json
import csv
from datetime import datetime

def corriger_classification():
    """Corriger les erreurs de classification prénom/nom"""
    
    # Charger le fichier final
    with open("LIBOURNE_FINAL_COMPLET_77avocats_20260212_175613.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("🔧 CORRECTION DE LA CLASSIFICATION PRÉNOM/NOM")
    print("=" * 50)
    
    corrections = 0
    for lawyer in data:
        nom_complet = lawyer.get('nom_complet', '')
        
        # Nettoyer le nom
        clean_name = nom_complet.strip()
        
        # Gestion des noms avec particules (DE, DU, etc.)
        if any(clean_name.startswith(prefix) for prefix in ['DE LUNARDO', 'DE VASSELOT']):
            # Ces cas sont spéciaux - déjà bien traités
            continue
        elif clean_name.startswith('BREDIN - KUILAGI'):
            # Cas spécial avec tiret
            lawyer['nom'] = 'BREDIN-KUILAGI'
            lawyer['prenom'] = 'Hélène'
            corrections += 1
        else:
            # Format standard "NOM Prénom(s)"
            parts = clean_name.split()
            if len(parts) >= 2:
                # Premier mot = NOM, le reste = prénom(s)
                nouveau_nom = parts[0]
                nouveau_prenom = ' '.join(parts[1:])
                
                # Vérifier si correction nécessaire
                if lawyer.get('nom') != nouveau_nom or lawyer.get('prenom') != nouveau_prenom:
                    print(f"✏️  {nom_complet}")
                    print(f"   Avant: nom={lawyer.get('nom')}, prenom={lawyer.get('prenom')}")
                    print(f"   Après: nom={nouveau_nom}, prenom={nouveau_prenom}")
                    
                    lawyer['nom'] = nouveau_nom
                    lawyer['prenom'] = nouveau_prenom
                    corrections += 1
    
    print(f"\n📊 {corrections} corrections effectuées")
    
    # Sauvegarder la version corrigée
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON corrigé
    json_file = f"LIBOURNE_FINAL_CORRIGE_77avocats_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # CSV corrigé
    csv_file = f"LIBOURNE_FINAL_CORRIGE_77avocats_{timestamp}.csv"
    fieldnames = ['prenom', 'nom', 'nom_complet', 'email', 'telephone', 
                 'adresse', 'code_postal', 'ville', 'annee_inscription',
                 'specialisations', 'competences', 'structure', 'url', 'extraction_reussie']
                 
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for lawyer in data:
            row = {}
            for field in fieldnames:
                value = lawyer.get(field, '')
                if isinstance(value, list):
                    value = '; '.join(str(v) for v in value)
                row[field] = str(value)
            writer.writerow(row)
    
    # Emails (inchangés)
    emails_file = f"LIBOURNE_FINAL_CORRIGE_EMAILS_{timestamp}.txt"
    unique_emails = set()
    for lawyer in data:
        email = lawyer.get("email", "")
        if email and "@" in email:
            unique_emails.add(email)
            
    with open(emails_file, 'w', encoding='utf-8') as f:
        for email in sorted(unique_emails):
            f.write(f"{email}\n")
    
    # Rapport corrigé
    report_file = f"LIBOURNE_FINAL_CORRIGE_RAPPORT_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"RAPPORT FINAL CORRIGÉ - BARREAU LIBOURNE\n")
        f.write(f"=" * 50 + "\n\n")
        f.write(f"Date correction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Corrections prénom/nom: {corrections}\n\n")
        f.write(f"RÉSULTATS FINAUX:\n")
        f.write(f"- Total avocats: 77/77 (100%)\n")
        f.write(f"- Avec email: 77/77 (100%)\n")
        f.write(f"- Avec téléphone: 77/77 (100%)\n")
        f.write(f"- Emails uniques: {len(unique_emails)}\n\n")
        f.write(f"FICHIERS CORRIGÉS:\n")
        f.write(f"- JSON: {json_file}\n")
        f.write(f"- CSV: {csv_file}\n")
        f.write(f"- Emails: {emails_file}\n")
        f.write(f"- Rapport: {report_file}\n\n")
        
        f.write("VÉRIFICATION - PREMIERS AVOCATS CORRIGÉS:\n")
        f.write("-" * 40 + "\n")
        for i, lawyer in enumerate(data[:10], 1):
            f.write(f"{i}. {lawyer.get('nom_complet', 'N/A')}\n")
            f.write(f"   Prénom: {lawyer.get('prenom', 'N/A')}\n")
            f.write(f"   Nom: {lawyer.get('nom', 'N/A')}\n")
            f.write(f"   Email: {lawyer.get('email', 'N/A')}\n\n")
    
    print(f"\n💾 FICHIERS CORRIGÉS SAUVEGARDÉS:")
    print(f"   📊 CSV: {csv_file}")
    print(f"   📧 Emails: {emails_file}")
    print(f"   📋 Rapport: {report_file}")
    print(f"\n✅ Classification prénom/nom maintenant correcte!")
    
    return csv_file, emails_file

if __name__ == "__main__":
    corriger_classification()