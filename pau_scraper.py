#!/usr/bin/env python3
"""
Scraper CORRIGÉ pour le Barreau de Pau - VERSION ROBUSTE
Extraction simple et efficace avec séparation prénom/nom correcte
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import re
from datetime import datetime
import time
import random
from urllib.parse import urljoin

class PauBarScraper:
    def __init__(self, max_lawyers=None):
        """
        Scraper robuste pour le Barreau de Pau
        """
        self.base_url = "https://avocats-pau.fr"
        self.directory_url = "https://avocats-pau.fr/avocat/"
        self.max_lawyers = max_lawyers
        self.lawyers_data = []
        self.errors = []
        
        # Session HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        print(f"🚀 SCRAPER PAU - VERSION CORRIGÉE")
        if max_lawyers:
            print(f"Limite: {max_lawyers} avocats")

    def clean_text(self, text):
        """Nettoie un texte"""
        if not text:
            return ""
        # Supprimer les caractères problématiques
        text = re.sub(r'[|\n\r\t]', ' ', str(text))
        return ' '.join(text.strip().split())

    def extract_lawyers_list(self):
        """Extrait la liste des avocats"""
        try:
            print(f"🌐 Récupération de la liste des avocats...")
            response = self.session.get(self.directory_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver les articles avocat
            lawyer_articles = soup.find_all('article', class_='avocat')
            
            lawyers_list = []
            for article in lawyer_articles:
                title_link = article.find('a', {'title': True})
                if title_link:
                    href = title_link.get('href')
                    title = title_link.get('title', '').strip()
                    
                    if href and title:
                        full_url = href if href.startswith('http') else urljoin(self.base_url, href)
                        lawyers_list.append({
                            'name': title,
                            'url': full_url
                        })
            
            print(f"✓ {len(lawyers_list)} avocats trouvés")
            
            if self.max_lawyers:
                lawyers_list = lawyers_list[:self.max_lawyers]
                print(f"ℹ Limité à {self.max_lawyers} avocats")
            
            return lawyers_list
            
        except Exception as e:
            print(f"✗ Erreur liste: {e}")
            return []

    def extract_name_simple(self, full_name):
        """Extraction robuste FINAL du prénom et nom"""
        try:
            # Nettoyer le nom
            name = self.clean_text(full_name)
            name = re.sub(r'^(Me\.?|Maître|M\.)\s*', '', name, flags=re.IGNORECASE)
            name = re.sub(r'\s*[-–]\s*Avocat\s+(honoraire|Honoraire).*$', '', name)
            
            # Séparer les mots
            words = name.split()
            if not words:
                return '', name
            
            if len(words) == 1:
                return '', words[0]
            
            # NOUVELLE LOGIQUE : chercher le prénom (dernier mot non entièrement en majuscules)
            # Format typique du site : "DUPONT Pierre" ou "MARTIN Marie-Claire"
            
            # Cas spéciaux : noms composés avec DIT
            if 'DIT' in name.upper():
                # Ex: "MASSOU DIT LABAQUERE Maripierre" -> nom="MASSOU DIT LABAQUERE", prenom="Maripierre"
                dit_parts = name.split()
                # Chercher le dernier mot qui n'est pas tout en majuscules
                prenom_words = []
                nom_words = []
                
                for i in range(len(dit_parts)-1, -1, -1):  # De la fin vers le début
                    if dit_parts[i].isupper() or dit_parts[i] in ['DIT', 'DE', 'DU', 'DES', 'LA', 'LE']:
                        nom_words.insert(0, dit_parts[i])
                    else:
                        prenom_words = dit_parts[i:]
                        break
                
                if prenom_words:
                    nom = ' '.join(nom_words)
                    prenom = ' '.join(prenom_words)
                else:
                    # Fallback
                    nom = ' '.join(dit_parts[:-1])
                    prenom = dit_parts[-1]
            
            # Cas spéciaux : noms avec tirets (ex: "ANEROT-BAYLAUCQ Valérie")
            elif any('-' in word for word in words):
                # Le dernier mot non entièrement en majuscules = prénom
                for i in range(len(words)-1, -1, -1):
                    if not words[i].isupper():
                        nom = ' '.join(words[:i])
                        prenom = ' '.join(words[i:])
                        break
                else:
                    # Tous en majuscules : dernier = prénom
                    nom = ' '.join(words[:-1])
                    prenom = words[-1].title()  # Mettre en forme normale
            
            # Cas général
            else:
                # Chercher le dernier groupe de mots qui ne sont pas entièrement en majuscules
                # Ex: "DUPONT Pierre" -> nom="DUPONT", prenom="Pierre"
                # Ex: "MARTIN Jean-Claude" -> nom="MARTIN", prenom="Jean-Claude"
                
                prenom_start = len(words)
                for i in range(len(words)-1, -1, -1):
                    if not words[i].isupper():
                        prenom_start = i
                    else:
                        break
                
                if prenom_start < len(words):
                    nom = ' '.join(words[:prenom_start]) if prenom_start > 0 else words[0]
                    prenom = ' '.join(words[prenom_start:])
                else:
                    # Tous les mots sont en majuscules, supposer dernier = prénom
                    nom = ' '.join(words[:-1])
                    prenom = words[-1].title()
            
            return self.clean_text(prenom), self.clean_text(nom)
            
        except Exception as e:
            print(f"⚠ Erreur nom: {e}")
            return '', self.clean_text(full_name)

    def extract_lawyer_details(self, lawyer_info, index):
        """Extrait les détails d'un avocat"""
        try:
            print(f"📄 [{index}] {lawyer_info['name'][:40]}...")
            
            response = self.session.get(lawyer_info['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()
            
            # Initialiser
            lawyer_data = {
                'prenom': '',
                'nom': '',
                'email': '',
                'telephone': '',
                'adresse': '',
                'annee_inscription': '',
                'specialisations': '',
                'structure': '',
                'source': lawyer_info['url']
            }
            
            # 1. Nom et prénom
            prenom, nom = self.extract_name_simple(lawyer_info['name'])
            lawyer_data['prenom'] = prenom
            lawyer_data['nom'] = nom
            
            # 2. Email
            email_matches = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_text)
            if email_matches:
                lawyer_data['email'] = email_matches[0]
            
            # 3. Téléphone
            phone_matches = re.findall(r'(0[0-9\s\-\.]{8,})', page_text)
            if phone_matches:
                phone = phone_matches[0]
                # Formatage simple
                digits = re.sub(r'[^\d]', '', phone)
                if len(digits) == 10:
                    formatted = f"{digits[:2]}.{digits[2:4]}.{digits[4:6]}.{digits[6:8]}.{digits[8:10]}"
                    lawyer_data['telephone'] = formatted
                else:
                    lawyer_data['telephone'] = self.clean_text(phone)
            
            # 4. Année d'inscription
            year_matches = re.findall(r'inscrit[^0-9]*(\d{4})|(\d{4})[^0-9]*inscrit', page_text, re.IGNORECASE)
            for match in year_matches:
                year = match[0] or match[1]
                year_int = int(year)
                if 1950 <= year_int <= 2024:
                    lawyer_data['annee_inscription'] = year
                    break
            
            # 5. Adresse
            address_patterns = [
                r'(\d+[^,\n]*(?:rue|avenue|place|boulevard)[^,\n]*)',
                r'([^,\n]*(?:rue|avenue|place|boulevard)[^,\n]*\d+)',
                r'([^,\n]*64000[^,\n]*)',
                r'([^,\n]*Pau[^,\n]*64[0-9]{3}[^,\n]*)'
            ]
            for pattern in address_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    address = self.clean_text(matches[0])
                    if 10 < len(address) < 150:
                        lawyer_data['adresse'] = address
                        break
            
            # 6. Structure
            structure_patterns = [
                r'(SCP[^,\n]{5,60})',
                r'(SELARL[^,\n]{5,60})',
                r'(Cabinet[^,\n]{5,60})',
                r'(CABINET[^,\n]{5,60})'
            ]
            for pattern in structure_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    structure = self.clean_text(matches[0])
                    if len(structure) > 5:
                        lawyer_data['structure'] = structure
                        break
            
            # 7. Spécialisations
            specializations = []
            droit_matches = re.findall(r'(droit[^,\.\n]{5,50})', page_text, re.IGNORECASE)
            for match in droit_matches:
                spec = self.clean_text(match)
                if 10 < len(spec) < 80 and spec not in specializations:
                    specializations.append(spec)
                    if len(specializations) >= 3:
                        break
            
            if specializations:
                lawyer_data['specialisations'] = '; '.join(specializations)
            
            # Status
            status_email = "✓" if lawyer_data['email'] else "✗"
            status_phone = "✓" if lawyer_data['telephone'] else "✗"
            print(f"   📧 {status_email} | 📞 {status_phone} | ✓")
            
            return lawyer_data
            
        except Exception as e:
            print(f"✗ Erreur [{index}]: {e}")
            prenom, nom = self.extract_name_simple(lawyer_info['name'])
            return {
                'prenom': prenom,
                'nom': nom,
                'email': '',
                'telephone': '',
                'adresse': '',
                'annee_inscription': '',
                'specialisations': '',
                'structure': '',
                'source': lawyer_info['url']
            }

    def save_results(self):
        """Sauvegarde les résultats"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # CSV propre
            csv_filename = f"pau_CORRIGE_FINAL_{len(self.lawyers_data)}_avocats_{timestamp}.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['prenom', 'nom', 'email', 'telephone', 'adresse', 'annee_inscription', 'specialisations', 'structure', 'source']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.lawyers_data:
                    # Nettoyage final
                    clean_row = {}
                    for field in fieldnames:
                        value = lawyer.get(field, '')
                        clean_row[field] = self.clean_text(value) if value else ''
                    writer.writerow(clean_row)
            
            # JSON
            json_filename = f"pau_CORRIGE_FINAL_{len(self.lawyers_data)}_avocats_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.lawyers_data, jsonfile, ensure_ascii=False, indent=2)
            
            # Emails uniquement
            emails_filename = f"pau_CORRIGE_EMAILS_{timestamp}.txt"
            emails_count = 0
            with open(emails_filename, 'w', encoding='utf-8') as emailfile:
                for lawyer in self.lawyers_data:
                    if lawyer.get('email'):
                        emailfile.write(f"{lawyer['email']}\n")
                        emails_count += 1
            
            # Rapport
            report_filename = f"pau_CORRIGE_RAPPORT_{timestamp}.txt"
            with open(report_filename, 'w', encoding='utf-8') as report:
                report.write(f"RAPPORT CORRIGÉ - BARREAU DE PAU\n")
                report.write(f"=" * 50 + "\n\n")
                report.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                report.write(f"Avocats traités: {len(self.lawyers_data)}\n")
                report.write(f"Emails trouvés: {emails_count}\n")
                
                phones_found = sum(1 for l in self.lawyers_data if l.get('telephone'))
                addresses_found = sum(1 for l in self.lawyers_data if l.get('adresse'))
                years_found = sum(1 for l in self.lawyers_data if l.get('annee_inscription'))
                specializations_found = sum(1 for l in self.lawyers_data if l.get('specialisations'))
                
                report.write(f"Téléphones: {phones_found}\n")
                report.write(f"Adresses: {addresses_found}\n")
                report.write(f"Années: {years_found}\n")
                report.write(f"Spécialisations: {specializations_found}\n\n")
                
                report.write("ÉCHANTILLON (10 premiers):\n")
                for i, lawyer in enumerate(self.lawyers_data[:10], 1):
                    report.write(f"\n{i}. {lawyer['prenom']} {lawyer['nom']}\n")
                    report.write(f"   Email: {lawyer['email'] or 'N/A'}\n")
                    report.write(f"   Tél: {lawyer['telephone'] or 'N/A'}\n")
                    report.write(f"   Spé: {lawyer['specialisations'][:50] + '...' if len(lawyer.get('specialisations', '')) > 50 else lawyer.get('specialisations', 'N/A')}\n")
            
            print(f"\n🎉 FICHIERS GÉNÉRÉS:")
            print(f"📄 CSV: {csv_filename}")
            print(f"📄 JSON: {json_filename}")
            print(f"📧 Emails: {emails_filename} ({emails_count} emails)")
            print(f"📋 Rapport: {report_filename}")
            
            return csv_filename, json_filename, emails_filename, report_filename
            
        except Exception as e:
            print(f"✗ Erreur sauvegarde: {e}")
            return None, None, None, None

    def run_production(self):
        """Lance l'extraction corrigée"""
        try:
            start_time = time.time()
            print(f"\n{'='*60}")
            print(f"🚀 EXTRACTION CORRIGÉE - BARREAU DE PAU")
            print(f"{'='*60}")
            
            # Liste des avocats
            lawyers_list = self.extract_lawyers_list()
            if not lawyers_list:
                print("❌ Aucun avocat trouvé")
                return False
            
            print(f"\n📋 EXTRACTION EN COURS...")
            
            # Extraction détaillée
            for i, lawyer_info in enumerate(lawyers_list, 1):
                lawyer_data = self.extract_lawyer_details(lawyer_info, i)
                self.lawyers_data.append(lawyer_data)
                
                # Sauvegarde périodique
                if i % 50 == 0:
                    print(f"\n📊 Progression: {i}/{len(lawyers_list)} ({i/len(lawyers_list)*100:.1f}%)")
                    emails_so_far = sum(1 for l in self.lawyers_data if l['email'])
                    print(f"📧 Emails: {emails_so_far}")
                
                # Petite pause
                time.sleep(random.uniform(0.3, 0.8))
            
            # Sauvegarde finale
            print(f"\n💾 Sauvegarde finale...")
            self.save_results()
            
            # Stats finales
            end_time = time.time()
            duration = end_time - start_time
            emails_total = sum(1 for l in self.lawyers_data if l['email'])
            
            print(f"\n🎯 EXTRACTION CORRIGÉE TERMINÉE!")
            print(f"⏱ Durée: {duration/60:.1f} min")
            print(f"✅ Avocats: {len(self.lawyers_data)}")
            print(f"📧 Emails: {emails_total}")
            print(f"📞 Taux succès: {emails_total/len(self.lawyers_data)*100:.1f}%")
            
            return True
            
        except Exception as e:
            print(f"💥 Erreur critique: {e}")
            return False

def main():
    """Fonction principale"""
    print("SCRAPER BARREAU DE PAU - VERSION CORRIGÉE")
    
    try:
        # Créer le scraper (sans limite = tous les avocats)
        scraper = PauBarScraper(max_lawyers=None)
        
        # Lancer l'extraction
        success = scraper.run_production()
        
        if success:
            print("\n🏆 EXTRACTION CORRIGÉE RÉUSSIE!")
        else:
            print("\n⚠️ Extraction échouée")
            
    except KeyboardInterrupt:
        print("\n⏹ Arrêté par l'utilisateur")
    except Exception as e:
        print(f"\n💥 Erreur: {e}")

if __name__ == "__main__":
    main()