#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper pour le Barreau de Sens - Version Finale
URL: https://www.barreau-sens-avocat.fr/annuaire

Ce scraper extrait les 30 avocats du Barreau de Sens avec:
- Séparation précise des prénoms et noms de famille
- Adresses complètes avec codes postaux
- Numéros de téléphone
- Gestion des noms composés et caractères spéciaux

Auteur: Claude Code
Date: Mars 2026
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import json
from datetime import datetime
import csv
import sys
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SensBarreauScraper:
    def __init__(self):
        self.base_url = "https://www.barreau-sens-avocat.fr"
        self.annuaire_url = "https://www.barreau-sens-avocat.fr/annuaire"
        self.session = requests.Session()
        self.setup_headers()
        
    def setup_headers(self):
        """Configuration des headers pour ressembler à un navigateur réel"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def separate_first_last_names(self, full_name):
        """
        Sépare de manière précise les prénoms et noms de famille
        Utilise un dictionnaire des cas connus pour une précision maximale
        """
        
        # Dictionnaire complet des 30 avocats avec séparation précise
        known_separations = {
            'Denis EVRARD': ('Denis', 'EVRARD'),
            'Españita ORTEGA': ('Españita', 'ORTEGA'),
            'Chantal DEVELAY-BARDE': ('Chantal', 'DEVELAY-BARDE'),
            'Patricia CROCI': ('Patricia', 'CROCI'),
            'Christophe NOEL': ('Christophe', 'NOEL'),
            'Laure LICHÈRE LEMONNIER': ('Laure', 'LICHÈRE LEMONNIER'),
            'Laure LE CHEVOIR': ('Laure', 'LE CHEVOIR'),
            'Carole DURIF': ('Carole', 'DURIF'),
            'Karine BERAL': ('Karine', 'BERAL'),
            'Thierry FLEURIER': ('Thierry', 'FLEURIER'),
            'Véronique BOICHÉ-CALLUS': ('Véronique', 'BOICHÉ-CALLUS'),
            'David KAHN': ('David', 'KAHN'),
            'Anne-Gaëlle LECOUR': ('Anne-Gaëlle', 'LECOUR'),
            'Rudy FARIA': ('Rudy', 'FARIA'),
            'Magali DUBREUCQ TRUDDAÏU': ('Magali', 'DUBREUCQ TRUDDAÏU'),
            'Linda BEAUXIS-AUSSALET': ('Linda', 'BEAUXIS-AUSSALET'),
            'Marie-Marguerite FIUMÉ': ('Marie-Marguerite', 'FIUMÉ'),
            'Gaëlle BUFFIÈRE': ('Gaëlle', 'BUFFIÈRE'),
            'Emmanuelle BRUN': ('Emmanuelle', 'BRUN'),
            'Karym FELLAH': ('Karym', 'FELLAH'),
            'Laure CRETIN': ('Laure', 'CRETIN'),
            'Déborah MAUPETIT': ('Déborah', 'MAUPETIT'),
            'Céline LECARPENTIER': ('Céline', 'LECARPENTIER'),
            'Mélinda DEVIDAL': ('Mélinda', 'DEVIDAL'),
            'Roxane BOURGUIGNON': ('Roxane', 'BOURGUIGNON'),
            'Sabine VUILLERMOZ': ('Sabine', 'VUILLERMOZ'),
            'Evrard KOUASSI': ('Evrard', 'KOUASSI'),
            'Nicolas DEILLER': ('Nicolas', 'DEILLER'),
            'Danielle KAMDOUM': ('Danielle', 'KAMDOUM'),
            'Léonce KOLIMEDJE': ('Léonce', 'KOLIMEDJE')
        }
        
        # Vérification directe
        if full_name in known_separations:
            return known_separations[full_name]
        
        # Algorithme générique pour nouveaux noms
        parts = full_name.strip().split()
        
        if len(parts) <= 1:
            return ('', full_name)
        
        # Logique intelligente de séparation
        prenom_parts = []
        nom_parts = []
        
        for i, part in enumerate(parts):
            is_lastname = False
            
            # Critères d'identification du nom de famille
            if part.isupper() and len(part) > 1:
                is_lastname = True
            elif part.upper() in ['LE', 'DE', 'DU', 'DES', 'LA', 'VAN', 'VON']:
                is_lastname = True
            elif i > 0 and (part.isupper() or '-' in part):
                is_lastname = True
            
            if is_lastname:
                nom_parts.extend(parts[i:])
                break
            else:
                prenom_parts.append(part)
        
        # Fallback
        if not nom_parts:
            if len(parts) == 2:
                prenom_parts = [parts[0]]
                nom_parts = [parts[1]]
            else:
                prenom_parts = parts[:-1]
                nom_parts = [parts[-1]]
        
        return (' '.join(prenom_parts), ' '.join(nom_parts))

    def extract_contact_info(self, text_block):
        """Extrait les informations de contact depuis un bloc de texte"""
        lines = [line.strip() for line in text_block.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        # Première ligne = nom complet
        full_name = lines[0]
        prenom, nom_famille = self.separate_first_last_names(full_name)
        
        # Initialisation
        address = ""
        postal_code = ""
        city = ""
        phone = ""
        
        # Extraction des autres informations
        for line in lines[1:]:
            # Téléphone (formats multiples)
            phone_match = re.search(r'(\d{2}\.?\d{2}\.?\d{2}\.?\d{2}\.?\d{2})', line)
            if phone_match:
                phone = phone_match.group(1)
                # Normalisation du format
                if '.' not in phone:
                    phone = f"{phone[:2]}.{phone[2:4]}.{phone[4:6]}.{phone[6:8]}.{phone[8:]}"
            
            # Code postal et ville
            postal_match = re.search(r'(\d{5})\s+([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ\s\-]+)$', line, re.IGNORECASE)
            if postal_match:
                postal_code = postal_match.group(1)
                city = postal_match.group(2).strip().upper()
                # Adresse = tout ce qui précède le code postal
                address = line.replace(f"{postal_code} {postal_match.group(2)}", "").strip()
        
        return {
            'nom_complet': full_name,
            'prenom': prenom,
            'nom_famille': nom_famille,
            'adresse': address,
            'code_postal': postal_code,
            'ville': city,
            'telephone': phone,
            'email': '',  # Non disponible publiquement
            'structure': '',  # Non disponible
            'specialisations': '',  # Non disponible sur ce site
            'annee_serment': '',  # Non disponible sur ce site
            'source': self.annuaire_url
        }

    def scrape_all_lawyers(self):
        """Scrape tous les avocats du Barreau de Sens"""
        logger.info("Début du scraping du Barreau de Sens...")
        
        try:
            # Récupération de la page
            response = self.session.get(self.annuaire_url)
            response.raise_for_status()
            logger.info(f"Page récupérée avec succès ({len(response.content)} bytes)")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Recherche du contenu principal
            main_content = soup.find('div', class_='da-cell-content')
            if not main_content:
                main_content = soup.find('div', class_='content') or soup.find('main') or soup
            
            logger.info("Bloc principal trouvé, extraction des avocats...")
            
            # Extraction des blocs d'avocats
            full_text = main_content.get_text()
            lines = full_text.split('\n')
            
            lawyer_blocks = []
            current_block = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Détecter un nouveau avocat (prénom + nom en majuscules)
                if re.match(r'^[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ][a-zàáâãäåæçèéêëìíîïñòóôõöøùúûüý\-]+\s+[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ\s\-]+$', line):
                    if current_block:
                        lawyer_blocks.append(current_block.strip())
                    current_block = line
                else:
                    if current_block:
                        current_block += "\n" + line
            
            # Ajouter le dernier bloc
            if current_block:
                lawyer_blocks.append(current_block.strip())
            
            logger.info(f"{len(lawyer_blocks)} blocs d'avocats détectés")
            
            # Extraction des données
            lawyers_data = []
            
            for i, block in enumerate(lawyer_blocks):
                try:
                    lawyer_info = self.extract_contact_info(block)
                    if lawyer_info and lawyer_info['nom_famille']:
                        lawyers_data.append(lawyer_info)
                        logger.info(f"Extrait: {lawyer_info['prenom']} {lawyer_info['nom_famille']}")
                    else:
                        logger.warning(f"Échec extraction bloc {i+1}")
                
                except Exception as e:
                    logger.error(f"Erreur bloc {i+1}: {e}")
                    continue
            
            logger.info(f"Total: {len(lawyers_data)} avocats extraits avec succès")
            return lawyers_data
            
        except Exception as e:
            logger.error(f"Erreur générale: {e}")
            return []

    def save_results(self, lawyers_data, mode="production"):
        """Sauvegarde les résultats dans différents formats"""
        if not lawyers_data:
            logger.error("Aucune donnée à sauvegarder")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"SENS_BARREAU_{mode.upper()}_{len(lawyers_data)}_avocats_{timestamp}"
        
        files_created = {}
        
        try:
            # CSV principal
            csv_file = f"{base_filename}.csv"
            df = pd.DataFrame(lawyers_data)
            
            # Ordre des colonnes optimisé
            column_order = ['nom_complet', 'prenom', 'nom_famille', 'adresse', 'code_postal', 
                          'ville', 'telephone', 'email', 'structure', 'specialisations', 
                          'annee_serment', 'source']
            df = df.reindex(columns=column_order)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            files_created['csv'] = csv_file
            
            # JSON
            json_file = f"{base_filename}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
            files_created['json'] = json_file
            
            # Téléphones
            phones = [lawyer['telephone'] for lawyer in lawyers_data if lawyer['telephone']]
            phones_unique = sorted(list(set(phones)))
            if phones_unique:
                phone_file = f"{base_filename}_TELEPHONES_{len(phones_unique)}.txt"
                with open(phone_file, 'w', encoding='utf-8') as f:
                    for phone in phones_unique:
                        f.write(f"{phone}\n")
                files_created['phones'] = phone_file
            
            # Rapport détaillé
            rapport_file = f"{base_filename}_RAPPORT_COMPLET.txt"
            self.generate_report(lawyers_data, rapport_file)
            files_created['report'] = rapport_file
            
            logger.info("Fichiers sauvegardés:")
            for file_type, filename in files_created.items():
                logger.info(f"  {file_type}: {filename}")
            
            return files_created
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return None

    def generate_report(self, lawyers_data, filename):
        """Génère un rapport détaillé"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RAPPORT DE SCRAPING - BARREAU DE SENS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"🌐 URL: {self.annuaire_url}\n")
            f.write(f"📊 Avocats extraits: {len(lawyers_data)}\n\n")
            
            # Statistiques
            prenoms = [l['prenom'] for l in lawyers_data if l['prenom']]
            noms = [l['nom_famille'] for l in lawyers_data if l['nom_famille']]
            prenoms_composes = [p for p in prenoms if '-' in p]
            noms_composes = [n for n in noms if '-' in n or ' ' in n]
            
            f.write("📈 STATISTIQUES:\n")
            f.write(f"   • Prénoms extraits: {len(prenoms)}\n")
            f.write(f"   • Prénoms composés: {len(prenoms_composes)}\n")
            f.write(f"   • Noms extraits: {len(noms)}\n")
            f.write(f"   • Noms composés: {len(noms_composes)}\n")
            f.write(f"   • Téléphones: {len([l for l in lawyers_data if l['telephone']])}\n")
            f.write(f"   • Adresses: {len([l for l in lawyers_data if l['adresse']])}\n\n")
            
            # Répartition géographique
            villes = {}
            for lawyer in lawyers_data:
                if lawyer['ville']:
                    villes[lawyer['ville']] = villes.get(lawyer['ville'], 0) + 1
            
            f.write("🏙️  RÉPARTITION GÉOGRAPHIQUE:\n")
            for ville, count in sorted(villes.items(), key=lambda x: x[1], reverse=True):
                f.write(f"   • {ville}: {count} avocat(s)\n")
            f.write("\n")
            
            # Liste complète
            f.write("👥 LISTE COMPLÈTE:\n")
            f.write("-" * 60 + "\n")
            for i, lawyer in enumerate(lawyers_data, 1):
                f.write(f"{i:2d}. {lawyer['prenom']} {lawyer['nom_famille']}\n")
                if lawyer['adresse']:
                    f.write(f"    📍 {lawyer['adresse']}\n")
                if lawyer['code_postal'] and lawyer['ville']:
                    f.write(f"       {lawyer['code_postal']} {lawyer['ville']}\n")
                if lawyer['telephone']:
                    f.write(f"    📞 {lawyer['telephone']}\n")
                f.write("\n")

def main():
    """Fonction principale"""
    print("🏛️  SCRAPER BARREAU DE SENS - VERSION FINALE")
    print("=" * 60)
    print("📍 Source: https://www.barreau-sens-avocat.fr/annuaire")
    print("🎯 Objectif: Extraction de tous les avocats avec prénoms/noms séparés")
    print("=" * 60)
    
    scraper = SensBarreauScraper()
    
    try:
        # Scraping
        lawyers_data = scraper.scrape_all_lawyers()
        
        if lawyers_data:
            # Sauvegarde
            files = scraper.save_results(lawyers_data)
            
            if files:
                # Résumé
                prenoms = [l['prenom'] for l in lawyers_data if l['prenom']]
                noms = [l['nom_famille'] for l in lawyers_data if l['nom_famille']]
                prenoms_composes = len([p for p in prenoms if '-' in p])
                noms_composes = len([n for n in noms if '-' in n or ' ' in n])
                
                print(f"\n" + "="*60)
                print(f"✅ SCRAPING TERMINÉ AVEC SUCCÈS!")
                print(f"📊 {len(lawyers_data)} avocats extraits")
                print(f"👤 {len(prenoms)} prénoms ({prenoms_composes} composés)")
                print(f"👥 {len(noms)} noms ({noms_composes} composés)")
                print(f"📞 {len([l for l in lawyers_data if l['telephone']])} téléphones")
                print(f"📍 {len([l for l in lawyers_data if l['ville']])} adresses")
                print(f"=" * 60)
            else:
                print("\n❌ Erreur lors de la sauvegarde")
                sys.exit(1)
        else:
            print("\n❌ Aucun avocat extrait")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        print(f"\n❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()