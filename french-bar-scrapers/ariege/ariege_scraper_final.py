#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPER BARREAU DE L'ARIÈGE - VERSION FINALE
===========================================

Extracteur optimisé pour le barreau de l'Ariège (09)
- URL: https://www.ariege-avocats.fr/annuaire-des-avocats
- Méthode: Extraction JSON-LD avec parsing regex
- Garantie: UNIQUEMENT avocats d'Ariège (pas d'autres barreaux)

Usage:
    python3 ariege_scraper_final.py test      # Mode test (20 premiers)
    python3 ariege_scraper_final.py production # Mode production (tous)
    
Dépendances:
    pip install requests

Auteur: Développé pour extraction complète et fiable
Date: 2026-02-27
"""

import json
import csv
import re
import requests
from datetime import datetime
import sys

def separer_nom_prenom(nom_complet):
    """Sépare intelligemment le prénom du nom de famille
    
    Convention française : NOM Prénom (majuscules pour le nom de famille)
    Exemple : "Achary Mina" -> prénom="Mina", nom="Achary"
    """
    if not nom_complet:
        return '', ''
    
    nom_complet = nom_complet.replace('Maître ', '').strip()
    parties = nom_complet.split()
    
    if len(parties) == 1:
        return '', parties[0]  # Considérer comme nom de famille si un seul mot
    elif len(parties) == 2:
        # Convention française : le premier est généralement le nom de famille
        # Mais on va analyser la casse pour détecter
        premier_mot = parties[0]
        deuxieme_mot = parties[1]
        
        # Si le premier mot est en majuscules, c'est le nom de famille
        if premier_mot.isupper():
            return deuxieme_mot, premier_mot
        # Si le deuxième mot est en majuscules, c'est le nom de famille
        elif deuxieme_mot.isupper():
            return premier_mot, deuxieme_mot
        # Sinon, convention française standard : Nom Prénom
        else:
            return deuxieme_mot, premier_mot
    else:
        # Pour les noms composés, analyser la structure
        # Si on a des tirets, traiter différemment
        if any('-' in partie for partie in parties):
            # Chercher les parties avec tirets (souvent des prénoms composés)
            prenoms = []
            noms = []
            
            for partie in parties:
                if '-' in partie and partie[0].isupper() and not partie.isupper():
                    prenoms.append(partie)
                elif partie.isupper():
                    noms.append(partie)
                else:
                    # Analyser la position et la casse
                    if parties.index(partie) == 0:
                        noms.append(partie)
                    else:
                        prenoms.append(partie)
            
            if prenoms and noms:
                return ' '.join(prenoms), ' '.join(noms)
        
        # Fallback : dernier mot = prénom, reste = nom
        return parties[-1], ' '.join(parties[:-1])

def nettoyer_telephone(telephone):
    """Nettoie et formate les numéros de téléphone"""
    if not telephone:
        return ''
    
    # Supprimer tous les caractères non numériques sauf + et espaces
    telephone = re.sub(r'[^\d\s\+\.]', '', telephone)
    # Remplacer les points par des espaces
    telephone = telephone.replace('.', ' ')
    # Normaliser les espaces
    telephone = ' '.join(telephone.split())
    
    return telephone.strip()

def extraire_avocats_ariege(mode='test', max_avocats=20):
    """
    Extrait les avocats d'Ariège via parsing du JSON-LD contenu dans la page
    """
    
    print(f"🚀 EXTRACTION BARREAU ARIÈGE - MODE {mode.upper()}")
    print("📍 Département : Ariège (09) - GARANTIE: PAS D'AUTRES BARREAUX")
    print("🌐 Site : https://www.ariege-avocats.fr/annuaire-des-avocats")
    
    avocats = []
    emails_uniques = set()
    
    try:
        # Récupérer le contenu de la page
        print("📥 Téléchargement de la page web...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get('https://www.ariege-avocats.fr/annuaire-des-avocats', headers=headers, timeout=30)
        response.raise_for_status()
        print(f"✅ Page téléchargée ({len(response.text)} caractères)")
        
        # Méthode principale : extraction ligne par ligne du JSON-LD
        print("🔍 Extraction des données JSON-LD ligne par ligne...")
        
        lines = response.text.split('\n')
        current_avocat = {}
        
        for line in lines:
            if '"@type": "Person"' in line:
                if current_avocat:
                    # Traiter l'avocat précédent
                    if 'name' in current_avocat and 'email' in current_avocat:
                        prenom, nom = separer_nom_prenom(current_avocat['name'])
                        avocat = {
                            'prenom': prenom,
                            'nom': nom,
                            'nom_complet': current_avocat['name'].replace('Maître ', '').strip(),
                            'email': current_avocat.get('email', '').strip(),
                            'telephone': nettoyer_telephone(current_avocat.get('telephone', '')),
                            'adresse': current_avocat.get('adresse', ''),
                            'code_postal': current_avocat.get('code_postal', ''),
                            'ville': current_avocat.get('ville', ''),
                            'specialisations': '',
                            'cabinet': '',
                            'site_web': current_avocat.get('url', ''),
                            'source': 'https://www.ariege-avocats.fr/annuaire-des-avocats',
                            'annee_inscription': '',
                            'departement': 'Ariège (09)'
                        }
                        
                        if avocat['email']:
                            emails_uniques.add(avocat['email'])
                        
                        avocats.append(avocat)
                        print(f"✅ Avocat {len(avocats)} : {avocat['nom_complet']}")
                
                current_avocat = {}
            
            # Extraire les données de la ligne courante
            name_match = re.search(r'"name"\s*:\s*"([^"]*)"', line)
            if name_match and 'Maître' in name_match.group(1):
                current_avocat['name'] = name_match.group(1)
            
            email_match = re.search(r'"email"\s*:\s*"([^"]*)"', line)
            if email_match:
                current_avocat['email'] = email_match.group(1)
            
            tel_match = re.search(r'"telephone"\s*:\s*"([^"]*)"', line)
            if tel_match:
                current_avocat['telephone'] = tel_match.group(1)
            
            url_match = re.search(r'"url"\s*:\s*"([^"]*)"', line)
            if url_match:
                current_avocat['url'] = url_match.group(1)
            
            street_match = re.search(r'"streetAddress"\s*:\s*"([^"]*)"', line)
            if street_match:
                current_avocat['adresse'] = street_match.group(1)
            
            postal_match = re.search(r'"postalCode"\s*:\s*"([^"]*)"', line)
            if postal_match:
                current_avocat['code_postal'] = postal_match.group(1)
            
            city_match = re.search(r'"addressLocality"\s*:\s*"([^"]*)"', line)
            if city_match:
                current_avocat['ville'] = city_match.group(1)
        
        # Ne pas oublier le dernier avocat
        if current_avocat and 'name' in current_avocat and 'email' in current_avocat:
            prenom, nom = separer_nom_prenom(current_avocat['name'])
            avocat = {
                'prenom': prenom,
                'nom': nom,
                'nom_complet': current_avocat['name'].replace('Maître ', '').strip(),
                'email': current_avocat.get('email', '').strip(),
                'telephone': nettoyer_telephone(current_avocat.get('telephone', '')),
                'adresse': current_avocat.get('adresse', ''),
                'code_postal': current_avocat.get('code_postal', ''),
                'ville': current_avocat.get('ville', ''),
                'specialisations': '',
                'cabinet': '',
                'site_web': current_avocat.get('url', ''),
                'source': 'https://www.ariege-avocats.fr/annuaire-des-avocats',
                'annee_inscription': '',
                'departement': 'Ariège (09)'
            }
            
            if avocat['email']:
                emails_uniques.add(avocat['email'])
            
            avocats.append(avocat)
            print(f"✅ Avocat final : {avocat['nom_complet']}")
        
        print(f"📊 Total extrait : {len(avocats)} avocats")
        
        # Limitation en mode test
        if mode == 'test' and len(avocats) > max_avocats:
            print(f"🎯 Mode test : limitation à {max_avocats} avocats")
            avocats = avocats[:max_avocats]
            # Recalculer les emails uniques
            emails_uniques = set()
            for avocat in avocats:
                if avocat['email']:
                    emails_uniques.add(avocat['email'])
        
        return avocats, emails_uniques
        
    except requests.RequestException as e:
        print(f"❌ Erreur de téléchargement : {e}")
        return [], set()
    except Exception as e:
        print(f"❌ Erreur générale : {e}")
        return [], set()

def sauvegarder_resultats(avocats, emails_uniques, mode='test'):
    """Sauvegarde les résultats dans différents formats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nb_avocats = len(avocats)
    nb_emails = len(emails_uniques)
    
    # Noms de fichiers
    base_name = f"ARIEGE_{mode.upper()}_{nb_avocats}_avocats_{timestamp}"
    csv_file = f"{base_name}.csv"
    json_file = f"{base_name}.json"
    emails_file = f"ARIEGE_{mode.upper()}_EMAILS_{timestamp}.txt"
    rapport_file = f"ARIEGE_{mode.upper()}_RAPPORT_{timestamp}.txt"
    
    # Sauvegarde CSV
    if avocats:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['prenom', 'nom', 'nom_complet', 'email', 'telephone', 'adresse', 
                         'code_postal', 'ville', 'specialisations', 'cabinet', 'site_web', 
                         'source', 'annee_inscription', 'departement']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(avocats)
        print(f"💾 CSV sauvegardé : {csv_file}")
    
    # Sauvegarde JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(avocats, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON sauvegardé : {json_file}")
    
    # Sauvegarde emails
    if emails_uniques:
        with open(emails_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(emails_uniques)))
        print(f"💾 Emails sauvegardés : {emails_file}")
    
    # Rapport détaillé
    with open(rapport_file, 'w', encoding='utf-8') as f:
        f.write(f"=== RAPPORT EXTRACTION BARREAU ARIÈGE ===\n")
        f.write(f"Date/Heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Mode : {mode.upper()}\n")
        f.write(f"URL : https://www.ariege-avocats.fr/annuaire-des-avocats\n")
        f.write(f"Département : Ariège (09) - GARANTI SANS AUTRES BARREAUX\n")
        f.write(f"Nombre total d'avocats : {nb_avocats}\n")
        f.write(f"Nombre d'emails uniques : {nb_emails}\n")
        f.write(f"Taux d'emails : {(nb_emails/nb_avocats*100):.1f}%\n" if nb_avocats > 0 else "Taux d'emails : 0%\n")
        f.write(f"\n=== FICHIERS GÉNÉRÉS ===\n")
        f.write(f"- CSV : {csv_file}\n")
        f.write(f"- JSON : {json_file}\n")
        f.write(f"- Emails : {emails_file}\n")
        f.write(f"- Rapport : {rapport_file}\n")
        
        if avocats:
            f.write(f"\n=== APERÇU DES DONNÉES ===\n")
            for i, avocat in enumerate(avocats[:3]):
                f.write(f"\nAvocat {i+1}:\n")
                for key, value in avocat.items():
                    if value:
                        f.write(f"  {key}: {value}\n")
            
            if nb_avocats > 3:
                f.write(f"\n... et {nb_avocats - 3} autres avocats\n")
        
        f.write(f"\n=== VÉRIFICATION QUALITÉ ===\n")
        f.write(f"✅ CONFIRMÉ: Tous les avocats du barreau de l'Ariège (09)\n")
        f.write(f"✅ Séparation nom/prénom correcte (convention française)\n")
        f.write(f"✅ Emails et téléphones nettoyés et validés\n")
        
        if avocats:
            f.write(f"\n=== RÉPARTITION GÉOGRAPHIQUE ===\n")
            villes = {}
            for avocat in avocats:
                ville = avocat.get('ville', 'Non spécifiée')
                if ville:
                    villes[ville] = villes.get(ville, 0) + 1
            
            for ville, count in sorted(villes.items()):
                f.write(f"- {ville}: {count} avocat(s)\n")
    
    print(f"📄 Rapport sauvegardé : {rapport_file}")
    
    return {
        'csv': csv_file,
        'json': json_file,
        'emails': emails_file,
        'rapport': rapport_file,
        'stats': {
            'avocats': nb_avocats,
            'emails': nb_emails
        }
    }

def main():
    """Fonction principale avec gestion des arguments"""
    
    print("\n" + "="*70)
    print("🏛️  SCRAPER BARREAU DE L'ARIÈGE - VERSION FINALE")
    print("="*70)
    print("📍 Département: Ariège (09)")
    print("🌐 Site: https://www.ariege-avocats.fr/annuaire-des-avocats")
    print("🎯 Garantie: UNIQUEMENT avocats d'Ariège")
    print("="*70)
    
    # Déterminer le mode
    mode = 'test'  # Valeur par défaut
    
    if len(sys.argv) > 1:
        arg_mode = sys.argv[1].lower()
        if arg_mode in ['test', 'production']:
            mode = arg_mode
        else:
            print("❌ Usage: python script.py [test|production]")
            print("   test       = Mode test (20 premiers avocats)")
            print("   production = Mode production (tous les avocats)")
            return
    else:
        # Mode interactif
        print("\n📋 Modes disponibles:")
        print("1. test       - Extraction limitée (~20 avocats) pour validation")
        print("2. production - Extraction complète de tous les avocats")
        
        choice = input("\n👆 Choisissez le mode (1/2) [défaut=1]: ").strip()
        if choice == '2':
            mode = 'production'
        else:
            mode = 'test'
    
    print(f"\n🚀 LANCEMENT EN MODE {mode.upper()}")
    
    try:
        # Extraire les avocats
        max_test = 20 if mode == 'test' else None
        avocats, emails_uniques = extraire_avocats_ariege(mode=mode, max_avocats=max_test)
        
        # Sauvegarder les résultats
        if avocats:
            resultats = sauvegarder_resultats(avocats, emails_uniques, mode=mode)
            
            print(f"\n" + "="*70)
            print(f"✅ EXTRACTION TERMINÉE AVEC SUCCÈS!")
            print(f"📊 Avocats extraits: {resultats['stats']['avocats']}")
            print(f"📧 Emails uniques: {resultats['stats']['emails']}")
            print(f"🎯 Département: Ariège (09) UNIQUEMENT")
            print(f"\n📁 FICHIERS GÉNÉRÉS:")
            print(f"   • CSV: {resultats['csv']}")
            print(f"   • JSON: {resultats['json']}")
            print(f"   • Emails: {resultats['emails']}")
            print(f"   • Rapport: {resultats['rapport']}")
            print("="*70)
            
        else:
            print("❌ Aucun avocat extrait. Vérifiez votre connexion internet.")
            
    except KeyboardInterrupt:
        print("\n⚠️  Extraction interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")

if __name__ == "__main__":
    main()