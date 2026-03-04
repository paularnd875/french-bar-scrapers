#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper amélioré pour extraire les données des avocats du barreau de la Meuse
"""

import re
import csv
import json
from typing import List, Dict, Any

def parse_avocat_data_improved() -> List[Dict[str, Any]]:
    """
    Parse améliorer les données des avocats depuis le contenu textuel du PDF
    """
    
    # Données extraites manuellement du PDF avec une structure plus propre
    avocats_raw = [
        "Me LECHAUDEL Jean-Pierre 5 rue du Cygne - BAR LE DUC jp.lechaudel@orange.fr Tél. 03 29 79 08 68 1977",
        "Me FORGET Jean-Louis 81 rue des Ducs de Bar - BAR LE DUC conseiletdefensedubarrois@gmail.com Tél. 03 29 79 01 65 - Fax : 03.29.79.75.30 1985 24 avenue Stanislas - COMMERCY",
        "Me HECHINGER Christophe 3 rue Louis Maury - VERDUN c.hechinger-avocat@wanadoo.fr Tél. 03 29 86 71 33 1986",
        "Me MOUGENOT MATHIS Sophie 2 rue de Couchot - BAR LE DUC sophie.mougenot-mathis@wanadoo.fr Tél. 03 29 77 19 81 1996 Docteur en droit - Spécialiste en Droit Commercial, des affaires et de la concurrence www.mougenot-mathis.avocat.fr",
        "Me PERCEVAL Elisabeth 28 rue Saint-Pierre - VERDUN scp.demange-associes@wanadoo.fr Tél. 03 29 86 04 64 - Fax: 03.29.86.45.69 2001 20 place Saint-Pierre - BAR LE DUC www.demange-associes.fr Tél. 03 29 75 35 48",
        "Me HAGNIER Fabrice 14 Avenue de la Victoire - VERDUN hagnier.fabrice@cedpavocat.com Tél. 03 55 13 65 89 2001 www.cedpavocat.fr",
        "Me VAUTRIN Vincent 66 avenue Miribel - VERDUN vautrin.vincent@avocatslca.com Tél. 03 29 73 71 56 - Fax: 03.29.73.71.55 2001 www.legi-conseil.com",
        "Me SCHINDLER Loïc 28 Rue Saint Pierre - VERDUN scp.demange-associes@wanadoo.fr Tél. 03 29 86 04 64 - Fax: 03.29.86.45.69 2001 20 Place Saint Pierre - BAR LE DUC www.demange-associes.fr Tél. 03 29 75 35 48",
        "Me LIGNOT Angélique 13 Rue Exelmans - BAR LE DUC cabinet.lignot@wanadoo.fr Tél. 03 29 45 80 53 - Fax: 03.29.70.09.86 2002 www.cabinet-lignot.fr",
        "Me LAUMONT David 7 Place du Gouvernement - VERDUN laumont.david@wanadoo.fr Tél. 03 29 86 75 05 - Fax: 03.29.86.72.95 2002",
        "Me BEYNA Sylvain 66 avenue Miribel - VERDUN sylvain.beyna@avocatslca.com Tél. 03 29 73 71 56 - Fax: 03.29.73.71.55 2004 www.legi-conseil.com",
        "Me LIGNOT Xavier 13 Rue Exelmans - BAR LE DUC cabinet.lignot@wanadoo.fr Tél. 03 29 45 80 53 - Fax: 03.29.70.09.86 2008 www.cabinet-lignot.fr",
        "Me DUBAUX Nadège 16 Rue de la 7° DB USA -VERDUN www.nadege-dubaux.fr Tél. 03 29 79 29 13 - Fax: 03.29.79.81.36 2008 20 rue Voltaire - BAR LE DUC nadege.dubaux.avocat@outlook.com",
        "Me LAGRIFFOUL Laetitia 24 bd Raymond Poincaré - BAR LE DUC laetitia.lagriffoul@outlook.fr Tél. 03 54 02 77 80 - Fax : 03.72.27.36.97 2012 www.laetitialagriffoul.wixsite.com/avocat",
        "Me NODEE Xavier 7 place du Gouvernement - VERDUN xavier.nodee@orange.fr Tél. 03 29 86 18 91 - Fax : 03.29.86.72.95 2013",
        "Me HEL Théo 81 rue des Ducs de Bar – BAR LE DUC conseiletdefensedubarrois@gmail.com Tél. 03 29 79 01 65 – Fax : 03.29.79.75 30 2014 24 avenue Stanislas - COMMERCY",
        "Me RODRIGUES Julia 13 Rue Exelmans– BAR LE DUC contact@rodrigues-avocat.fr Tél. 03 29 45 80 53 - Fax: 03.29.70.09.86 2018 www.rodrigues-avocat.fr Tél. 06 88 44 55 65",
        "Me BAGARD Guillaume 23 Grande Rue – TRONVILLE EN BARROIS bagard.guillaume@avocat-conseil.fr Tél. 09 63 52 69 80 2023",
        "Me RODRIGUES Léa 24 bd Raymond Poincaré - BAR LE DUC lea.rodrigues.avocat@outlook.fr Tél. 03 54 02 77 80 - Fax : 03.72.27.36.97 2023"
    ]
    
    avocats = []
    
    for line in avocats_raw:
        avocat = parse_single_avocat(line)
        if avocat:
            avocats.append(avocat)
    
    return avocats

def parse_single_avocat(line: str) -> Dict[str, Any]:
    """
    Parse une ligne d'avocat individual
    """
    avocat = {
        'civilite': 'Me',
        'nom': '',
        'prenom': '',
        'adresse_principale': '',
        'adresse_secondaire': '',
        'ville_principale': '',
        'ville_secondaire': '',
        'email': '',
        'telephone': '',
        'telephone_2': '',
        'fax': '',
        'website': '',
        'annee_serment': '',
        'specialisations': '',
        'structure': ''
    }
    
    # Extraire nom et prénom
    name_match = re.match(r'^Me\s+([A-ZÉÈÊ\-\s]+?)\s+([A-Za-zéèêàùç\-\s]+?)\s+(.+)', line)
    if name_match:
        avocat['nom'] = name_match.group(1).strip()
        avocat['prenom'] = name_match.group(2).strip()
        rest_of_line = name_match.group(3)
    else:
        return None
    
    # Email(s)
    emails = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', rest_of_line)
    if emails:
        avocat['email'] = emails[0]
    
    # Téléphones
    telephones = re.findall(r'Tél\.?\s*([0-9\s\.]{10,})', rest_of_line)
    if len(telephones) >= 1:
        avocat['telephone'] = telephones[0].strip()
    if len(telephones) >= 2:
        avocat['telephone_2'] = telephones[1].strip()
    
    # Fax
    fax_match = re.search(r'Fax[:\s]*([0-9\s\.]{10,})', rest_of_line)
    if fax_match:
        avocat['fax'] = fax_match.group(1).strip()
    
    # Website
    websites = re.findall(r'(www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', rest_of_line)
    if websites:
        avocat['website'] = websites[0]
    
    # Année de serment
    annee_match = re.search(r'\b(19\d{2}|20\d{2})\b', rest_of_line)
    if annee_match:
        avocat['annee_serment'] = annee_match.group(1)
    
    # Adresses (avant les emails)
    adresses_raw = re.findall(r'(\d+[^@]*?(?:BAR LE DUC|VERDUN|COMMERCY|TRONVILLE EN BARROIS))', rest_of_line)
    if len(adresses_raw) >= 1:
        avocat['adresse_principale'] = adresses_raw[0].strip()
        # Extraire la ville principale
        ville_match = re.search(r'(BAR LE DUC|VERDUN|COMMERCY|TRONVILLE EN BARROIS)', adresses_raw[0])
        if ville_match:
            avocat['ville_principale'] = ville_match.group(1)
    
    if len(adresses_raw) >= 2:
        avocat['adresse_secondaire'] = adresses_raw[1].strip()
        # Extraire la ville secondaire
        ville_match = re.search(r'(BAR LE DUC|VERDUN|COMMERCY|TRONVILLE EN BARROIS)', adresses_raw[1])
        if ville_match:
            avocat['ville_secondaire'] = ville_match.group(1)
    
    # Spécialisations
    if 'Spécialiste' in rest_of_line or 'Docteur en droit' in rest_of_line:
        spec_match = re.search(r'(Docteur en droit.*?(?=www|Tél|$)|Spécialiste.*?(?=www|Tél|$))', rest_of_line)
        if spec_match:
            avocat['specialisations'] = spec_match.group(1).strip()
    
    return avocat

def detect_structures(avocats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Détecte les structures/cabinets basés sur les emails et adresses partagés
    """
    
    # Structures connues basées sur le PDF
    structures = {
        'scp.demange-associes@wanadoo.fr': 'SCP DEMANGE ET ASSOCIES',
        'cabinet.lignot@wanadoo.fr': 'SCP LIGNOT',
        'conseiletdefensedubarrois@gmail.com': 'SELARL CONSEIL et DEFENSE DU BARROIS',
        'avocatslca.com': 'SELARL LEGICONSEILS AVOCATS',
        'cedpavocat.com': 'Cabinet CEDP'
    }
    
    for avocat in avocats:
        email = avocat['email']
        for pattern, structure in structures.items():
            if pattern in email:
                avocat['structure'] = structure
                break
        
        # Détection basée sur les sites web
        website = avocat['website']
        if 'demange-associes' in website:
            avocat['structure'] = 'SCP DEMANGE ET ASSOCIES'
        elif 'cabinet-lignot' in website:
            avocat['structure'] = 'SCP LIGNOT'
        elif 'legi-conseil' in website:
            avocat['structure'] = 'SELARL LEGICONSEILS AVOCATS'
        elif 'cedpavocat' in website:
            avocat['structure'] = 'Cabinet CEDP'
    
    return avocats

def save_to_csv(avocats: List[Dict[str, Any]], filename: str = "avocats_meuse_complet.csv"):
    """
    Sauvegarde les données en CSV
    """
    if not avocats:
        print("Aucune donnée à sauvegarder")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['civilite', 'nom', 'prenom', 'adresse_principale', 'adresse_secondaire', 
                     'ville_principale', 'ville_secondaire', 'email', 'telephone', 'telephone_2',
                     'fax', 'website', 'annee_serment', 'specialisations', 'structure']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for avocat in avocats:
            writer.writerow(avocat)
    
    print(f"Données sauvegardées dans {filename}")

def save_to_json(avocats: List[Dict[str, Any]], filename: str = "avocats_meuse_complet.json"):
    """
    Sauvegarde les données en JSON
    """
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(avocats, jsonfile, ensure_ascii=False, indent=2)
    
    print(f"Données sauvegardées dans {filename}")

def print_stats(avocats: List[Dict[str, Any]]):
    """
    Affiche des statistiques sur les données extraites
    """
    print(f"\n=== STATISTIQUES ===")
    print(f"Nombre total d'avocats : {len(avocats)}")
    
    # Emails
    emails_count = len([a for a in avocats if a['email']])
    print(f"Avocats avec email : {emails_count}")
    
    # Spécialisations
    specs_count = len([a for a in avocats if a['specialisations']])
    print(f"Avocats avec spécialisations : {specs_count}")
    
    # Structures
    structures_count = len([a for a in avocats if a['structure']])
    print(f"Avocats avec structure identifiée : {structures_count}")
    
    # Répartition par ville
    villes = {}
    for avocat in avocats:
        ville = avocat['ville_principale']
        if ville:
            villes[ville] = villes.get(ville, 0) + 1
    
    print(f"\nRépartition par ville :")
    for ville, count in sorted(villes.items()):
        print(f"  {ville}: {count}")
    
    # Années
    annees = [int(a['annee_serment']) for a in avocats if a['annee_serment'].isdigit()]
    if annees:
        print(f"\nAnnées de serment : {min(annees)} - {max(annees)}")

def main():
    """
    Fonction principale
    """
    print("=== EXTRACTION COMPLÈTE DES AVOCATS DU BARREAU DE LA MEUSE ===")
    
    # Parser les données
    avocats = parse_avocat_data_improved()
    
    # Détecter les structures
    avocats = detect_structures(avocats)
    
    print(f"\nNombre d'avocats extraits : {len(avocats)}")
    
    # Afficher quelques exemples détaillés
    print("\n=== EXEMPLES DÉTAILLÉS ===")
    for i, avocat in enumerate(avocats[:3]):
        print(f"\nAvocat {i+1}:")
        for key, value in avocat.items():
            if value:
                print(f"  {key}: {value}")
    
    # Statistiques
    print_stats(avocats)
    
    # Sauvegarder
    save_to_csv(avocats)
    save_to_json(avocats)
    
    return avocats

if __name__ == "__main__":
    main()