#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORRECTION SIMPLE DES NOMS COMPOSÉS - MELUN
Application du parsing corrigé sur le fichier de 140 avocats
"""
import csv
import json
from datetime import datetime

def parse_name_corrected(full_name):
    """Logique corrigée pour les noms composés avec espaces"""
    if ' ' in full_name:
        name_parts = full_name.split()
        
        # Trouver le dernier mot qui n'est pas entièrement en majuscules
        prenom_index = len(name_parts) - 1  # par défaut le dernier
        
        for i in range(len(name_parts) - 1, -1, -1):
            word = name_parts[i]
            # Si le mot a des minuscules (pas tout en majuscules), c'est probablement le prénom
            if any(c.islower() for c in word):
                prenom_index = i
                break
        
        # Séparer nom et prénom
        if prenom_index > 0:
            nom = ' '.join(name_parts[:prenom_index])
            prenom = ' '.join(name_parts[prenom_index:])
        else:
            # Cas particulier : tout en majuscules ou un seul mot composé
            nom = ' '.join(name_parts[:-1]) if len(name_parts) > 1 else name_parts[0]
            prenom = name_parts[-1] if len(name_parts) > 1 else ""
    else:
        nom = full_name
        prenom = ""
    
    return nom, prenom

# Fichiers
input_file = "/Users/paularnould/MELUN_FIXED_COMPLET_140_avocats_20260216_175403.csv"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_csv = f"/Users/paularnould/MELUN_FINAL_CORRIGE_140_avocats_{timestamp}.csv"
output_json = f"/Users/paularnould/MELUN_FINAL_CORRIGE_140_avocats_{timestamp}.json"
output_emails = f"/Users/paularnould/MELUN_FINAL_EMAILS_SEULEMENT_{timestamp}.txt"
output_rapport = f"/Users/paularnould/MELUN_FINAL_RAPPORT_COMPLET_{timestamp}.txt"

print("🔧 CORRECTION DES NOMS COMPOSÉS - MELUN")
print("=" * 50)
print(f"📁 Fichier source: {input_file.split('/')[-1]}")

lawyers = []
fixed_count = 0

# Lire et corriger le fichier CSV
with open(input_file, 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    
    for row in reader:
        # Extraire nom complet original
        nom_complet = row['nom_complet']
        
        # Appliquer le parsing corrigé
        nom_corrige, prenom_corrige = parse_name_corrected(nom_complet)
        
        # Vérifier si une correction a été appliquée
        if nom_corrige != row['nom'] or prenom_corrige != row['prenom']:
            print(f"✅ CORRIGÉ: '{nom_complet}' -> nom: '{nom_corrige}', prenom: '{prenom_corrige}'")
            fixed_count += 1
        
        # Créer l'entrée corrigée
        lawyer = {
            'nom': nom_corrige,
            'prenom': prenom_corrige,
            'nom_complet': nom_complet,
            'email': row['email'],
            'telephone': row['telephone'],
            'date_serment': row['date_serment'],
            'annee_inscription': row['annee_inscription'],
            'specialisations': row['specialisations'],
            'structure': row['structure'],
            'adresse': row['adresse'],
            'source': row['source']
        }
        
        lawyers.append(lawyer)

print(f"\n📊 RÉSULTATS:")
print(f"Total d'avocats: {len(lawyers)}")
print(f"Noms corrigés: {fixed_count}")

# Écrire les fichiers de sortie
with open(output_csv, 'w', newline='', encoding='utf-8') as file:
    fieldnames = ['nom', 'prenom', 'nom_complet', 'email', 'telephone', 'date_serment', 'annee_inscription', 'specialisations', 'structure', 'adresse', 'source']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(lawyers)

with open(output_json, 'w', encoding='utf-8') as file:
    json.dump(lawyers, file, ensure_ascii=False, indent=2)

# Extraire uniquement les emails
emails = [lawyer['email'] for lawyer in lawyers if lawyer['email']]
with open(output_emails, 'w', encoding='utf-8') as file:
    for email in emails:
        file.write(f"{email}\n")

# Rapport final
with open(output_rapport, 'w', encoding='utf-8') as file:
    file.write("🏛️  RAPPORT FINAL - BARREAU DE MELUN (NOMS CORRIGÉS)\n")
    file.write("=" * 60 + "\n\n")
    file.write(f"📅 Date: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
    file.write(f"🌐 Source: https://www.barreau-melun.org\n\n")
    file.write(f"✅ Total d'avocats: {len(lawyers)}\n")
    file.write(f"📧 Emails: {len(emails)} ({len(emails)/len(lawyers)*100:.1f}%)\n")
    file.write(f"🔧 Noms corrigés: {fixed_count}\n\n")
    file.write("📁 Fichiers générés:\n")
    file.write(f"   • {output_csv.split('/')[-1]}\n")
    file.write(f"   • {output_json.split('/')[-1]}\n")
    file.write(f"   • {output_emails.split('/')[-1]}\n")

print(f"\n🎉 FICHIERS GÉNÉRÉS:")
print(f"   • CSV: {output_csv.split('/')[-1]}")
print(f"   • JSON: {output_json.split('/')[-1]}")
print(f"   • Emails: {output_emails.split('/')[-1]}")
print(f"   • Rapport: {output_rapport.split('/')[-1]}")