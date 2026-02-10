#!/usr/bin/env python3
"""
Parser amélioré pour le PDF du Barreau de Bonneville
Parse correctement les données des avocats depuis le texte extrait
"""

import re
import csv
import json
from datetime import datetime

def parse_bonneville_lawyers(text_file_path):
    """Parse les avocats depuis le fichier texte extrait du PDF"""
    
    with open(text_file_path, 'r', encoding='utf-8') as f:
        text_content = f.read()
    
    lawyers = []
    lines = text_content.split('\n')
    
    # Trouver le début de la liste des avocats
    start_index = 0
    for i, line in enumerate(lines):
        if 'baStid arnaud' in line and 'SELARL' in line:
            start_index = i
            break
    
    print(f"Début de la liste d'avocats trouvé à la ligne {start_index}")
    
    # Parser chaque avocat
    i = start_index
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
            
        # Pattern pour une ligne d'avocat
        # Format: nom prénom - structure    ville - adresse    téléphone    email    année
        lawyer_match = re.search(
            r'([a-zA-ZàáâäèéêëìíîïòóôöùúûüÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜç\s-]+)\s+-\s*([^-]*?)\s+([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][a-zA-ZàáâäèéêëìíîïòóôöùúûüÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜç\s-]+)\s+-\s*([^0-9]+?)\s+((?:04\.|0[1-9])[0-9\.\s]+)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+([0-9]{4})',
            line
        )
        
        if lawyer_match:
            nom_prenom = lawyer_match.group(1).strip()
            structure = lawyer_match.group(2).strip()
            ville = lawyer_match.group(3).strip()
            adresse = lawyer_match.group(4).strip()
            telephone = lawyer_match.group(5).strip()
            email = lawyer_match.group(6).strip()
            annee_inscription = lawyer_match.group(7).strip()
            
            # Séparer nom et prénom
            nom_parts = nom_prenom.split()
            if len(nom_parts) >= 2:
                nom = nom_parts[0].title()
                prenom = ' '.join(nom_parts[1:]).title()
            else:
                nom = nom_prenom.title()
                prenom = ""
            
            # Nettoyer les données
            structure = re.sub(r'\s+', ' ', structure)
            adresse_complete = f"{ville} - {adresse}".strip()
            telephone = re.sub(r'[^\d\+\.]', '', telephone)
            
            lawyer = {
                'nom': nom,
                'prenom': prenom,
                'nom_complet': f"{prenom} {nom}".strip(),
                'email': email,
                'telephone': telephone,
                'adresse': adresse_complete,
                'ville': ville.title(),
                'annee_inscription': annee_inscription,
                'structure': structure,
                'specialisations': ''
            }
            
            # Chercher les spécialisations sur la ligne suivante
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and 'Drt' in next_line:
                    lawyer['specialisations'] = next_line
                    i += 1  # Skip la ligne de spécialisation
            
            lawyers.append(lawyer)
            print(f"Avocat trouvé: {lawyer['nom_complet']} - {lawyer['email']}")
            
        i += 1
    
    return lawyers

def save_improved_results(lawyers):
    """Sauvegarde les résultats améliorés"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV
    csv_filename = f"bonneville_avocats_AMELIORE_{timestamp}.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['nom', 'prenom', 'nom_complet', 'email', 'telephone', 
                     'adresse', 'ville', 'annee_inscription', 'structure', 'specialisations']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for lawyer in lawyers:
            writer.writerow(lawyer)
    
    # JSON
    json_filename = f"bonneville_avocats_AMELIORE_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(lawyers, jsonfile, ensure_ascii=False, indent=2)
    
    # Emails uniquement
    emails_filename = f"bonneville_emails_AMELIORE_{timestamp}.txt"
    with open(emails_filename, 'w', encoding='utf-8') as emailfile:
        for lawyer in lawyers:
            if lawyer['email']:
                emailfile.write(f"{lawyer['email']}\n")
    
    # Rapport
    report_filename = f"bonneville_rapport_AMELIORE_{timestamp}.txt"
    with open(report_filename, 'w', encoding='utf-8') as reportfile:
        reportfile.write("RAPPORT EXTRACTION AMÉLIORÉE - BARREAU DE BONNEVILLE\n")
        reportfile.write("="*55 + "\n\n")
        
        reportfile.write(f"Total avocats: {len(lawyers)}\n")
        reportfile.write(f"Emails: {sum(1 for l in lawyers if l['email'])}\n")
        reportfile.write(f"Téléphones: {sum(1 for l in lawyers if l['telephone'])}\n")
        reportfile.write(f"Spécialisations: {sum(1 for l in lawyers if l['specialisations'])}\n\n")
        
        reportfile.write("LISTE DES AVOCATS:\n")
        reportfile.write("-" * 30 + "\n")
        for i, lawyer in enumerate(lawyers, 1):
            reportfile.write(f"{i:2d}. {lawyer['nom_complet']}\n")
            reportfile.write(f"    📧 {lawyer['email']}\n")
            reportfile.write(f"    📞 {lawyer['telephone']}\n")
            reportfile.write(f"    🏢 {lawyer['structure']}\n")
            reportfile.write(f"    📍 {lawyer['adresse']}\n")
            reportfile.write(f"    📅 {lawyer['annee_inscription']}\n")
            if lawyer['specialisations']:
                reportfile.write(f"    ⚖️  {lawyer['specialisations']}\n")
            reportfile.write("\n")
    
    print(f"\n✅ PARSING AMÉLIORÉ TERMINÉ")
    print(f"📊 {len(lawyers)} avocats parsés")
    print(f"📁 Fichiers générés:")
    print(f"   • {csv_filename}")
    print(f"   • {json_filename}")
    print(f"   • {emails_filename}")
    print(f"   • {report_filename}")
    
    return lawyers

if __name__ == "__main__":
    print("🔍 PARSING AMÉLIORÉ DU PDF BONNEVILLE")
    print("=" * 40)
    
    # Parse les avocats depuis le fichier texte
    lawyers = parse_bonneville_lawyers('/Users/paularnould/bonneville_pdf_text.txt')
    
    if lawyers:
        # Sauvegarder les résultats
        save_improved_results(lawyers)
    else:
        print("❌ Aucun avocat trouvé")