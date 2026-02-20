#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper pour le Barreau de Sarreguemines
https://www.avocats-sarreguemines.fr/annuaire-des-avocats-du-barreau.htm

Version finale optimisée - Extraction complète de tous les avocats du barreau
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
import time
import random
from datetime import datetime
from urllib.parse import urljoin
import sys

class SarregueminesScraper:
    def __init__(self):
        self.base_url = "https://www.avocats-sarreguemines.fr"
        self.start_url = f"{self.base_url}/annuaire-des-avocats-du-barreau.htm"
        
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
        self.avocats_data = []

    def extract_name_parts(self, full_name):
        """
        Sépare correctement prénom et nom en gérant les cas complexes
        Gère les prénoms composés (Marie-Anne, Jean Christophe) et noms composés (GIANNETTI-LANG)
        """
        if not full_name:
            return "", ""
        
        # Nettoyer le nom
        clean_name = re.sub(r'^(Maître|Me\.?|M\.)\s*', '', full_name.strip(), flags=re.IGNORECASE)
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        # Séparer les mots
        parts = clean_name.split()
        
        if len(parts) <= 1:
            return clean_name, ""
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            # Logique améliorée pour les noms composés
            # Les mots entièrement en majuscules à la fin sont le nom de famille
            nom_parts = []
            prenom_parts = []
            
            # Parcourir de la fin vers le début
            for i in range(len(parts) - 1, -1, -1):
                if parts[i].isupper() and len(parts[i]) > 1:
                    nom_parts.insert(0, parts[i])
                else:
                    # Tout ce qui reste va dans le prénom
                    prenom_parts = parts[:i + 1]
                    break
            
            # Si pas de pattern clair, prendre le dernier mot comme nom
            if not nom_parts:
                nom_parts = [parts[-1]]
                prenom_parts = parts[:-1]
            
            prenom = " ".join(prenom_parts)
            nom = " ".join(nom_parts)
            
            return prenom, nom

    def get_lawyer_links(self, limit=None):
        """Récupère tous les liens vers les fiches des avocats"""
        try:
            print(f"🔍 Récupération de la liste des avocats depuis: {self.start_url}")
            
            response = self.session.get(self.start_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver tous les liens vers les fiches d'avocats
            all_links = soup.find_all('a', href=True)
            lawyer_links = set()  # Utiliser un set pour éviter les doublons
            
            for link in all_links:
                href = link.get('href', '')
                
                # Filtrer les liens qui pointent vers les fiches d'avocats
                if 'maitre-' in href.lower() and 'annuaire' in href.lower():
                    # Corriger l'URL relative
                    if href.startswith('page/'):
                        full_url = urljoin(self.base_url, href)
                    else:
                        full_url = urljoin(self.base_url, href)
                    
                    # Exclure les liens avec des ancres (#contact)
                    if '#' not in full_url:
                        lawyer_links.add(full_url)
            
            lawyer_links = list(lawyer_links)
            print(f"📊 {len(lawyer_links)} avocats uniques trouvés")
            
            # Limiter si demandé (pour les tests)
            if limit:
                lawyer_links = lawyer_links[:limit]
                print(f"🧪 Mode test: limitation à {len(lawyer_links)} avocats")
            
            return lawyer_links
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des liens: {e}")
            return []

    def extract_lawyer_details(self, lawyer_url):
        """Extrait les détails d'un avocat depuis sa fiche"""
        try:
            filename = lawyer_url.split('/')[-1]
            
            response = self.session.get(lawyer_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Initialiser les données
            data = {
                'prenom': '',
                'nom': '',
                'nom_complet': '',
                'annee_inscription': '',
                'specialisations': '',
                'competences': '',
                'activites_dominantes': '',
                'structure': '',
                'adresse': '',
                'telephone': '',
                'email': '',
                'source_url': lawyer_url
            }
            
            # Extraire le nom depuis le titre de la page
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # Extraire le nom du titre (avant le |)
                if '|' in title_text:
                    data['nom_complet'] = title_text.split('|')[0].strip()
            
            # Chercher aussi dans les H1/H2 si pas trouvé
            if not data['nom_complet']:
                for tag in ['h1', 'h2']:
                    element = soup.find(tag)
                    if element:
                        text = element.get_text(strip=True)
                        if 'maître' in text.lower() or len(text.split()) >= 2:
                            data['nom_complet'] = text
                            break
            
            # Séparer prénom et nom
            if data['nom_complet']:
                data['prenom'], data['nom'] = self.extract_name_parts(data['nom_complet'])
            
            # Récupérer tout le texte de la page pour l'analyse
            page_text = soup.get_text()
            page_html = str(soup)
            
            # Extraire le téléphone
            phone_patterns = [
                r'(\d{10})',
                r'(\d{2}[.\s-]?\d{2}[.\s-]?\d{2}[.\s-]?\d{2}[.\s-]?\d{2})'
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, page_text)
                if match:
                    phone = re.sub(r'[.\s-]', '', match.group(1))
                    if len(phone) == 10:
                        data['telephone'] = phone
                        break
            
            # Extraire l'adresse avec patterns améliorés et nettoyage HTML
            address_patterns = [
                r'(\d+[^0-9]*(?:Rue|Avenue|Boulevard|Place|Allée|Impasse|Chemin)[^0-9]*\d{5}[^0-9]*[A-Z][A-Z\s]+)',
                r'(\d+[^0-9]*[A-Za-zÀ-ÿ\s-]+\d{5}[^0-9]*[A-Z][A-Z\s]+)'
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, page_html, re.IGNORECASE)
                if match:
                    # Nettoyer complètement l'adresse
                    address = match.group(1)
                    # Supprimer tout le HTML et les attributs
                    address = re.sub(r'<[^>]*>', '', address)
                    address = re.sub(r'btnTel[^\s]*', '', address)  
                    address = re.sub(r'class=[^\s]*', '', address)
                    address = re.sub(r'"[^"]*"', '', address)
                    # Nettoyer les espaces et caractères spéciaux
                    address = re.sub(r'\s+', ' ', address)
                    # Trouver seulement la partie adresse valide (numéro + rue + code postal + ville)
                    clean_match = re.search(r'(\d+[^\d]*[A-Za-zÀ-ÿ\s]+\d{5}\s+[A-Z][A-Z\s]+)', address)
                    if clean_match:
                        address = clean_match.group(1).strip()
                    else:
                        address = re.sub(r'[^A-Za-z0-9\sÀ-ÿ]+', ' ', address).strip()
                        address = re.sub(r'\s+', ' ', address)
                    if 10 < len(address) < 200:
                        data['adresse'] = address
                        break
            
            # Extraire l'email (si présent)
            email_patterns = [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            ]
            
            for pattern in email_patterns:
                match = re.search(pattern, page_html)
                if match:
                    email = match.group(1) if pattern.startswith('mailto') else match.group(0)
                    # Vérifier que ce n'est pas un email générique du site
                    if not any(generic in email.lower() for generic in ['contact@', 'info@', 'webmaster@']):
                        data['email'] = email
                        break
            
            # Extraire l'année d'inscription (si mentionnée)
            inscription_patterns = [
                r'inscrit[e]?\s+(?:au\s+barreau\s+)?(?:depuis\s+|en\s+)?(\d{4})',
                r'inscription\s*:?\s*(\d{4})',
                r'barreau\s+(?:depuis\s+|en\s+)?(\d{4})',
                r'serment\s+(?:le\s+)?(\d{4})',
                r'assermenté[e]?\s+(?:en\s+)?(\d{4})'
            ]
            
            for pattern in inscription_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    year = int(match)
                    if 1950 <= year <= 2024:  # Années raisonnables
                        data['annee_inscription'] = match
                        break
                if data['annee_inscription']:
                    break
            
            # Recherche spécifique de spécialisations sur cette architecture de site
            # Ce site n'affiche pas les spécialisations détaillées sur les fiches publiques
            # On va chercher uniquement des mentions explicites de domaines juridiques
            
            specializations = []
            
            # Chercher des domaines juridiques spécifiques dans le contenu principal uniquement
            main_content = soup.find('div', {'class': re.compile(r'content|main|fiche')})
            content_text = main_content.get_text() if main_content else page_text
            
            # Patterns très spécifiques pour éviter le bruit
            legal_domains = [
                r'droit\s+civil(?!.*intervention)',
                r'droit\s+pénal(?!.*intervention)', 
                r'droit\s+commercial(?!.*intervention)',
                r'droit\s+du\s+travail(?!.*intervention)',
                r'droit\s+de\s+la\s+famille(?!.*intervention)',
                r'droit\s+immobilier(?!.*intervention)',
                r'droit\s+fiscal(?!.*intervention)',
                r'droit\s+des\s+affaires(?!.*intervention)',
                r'droit\s+social(?!.*intervention)',
                r'droit\s+administratif(?!.*intervention)'
            ]
            
            for pattern in legal_domains:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                for match in matches:
                    if match and len(match) > 5:
                        clean_match = match.strip().title()
                        if clean_match not in specializations:
                            specializations.append(clean_match)
            
            # Si aucune spécialisation spécifique trouvée, laisser vide
            # (mieux vaut pas de donnée que de fausses données)
            if specializations:
                # Limiter à 3 domaines maximum
                final_specs = specializations[:3]
                data['specialisations'] = '; '.join(final_specs)
                data['competences'] = data['specialisations']
                data['activites_dominantes'] = data['specialisations']
            # Sinon, on laisse les champs vides
            
            # Structure par défaut
            data['structure'] = 'Avocat'
            
            print(f"✅ {filename}: {data['nom_complet']}")
            return data
            
        except Exception as e:
            filename = lawyer_url.split('/')[-1] if lawyer_url else "unknown"
            print(f"❌ {filename}: {e}")
            return None

    def run_scraping(self, limit=None):
        """Lance le scraping complet"""
        limit_text = f" (limite: {limit})" if limit else ""
        print(f"🚀 Début du scraping{limit_text}")
        
        # Récupérer la liste des avocats
        lawyer_links = self.get_lawyer_links(limit=limit)
        
        if not lawyer_links:
            print("❌ Aucun lien d'avocat trouvé")
            return False
        
        print(f"📊 {len(lawyer_links)} avocats à traiter")
        
        # Extraire les détails de chaque avocat
        for i, lawyer_url in enumerate(lawyer_links, 1):
            print(f"--- Avocat {i}/{len(lawyer_links)} ---", end=" ")
            
            lawyer_data = self.extract_lawyer_details(lawyer_url)
            if lawyer_data:
                self.avocats_data.append(lawyer_data)
            
            # Pause entre les requêtes pour éviter de surcharger le serveur
            if i % 10 == 0:  # Pause plus longue tous les 10 avocats
                print("💤 Pause")
                time.sleep(random.uniform(2, 4))
            else:
                time.sleep(random.uniform(0.5, 1.5))
        
        # Sauvegarder les résultats
        self.save_results()
        
        return True

    def save_results(self):
        """Sauvegarde les résultats dans différents formats"""
        if not self.avocats_data:
            print("❌ Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV avec séparation correcte des colonnes
        df = pd.DataFrame(self.avocats_data)
        csv_file = f"SARREGUEMINES_COMPLET_{len(self.avocats_data)}_avocats_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"💾 CSV sauvegardé: {csv_file}")
        
        # JSON
        json_file = f"SARREGUEMINES_COMPLET_{len(self.avocats_data)}_avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.avocats_data, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON sauvegardé: {json_file}")
        
        # Emails uniquement (si trouvés)
        emails = [data['email'] for data in self.avocats_data if data.get('email')]
        unique_emails = list(set(emails))
        
        if unique_emails:
            emails_file = f"SARREGUEMINES_EMAILS_{timestamp}.txt"
            with open(emails_file, 'w', encoding='utf-8') as f:
                for email in sorted(unique_emails):
                    f.write(f"{email}\n")
            print(f"📧 Emails sauvegardés: {emails_file} ({len(unique_emails)} uniques)")
        
        # Rapport détaillé
        rapport_file = f"SARREGUEMINES_RAPPORT_COMPLET_{timestamp}.txt"
        with open(rapport_file, 'w', encoding='utf-8') as f:
            f.write("=== RAPPORT SCRAPING BARREAU DE SARREGUEMINES ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"URL source: {self.start_url}\n")
            f.write(f"Nombre total d'avocats extraits: {len(self.avocats_data)}\n")
            f.write(f"Nombre d'emails trouvés: {len(unique_emails)}\n\n")
            
            # Statistiques par champ
            fields_stats = {}
            for field in ['prenom', 'nom', 'annee_inscription', 'telephone', 'email', 'adresse']:
                count = len([d for d in self.avocats_data if d.get(field)])
                percentage = (count / len(self.avocats_data)) * 100
                fields_stats[field] = {'count': count, 'percentage': percentage}
                f.write(f"Champ '{field}' rempli: {count}/{len(self.avocats_data)} ({percentage:.1f}%)\n")
            
            # Exemples de prénoms composés détectés
            prenoms_composes = [d for d in self.avocats_data if d.get('prenom') and ('-' in d['prenom'] or ' ' in d['prenom'])]
            if prenoms_composes:
                f.write(f"\n=== PRÉNOMS COMPOSÉS DÉTECTÉS ({len(prenoms_composes)}) ===\n")
                for data in prenoms_composes[:10]:
                    f.write(f"- {data['prenom']} {data['nom']}\n")
            
            # Exemples de noms composés
            noms_composes = [d for d in self.avocats_data if d.get('nom') and (' ' in d['nom'] or '-' in d['nom'])]
            if noms_composes:
                f.write(f"\n=== NOMS COMPOSÉS DÉTECTÉS ({len(noms_composes)}) ===\n")
                for data in noms_composes[:10]:
                    f.write(f"- {data['prenom']} {data['nom']}\n")
            
            f.write(f"\n=== EXEMPLES D'AVOCATS COMPLETS ===\n")
            for i, data in enumerate(self.avocats_data[:10], 1):
                f.write(f"\n{i}. {data['nom_complet']}\n")
                f.write(f"   Prénom: '{data.get('prenom', '')}'\n")
                f.write(f"   Nom: '{data.get('nom', '')}'\n")
                f.write(f"   Téléphone: {data.get('telephone', 'N/A')}\n")
                f.write(f"   Adresse: {data.get('adresse', 'N/A')[:60]}...\n")
                f.write(f"   Email: {data.get('email', 'N/A')}\n")
                f.write(f"   Année: {data.get('annee_inscription', 'N/A')}\n")
                f.write(f"   Source: {data.get('source_url', 'N/A')}\n")
        
        print(f"📋 Rapport sauvegardé: {rapport_file}")

def main():
    print("🎯 SCRAPER BARREAU DE SARREGUEMINES")
    print("=" * 50)
    
    # Vérifier les arguments
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"🧪 Mode test avec {limit} avocats")
        except ValueError:
            print("🚀 Mode production complet")
    else:
        print("🚀 Mode production complet")
    
    scraper = SarregueminesScraper()
    success = scraper.run_scraping(limit=limit)
    
    if success:
        print(f"\n✅ Scraping terminé avec succès!")
        print(f"📊 {len(scraper.avocats_data)} avocats extraits")
        
        # Statistiques rapides
        emails_found = len([d for d in scraper.avocats_data if d.get('email')])
        years_found = len([d for d in scraper.avocats_data if d.get('annee_inscription')])
        prenoms_composes = len([d for d in scraper.avocats_data if d.get('prenom') and '-' in d['prenom']])
        
        print(f"📧 {emails_found} emails trouvés")
        print(f"📅 {years_found} années d'inscription trouvées")
        print(f"👥 {prenoms_composes} prénoms composés gérés")
    else:
        print(f"\n❌ Échec du scraping")

if __name__ == "__main__":
    main()