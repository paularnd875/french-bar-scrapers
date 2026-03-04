#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POST-TRAITEMENT INTELLIGENT - EXTRACTION CABINETS MEAUX
Analyse les emails pour identifier et corriger les noms de cabinets manqués

UTILISATION:
1. D'abord exécuter: python3 meaux_scraper_main.py
2. Puis exécuter: python3 meaux_cabinet_enhancer.py <fichier_json_généré>

EXEMPLE:
python3 meaux_cabinet_enhancer.py MEAUX_AVOCATS_185avocats_20260304_151321.json

AMÉLIORATION ATTENDUE:
- Cabinets: de 10-15% à 55-60% des avocats
- Identification automatique des cabinets via analyse des emails
- Détection des groupes d'avocats partageant le même cabinet

DÉVELOPPÉ POUR: https://github.com/paularnd875/french-bar-scrapers
"""

import json
import csv
import re
import sys
from datetime import datetime
from collections import defaultdict

def extract_cabinet_from_email(email, nom, prenom):
    """Extrait intelligemment le nom du cabinet à partir de l'email"""
    if not email:
        return ""
    
    email_parts = email.lower().split('@')
    if len(email_parts) != 2:
        return ""
    
    local, domain = email_parts
    
    # Patterns spéciaux pour des structures connues
    special_patterns = {
        'fidal': 'FIDAL',
        'touraut': 'Touraut & Associés',
        'lemys-avocats': 'LeMys Avocats',
        'fbcmd': 'Cabinet FBCMD',
        'bcdavocats': 'BCD Avocats',
        'avocats-igp': 'Cabinet IGP Avocats',
        'dfavocats': 'Cabinet DF Avocats',
        'ultreia-avocats': 'Ultreia Avocats',
        'rn-avocats': 'RN Avocats',
        'prolexial': 'Prolexial',
        'giegl-avocats': 'GIEGL Avocats',
        'aazavocats': 'AAZ Avocats',
        'habeneckavocats': 'Cabinet Habeneck',
        'hag-avocat': 'Cabinet HAG',
        'heuseleavocat': 'Cabinet Heusele',
        'mh-avocate': 'Cabinet MH Avocate',
        'juriscausa': 'Juriscausa',
        'ckavocats': 'CK Avocats',
        'jaw-avocats': 'JAW Avocats',
        'horme-avocats': 'Horme Avocats',
        'jokic-avocat': 'Cabinet Jokic',
        'mls-avocat': 'MLS Avocat',
        'avocat-negrevergne': 'Cabinet Négrevergne',
        'malpel-associes': 'Malpel & Associés',
        'sdsavocats': 'SDS Avocats',
        'vrea-avocat': 'VREA Avocat',
        'as-avocat': 'AS Avocat',
        'avocat-sirot': 'Cabinet Sirot',
        'stl-avocats': 'STL Avocats',
        'ctl-avocats': 'CTL Avocats',
        'vdvavocats': 'VDV Avocats',
        'altm': 'ALTM Avocats',
        'avocatsmorinperrault': 'Cabinet Morin Perrault',
        'bonnemaison-avocat': 'Cabinet Bonnemaison',
        'courtois-avocat': 'Cabinet Courtois',
        'vgerard-avocats': 'Cabinet Vincent Gérard',
        'cck-avocat': 'Cabinet CCK',
        'avocat-lenfant': 'Cabinet Lenfant',
        'avocat-mande': 'Cabinet Mande',
        'emargerie-avocat': 'Cabinet E. Margerie',
        'avocat-miquel': 'Cabinet Miquel',
        'lmavocat': 'Cabinet LM Avocat',
        'an-avocat': 'Cabinet AN Avocat',
        'avocat-rizk': 'Cabinet Rizk',
        'gaellereynaud-avocat': 'Cabinet Gaëlle Reynaud',
        'l-avocate': 'Cabinet L\'Avocate',
        'juliamoroni': 'Cabinet Julia Moroni'
    }
    
    # Vérifier les patterns spéciaux d'abord
    for key, value in special_patterns.items():
        if key in domain:
            return value
    
    # Patterns génériques pour extraction automatique
    cabinet_patterns = [
        # Patterns avec cabinet/avocat
        r'cabinet[.-]([a-zA-Z-]+)',
        r'avocat[s]?[.-]([a-zA-Z-]+)', 
        r'([a-zA-Z]+)-avocat[s]?',
        r'([a-zA-Z]+)avocat[s]?',
        r'avocat[s]?-([a-zA-Z]+)',
        
        # Structures juridiques
        r'scp[.-]([a-zA-Z-]+)',
        r'selarl[.-]([a-zA-Z-]+)',
        
        # Associations
        r'([a-zA-Z]+)-associes',
        r'([a-zA-Z]+)-avocats',
        r'avocats-([a-zA-Z]+)',
        
        # Domaines dédiés
        r'^([a-zA-Z]{3,})-avocats?\.fr$',
        r'^([a-zA-Z]{3,})avocats?\.fr$',
    ]
    
    for pattern in cabinet_patterns:
        match = re.search(pattern, domain)
        if match and match.group(1):
            cabinet_name = match.group(1).replace('-', ' ').title()
            # Éviter les noms personnels
            if (cabinet_name.lower() not in nom.lower() and 
                cabinet_name.lower() not in prenom.lower() and
                len(cabinet_name) > 2 and
                cabinet_name.lower() not in ['gmail', 'yahoo', 'orange', 'hotmail', 'outlook', 'free', 'sfr']):
                return f"Cabinet {cabinet_name}"
    
    return ""

def detect_cabinet_groups(lawyers):
    """Détecte les groupes de cabinets basés sur les domaines email similaires"""
    email_groups = defaultdict(list)
    
    for lawyer in lawyers:
        if lawyer.get('email'):
            domain = lawyer['email'].split('@')[-1] if '@' in lawyer['email'] else ''
            if domain and 'gmail' not in domain and 'yahoo' not in domain and 'orange' not in domain and 'hotmail' not in domain:
                email_groups[domain].append(lawyer)
    
    # Identifier les vrais cabinets (plusieurs avocats)
    cabinet_groups = {}
    for domain, group in email_groups.items():
        if len(group) > 1:
            cabinet_name = extract_cabinet_from_email(f"test@{domain}", "", "")
            if cabinet_name:
                cabinet_groups[domain] = cabinet_name
    
    return cabinet_groups

def enhance_cabinets(input_file):
    """Améliore l'extraction des cabinets sur un fichier existant"""
    
    print("🧠 POST-TRAITEMENT INTELLIGENT - EXTRACTION CABINETS")
    print("=" * 60)
    print(f"📂 Fichier d'entrée: {input_file}")
    
    # Charger les données
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lawyers = json.load(f)
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {input_file}")
        return
    except json.JSONDecodeError:
        print(f"❌ Fichier JSON invalide: {input_file}")
        return
    
    print(f"👥 {len(lawyers)} avocats chargés")
    
    # État initial
    initial_cabinets = len([l for l in lawyers if l.get('cabinet')])
    print(f"🏢 Cabinets initiaux: {initial_cabinets} ({initial_cabinets/len(lawyers)*100:.1f}%)")
    
    # Détecter les groupes de cabinets
    cabinet_groups = detect_cabinet_groups(lawyers)
    print(f"\n📊 Groupes de cabinets détectés: {len(cabinet_groups)}")
    for domain, cabinet in cabinet_groups.items():
        count = len([l for l in lawyers if l.get('email', '').endswith(f'@{domain}')])
        print(f"  - {cabinet}: {count} avocats")
    
    # Appliquer les améliorations
    enhanced_count = 0
    
    for lawyer in lawyers:
        if lawyer.get('cabinet'):
            continue  # Déjà un cabinet
            
        email = lawyer.get('email', '')
        if not email:
            continue
            
        # Utiliser les groupes détectés
        domain = email.split('@')[-1] if '@' in email else ''
        if domain in cabinet_groups:
            lawyer['cabinet'] = cabinet_groups[domain]
            enhanced_count += 1
            continue
            
        # Extraction individuelle
        cabinet = extract_cabinet_from_email(email, lawyer.get('nom', ''), lawyer.get('prenom', ''))
        if cabinet:
            lawyer['cabinet'] = cabinet
            enhanced_count += 1
    
    # Statistiques finales
    final_cabinets = len([l for l in lawyers if l.get('cabinet')])
    improvement = final_cabinets - initial_cabinets
    
    print(f"\n📊 RÉSULTATS:")
    print(f"  ✅ Total avocats: {len(lawyers)}")
    print(f"  📧 Emails: {len([l for l in lawyers if l.get('email')])} ({len([l for l in lawyers if l.get('email')])/len(lawyers)*100:.1f}%)")
    print(f"  🏢 Nouveaux cabinets: +{enhanced_count}")
    print(f"  🏢 Cabinets finaux: {final_cabinets} ({final_cabinets/len(lawyers)*100:.1f}%)")
    print(f"  📈 Amélioration: +{improvement} (+{improvement/len(lawyers)*100:.1f}%)")
    
    # Sauvegarder les résultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = input_file.replace('.json', '').replace('MEAUX_AVOCATS_', 'MEAUX_ENHANCED_')
    
    # CSV
    csv_file = f"{base_name}_ENHANCED_{timestamp}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        if lawyers:
            fieldnames = lawyers[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for lawyer in lawyers:
                row = lawyer.copy()
                # Convertir les listes en chaînes pour CSV
                for key, value in row.items():
                    if isinstance(value, list):
                        row[key] = ' | '.join(str(v) for v in value)
                writer.writerow(row)
    
    # JSON
    json_file = f"{base_name}_ENHANCED_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(lawyers, jsonfile, ensure_ascii=False, indent=2)
    
    # Emails
    emails = sorted(set([l['email'] for l in lawyers if l.get('email')]))
    email_file = f"{base_name}_EMAILS_{len(emails)}_ENHANCED_{timestamp}.txt"
    with open(email_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(emails))
    
    # Aperçu des cabinets
    cabinets = [l['cabinet'] for l in lawyers if l.get('cabinet')]
    if cabinets:
        unique_cabinets = sorted(set(cabinets))
        print(f"\n🏢 APERÇU DES CABINETS ({len(unique_cabinets)} uniques):")
        for cabinet in unique_cabinets[:15]:
            count = cabinets.count(cabinet)
            print(f"  - {cabinet}" + (f" ({count} avocats)" if count > 1 else ""))
        if len(unique_cabinets) > 15:
            print(f"  ... et {len(unique_cabinets)-15} autres")
    
    print(f"\n📁 FICHIERS GÉNÉRÉS:")
    print(f"  📊 CSV: {csv_file}")
    print(f"  🗂️  JSON: {json_file}")
    print(f"  📧 Emails: {email_file}")
    
    print(f"\n🎉 POST-TRAITEMENT TERMINÉ AVEC SUCCÈS !")
    return csv_file, json_file, email_file

def main():
    if len(sys.argv) != 2:
        print("UTILISATION: python3 meaux_cabinet_enhancer.py <fichier_json>")
        print("\nEXEMPLE:")
        print("python3 meaux_cabinet_enhancer.py MEAUX_AVOCATS_185avocats_20260304_151321.json")
        return
    
    input_file = sys.argv[1]
    enhance_cabinets(input_file)

if __name__ == "__main__":
    main()