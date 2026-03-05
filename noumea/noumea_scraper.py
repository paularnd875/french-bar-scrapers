#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPER NOUMEA - VERSION FINALE ULTRA-CORRIGÉE
Récupération COMPLÈTE avec activités dominantes
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime
import json
import sys

class NoumeeaFichesFinalScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.lawyers_data = []
        
    def get_lawyer_urls(self):
        """Liste des URLs des fiches avocats"""
        return [
            "https://www.barreau-noumea.nc/annuaire/125",
            "https://www.barreau-noumea.nc/annuaire/124",
            "https://www.barreau-noumea.nc/annuaire/11053",
            "https://www.barreau-noumea.nc/annuaire/123",
            "https://www.barreau-noumea.nc/annuaire/122",
            "https://www.barreau-noumea.nc/annuaire/120",
            "https://www.barreau-noumea.nc/annuaire/119",
            "https://www.barreau-noumea.nc/annuaire/118",
            "https://www.barreau-noumea.nc/annuaire/117",
            "https://www.barreau-noumea.nc/annuaire/599419",
            "https://www.barreau-noumea.nc/annuaire/114",
            "https://www.barreau-noumea.nc/annuaire/113",
            "https://www.barreau-noumea.nc/annuaire/910119",
            "https://www.barreau-noumea.nc/annuaire/35",
            "https://www.barreau-noumea.nc/annuaire/126",
            "https://www.barreau-noumea.nc/annuaire/112",
            "https://www.barreau-noumea.nc/annuaire/111",
            "https://www.barreau-noumea.nc/annuaire/109",
            "https://www.barreau-noumea.nc/annuaire/107",
            "https://www.barreau-noumea.nc/annuaire/106",
            "https://www.barreau-noumea.nc/annuaire/817299",
            "https://www.barreau-noumea.nc/annuaire/105",
            "https://www.barreau-noumea.nc/annuaire/104",
            "https://www.barreau-noumea.nc/annuaire/18",
            "https://www.barreau-noumea.nc/annuaire/102",
            "https://www.barreau-noumea.nc/annuaire/130",
            "https://www.barreau-noumea.nc/annuaire/101",
            "https://www.barreau-noumea.nc/annuaire/910535",
            "https://www.barreau-noumea.nc/annuaire/515335",
            "https://www.barreau-noumea.nc/annuaire/249051",
            "https://www.barreau-noumea.nc/annuaire/100",
            "https://www.barreau-noumea.nc/annuaire/99",
            "https://www.barreau-noumea.nc/annuaire/98",
            "https://www.barreau-noumea.nc/annuaire/33101",
            "https://www.barreau-noumea.nc/annuaire/97",
            "https://www.barreau-noumea.nc/annuaire/95",
            "https://www.barreau-noumea.nc/annuaire/94",
            "https://www.barreau-noumea.nc/annuaire/93",
            "https://www.barreau-noumea.nc/annuaire/92",
            "https://www.barreau-noumea.nc/annuaire/214251",
            "https://www.barreau-noumea.nc/annuaire/90",
            "https://www.barreau-noumea.nc/annuaire/89",
            "https://www.barreau-noumea.nc/annuaire/88",
            "https://www.barreau-noumea.nc/annuaire/86",
            "https://www.barreau-noumea.nc/annuaire/85",
            "https://www.barreau-noumea.nc/annuaire/84",
            "https://www.barreau-noumea.nc/annuaire/82",
            "https://www.barreau-noumea.nc/annuaire/204601",
            "https://www.barreau-noumea.nc/annuaire/81",
            "https://www.barreau-noumea.nc/annuaire/79",
            "https://www.barreau-noumea.nc/annuaire/78",
            "https://www.barreau-noumea.nc/annuaire/77",
            "https://www.barreau-noumea.nc/annuaire/11052",
            "https://www.barreau-noumea.nc/annuaire/75",
            "https://www.barreau-noumea.nc/annuaire/71",
            "https://www.barreau-noumea.nc/annuaire/74",
            "https://www.barreau-noumea.nc/annuaire/73",
            "https://www.barreau-noumea.nc/annuaire/72",
            "https://www.barreau-noumea.nc/annuaire/117151",
            "https://www.barreau-noumea.nc/annuaire/485175",
            "https://www.barreau-noumea.nc/annuaire/69",
            "https://www.barreau-noumea.nc/annuaire/68",
            "https://www.barreau-noumea.nc/annuaire/67",
            "https://www.barreau-noumea.nc/annuaire/65",
            "https://www.barreau-noumea.nc/annuaire/64",
            "https://www.barreau-noumea.nc/annuaire/62",
            "https://www.barreau-noumea.nc/annuaire/61",
            "https://www.barreau-noumea.nc/annuaire/135",
            "https://www.barreau-noumea.nc/annuaire/351251",
            "https://www.barreau-noumea.nc/annuaire/60",
            "https://www.barreau-noumea.nc/annuaire/288651",
            "https://www.barreau-noumea.nc/annuaire/254451",
            "https://www.barreau-noumea.nc/annuaire/58",
            "https://www.barreau-noumea.nc/annuaire/57",
            "https://www.barreau-noumea.nc/annuaire/56",
            "https://www.barreau-noumea.nc/annuaire/55",
            "https://www.barreau-noumea.nc/annuaire/943711",
            "https://www.barreau-noumea.nc/annuaire/53",
            "https://www.barreau-noumea.nc/annuaire/52",
            "https://www.barreau-noumea.nc/annuaire/127751",
            "https://www.barreau-noumea.nc/annuaire/51",
            "https://www.barreau-noumea.nc/annuaire/50",
            "https://www.barreau-noumea.nc/annuaire/49",
            "https://www.barreau-noumea.nc/annuaire/48",
            "https://www.barreau-noumea.nc/annuaire/47",
            "https://www.barreau-noumea.nc/annuaire/46",
            "https://www.barreau-noumea.nc/annuaire/796447",
            "https://www.barreau-noumea.nc/annuaire/44",
            "https://www.barreau-noumea.nc/annuaire/43",
            "https://www.barreau-noumea.nc/annuaire/45",
            "https://www.barreau-noumea.nc/annuaire/65801",
            "https://www.barreau-noumea.nc/annuaire/40",
            "https://www.barreau-noumea.nc/annuaire/39",
            "https://www.barreau-noumea.nc/annuaire/748555",
            "https://www.barreau-noumea.nc/annuaire/388151",
            "https://www.barreau-noumea.nc/annuaire/37",
            "https://www.barreau-noumea.nc/annuaire/38",
            "https://www.barreau-noumea.nc/annuaire/11701",
            "https://www.barreau-noumea.nc/annuaire/34",
            "https://www.barreau-noumea.nc/annuaire/32",
            "https://www.barreau-noumea.nc/annuaire/31",
            "https://www.barreau-noumea.nc/annuaire/30",
            "https://www.barreau-noumea.nc/annuaire/29",
            "https://www.barreau-noumea.nc/annuaire/28",
            "https://www.barreau-noumea.nc/annuaire/71251",
            "https://www.barreau-noumea.nc/annuaire/27",
            "https://www.barreau-noumea.nc/annuaire/26",
            "https://www.barreau-noumea.nc/annuaire/25",
            "https://www.barreau-noumea.nc/annuaire/24",
            "https://www.barreau-noumea.nc/annuaire/23",
            "https://www.barreau-noumea.nc/annuaire/132",
            "https://www.barreau-noumea.nc/annuaire/22",
            "https://www.barreau-noumea.nc/annuaire/21",
            "https://www.barreau-noumea.nc/annuaire/122401",
            "https://www.barreau-noumea.nc/annuaire/20",
            "https://www.barreau-noumea.nc/annuaire/318251",
            "https://www.barreau-noumea.nc/annuaire/17",
            "https://www.barreau-noumea.nc/annuaire/16",
            "https://www.barreau-noumea.nc/annuaire/92202",
            "https://www.barreau-noumea.nc/annuaire/14",
            "https://www.barreau-noumea.nc/annuaire/133",
            "https://www.barreau-noumea.nc/annuaire/12",
            "https://www.barreau-noumea.nc/annuaire/23051",
            "https://www.barreau-noumea.nc/annuaire/11",
            "https://www.barreau-noumea.nc/annuaire/10",
            "https://www.barreau-noumea.nc/annuaire/9",
            "https://www.barreau-noumea.nc/annuaire/13301",
            "https://www.barreau-noumea.nc/annuaire/1068563",
            "https://www.barreau-noumea.nc/annuaire/98851",
            "https://www.barreau-noumea.nc/annuaire/7"
        ]
    
    def extract_lawyer_details(self, url):
        """Extraction FINALE avec activités dominantes"""
        try:
            lawyer_id = url.split('/')[-1]
            print(f"📋 Extraction fiche {lawyer_id}...")
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"   ❌ Erreur HTTP {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()
            page_html = str(soup)
            
            # Structure des données
            lawyer_data = {
                'id': lawyer_id,
                'url': url,
                'nom_complet': '',
                'prenom': '',
                'nom': '',
                'email': '',
                'telephone': '',
                'fax': '',
                'adresse_complete': '',
                'adresse_ligne1': '',
                'adresse_ligne2': '',
                'code_postal': '',
                'ville': '',
                'pays': 'Nouvelle-Calédonie',
                'specialisations': '',
                'activites_dominantes': '',
                'annee_serment': '',
                'cabinet': '',
                'activite_dominante': '',
                'langues': '',
                'site_web': '',
                'photo_url': '',
                'raw_text': page_text[:500]
            }
            
            # NOM COMPLET
            card_title = soup.select_one('h3.card-title')
            if card_title:
                name_text = card_title.get_text().strip()
                lawyer_data['nom_complet'] = name_text
                print(f"     ✅ Nom trouvé: {name_text}")
            
            # SÉPARATION PRÉNOM/NOM
            if lawyer_data['nom_complet']:
                prenom, nom = self.parse_name_improved(lawyer_data['nom_complet'])
                lawyer_data['prenom'] = prenom
                lawyer_data['nom'] = nom
            
            # 🎯 ACTIVITÉS DOMINANTES - EXTRACTION CIBLÉE
            activities_found = []
            
            # Méthode 1: Chercher les badges dans la section "Activité dominante"
            activity_section = soup.find('span', class_='bold', string='Activité dominante')
            if activity_section:
                # Trouver le paragraphe parent
                parent_p = activity_section.find_parent('p')
                if parent_p:
                    # Extraire tous les badges
                    badges = parent_p.find_all('span', class_='badge')
                    for badge in badges:
                        activity = badge.get_text().strip()
                        if activity:
                            activities_found.append(activity)
                            
            # Méthode 2: Si pas trouvé, chercher dans le HTML
            if not activities_found:
                badge_elements = soup.find_all('span', class_='badge')
                for badge in badge_elements:
                    badge_text = badge.get_text().strip()
                    if 'droit' in badge_text.lower() or any(word in badge_text.lower() for word in ['commercial', 'civil', 'pénal', 'famille', 'immobilier', 'assurance', 'construction']):
                        activities_found.append(badge_text)
            
            if activities_found:
                lawyer_data['activites_dominantes'] = ' | '.join(activities_found)
                lawyer_data['activite_dominante'] = ', '.join(activities_found[:3])  # Maximum 3 pour la compatibilité
                print(f"     🎯 Activités trouvées: {', '.join(activities_found)}")
            else:
                print(f"     ⚠️ Aucune activité dominante trouvée")
            
            # Email
            email_patterns = [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                r'mailto:([^"\'>\s]+)'
            ]
            for pattern in email_patterns:
                matches = re.findall(pattern, page_html + " " + page_text)
                valid_emails = [e for e in matches if not any(skip in e.lower() for skip in ['bootstrap', 'google', 'example', 'test', 'noreply'])]
                if valid_emails:
                    lawyer_data['email'] = valid_emails[0]
                    break
            
            # Téléphone
            phone_patterns = [
                r'\+687[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}',
                r'687[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}',
                r'0\d[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}',
                r'Tél[^:]*:[\s]*([0-9\s\-\.\+]{10,})',
                r'Tel[^:]*:[\s]*([0-9\s\-\.\+]{10,})'
            ]
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    phone = re.sub(r'[^\d\+]', '', matches[0])
                    if len(phone) >= 6:
                        lawyer_data['telephone'] = matches[0].strip()
                        break
            
            # ANNÉE DE SERMENT
            serment_span = soup.find('span')
            if serment_span:
                span_text = serment_span.get_text().strip()
                if re.match(r'^\d{4}$', span_text):
                    lawyer_data['annee_serment'] = span_text
            
            if not lawyer_data['annee_serment']:
                serment_patterns = [
                    r"L'avocat a prêté serment en (\d{4})",
                    r"serment.*?(\d{4})",
                    r"prestation.*?(\d{4})",
                    r"inscription.*?(\d{4})"
                ]
                
                for pattern in serment_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        lawyer_data['annee_serment'] = match.group(1)
                        break
            
            # Adresse
            address_section = soup.find('span', class_='bold', string='Adresse physique')
            if address_section:
                parent_p = address_section.find_parent('p')
                if parent_p:
                    address_text = parent_p.get_text().replace('Adresse physique', '').strip()
                    lawyer_data['adresse_complete'] = address_text
                    if 'nouméa' in address_text.lower():
                        lawyer_data['ville'] = 'Nouméa'
                        lawyer_data['code_postal'] = '98800'
            
            print(f"   ✅ {lawyer_data['nom_complet']} - Email: {lawyer_data['email']} - Tel: {lawyer_data['telephone']} - Serment: {lawyer_data['annee_serment']} - Activités: {len(activities_found)}")
            return lawyer_data
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            return None
    
    def parse_name_improved(self, full_name):
        """Séparation prénom/nom"""
        full_name = full_name.strip()
        full_name = re.sub(r'^(Me|Maître|M\.|Mme|Mlle)\s+', '', full_name, flags=re.IGNORECASE)
        
        parts = full_name.split()
        if len(parts) <= 1:
            return full_name, ""
        elif len(parts) == 2:
            if parts[0].isupper() and parts[1].istitle():
                return parts[1], parts[0]  # Prénom, NOM
            elif parts[0].istitle() and parts[1].isupper():
                return parts[0], parts[1]  # Prénom, NOM
            else:
                return parts[1], parts[0]
        else:
            if parts[0].isupper():
                i = 1
                while i < len(parts) and (parts[i].isupper() or parts[i].lower() in ['de', 'du', 'des', 'le', 'la']):
                    i += 1
                nom = ' '.join(parts[:i])
                prenom = ' '.join(parts[i:]) if i < len(parts) else ""
            else:
                nom = parts[-1]
                prenom = ' '.join(parts[:-1])
            
            return prenom, nom
    
    def run_extraction(self, test_mode=False):
        """Extraction FINALE"""
        print("🚀 EXTRACTION FINALE ULTRA-CORRIGÉE - BARREAU NOUMÉA")
        print("🎯 AVEC ACTIVITÉS DOMINANTES")
        print("=" * 65)
        
        urls = self.get_lawyer_urls()
        
        if test_mode:
            urls = urls[:5]
            print(f"🧪 MODE TEST - {len(urls)} fiches")
        else:
            print(f"📋 MODE PRODUCTION - {len(urls)} fiches")
        
        successful_extractions = 0
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] {url}")
            
            lawyer_data = self.extract_lawyer_details(url)
            if lawyer_data:
                self.lawyers_data.append(lawyer_data)
                successful_extractions += 1
            
            time.sleep(0.5)
            
            if i % 20 == 0:
                print(f"\n💾 Sauvegarde intermédiaire après {i} fiches...")
                self.save_intermediate_results(i)
        
        print(f"\n✅ Extraction FINALE terminée: {successful_extractions}/{len(urls)} fiches réussies")
        
        if self.lawyers_data:
            self.save_final_results(test_mode)
        
        return self.lawyers_data
    
    def save_intermediate_results(self, count):
        """Sauvegarde intermédiaire"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"NOUMEA_FINAL_BACKUP_{count}fiches_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        print(f"   💾 Backup sauvé: {filename}")
    
    def save_final_results(self, test_mode=False):
        """Sauvegarde finale ultra-complète"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "NOUMEA_TEST_FINAL" if test_mode else "NOUMEA_PRODUCTION_FINAL"
        
        total = len(self.lawyers_data)
        
        # Statistiques
        with_email = len([l for l in self.lawyers_data if l.get('email')])
        with_phone = len([l for l in self.lawyers_data if l.get('telephone')])
        with_address = len([l for l in self.lawyers_data if l.get('adresse_complete')])
        with_specializations = len([l for l in self.lawyers_data if l.get('activites_dominantes')])
        with_year = len([l for l in self.lawyers_data if l.get('annee_serment')])
        with_names = len([l for l in self.lawyers_data if l.get('nom_complet')])
        
        # CSV
        csv_file = f"{prefix}_{total}avocats_{timestamp}.csv"
        df = pd.DataFrame(self.lawyers_data)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # JSON
        json_file = f"{prefix}_{total}avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        # Emails uniquement
        emails = list(set([l['email'] for l in self.lawyers_data if l.get('email')]))
        emails_file = f"{prefix}_EMAILS_{len(emails)}emails_{timestamp}.txt"
        with open(emails_file, 'w', encoding='utf-8') as f:
            for email in sorted(emails):
                f.write(f"{email}\n")
        
        # Activités dominantes uniquement
        activities = []
        for lawyer in self.lawyers_data:
            if lawyer.get('activites_dominantes'):
                acts = lawyer['activites_dominantes'].split(' | ')
                activities.extend(acts)
        
        unique_activities = list(set(activities))
        activities_file = f"{prefix}_ACTIVITES_{len(unique_activities)}activites_{timestamp}.txt"
        with open(activities_file, 'w', encoding='utf-8') as f:
            for activity in sorted(unique_activities):
                f.write(f"{activity}\n")
        
        # Rapport FINAL
        report_file = f"{prefix}_RAPPORT_FINAL_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("🏛️ RAPPORT EXTRACTION FINALE ULTRA-COMPLÈTE - BARREAU DE NOUMÉA\n")
            f.write("🎯 AVEC ACTIVITÉS DOMINANTES\n")
            f.write("=" * 75 + "\n\n")
            
            f.write(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"📊 Total avocats: {total}\n\n")
            
            f.write("📈 STATISTIQUES FINALES:\n")
            f.write("-" * 40 + "\n")
            f.write(f"👤 Noms complets: {with_names} ({with_names/total*100:.1f}%)\n")
            f.write(f"📧 Emails: {with_email} ({with_email/total*100:.1f}%)\n")
            f.write(f"📞 Téléphones: {with_phone} ({with_phone/total*100:.1f}%)\n")
            f.write(f"📍 Adresses: {with_address} ({with_address/total*100:.1f}%)\n")
            f.write(f"📅 Années serment: {with_year} ({with_year/total*100:.1f}%)\n")
            f.write(f"🎯 Activités dominantes: {with_specializations} ({with_specializations/total*100:.1f}%)\n\n")
            
            f.write(f"🎯 ACTIVITÉS DOMINANTES UNIQUES ({len(unique_activities)}):\n")
            f.write("-" * 50 + "\n")
            for activity in sorted(unique_activities):
                f.write(f"• {activity}\n")
            f.write("\n")
            
            f.write("📋 ÉCHANTILLON FINAL:\n")
            f.write("-" * 25 + "\n")
            for i, lawyer in enumerate(self.lawyers_data[:5]):
                f.write(f"\n{i+1}. {lawyer['nom_complet']}\n")
                f.write(f"   Prénom: {lawyer.get('prenom', 'N/A')}\n")
                f.write(f"   Nom: {lawyer.get('nom', 'N/A')}\n")
                f.write(f"   Email: {lawyer.get('email', 'N/A')}\n")
                f.write(f"   Téléphone: {lawyer.get('telephone', 'N/A')}\n")
                f.write(f"   Année serment: {lawyer.get('annee_serment', 'N/A')}\n")
                f.write(f"   🎯 Activités: {lawyer.get('activites_dominantes', 'N/A')}\n")
                f.write(f"   Adresse: {lawyer.get('adresse_complete', 'N/A')}\n")
        
        print(f"\n🎉 SAUVEGARDE FINALE ULTRA-COMPLÈTE!")
        print(f"📁 Fichiers:")
        print(f"   📊 CSV: {csv_file}")
        print(f"   📄 JSON: {json_file}")
        print(f"   📧 Emails: {emails_file} ({len(emails)})")
        print(f"   🎯 Activités: {activities_file} ({len(unique_activities)})")
        print(f"   📋 Rapport: {report_file}")
        
        print(f"\n🏆 BILAN FINAL ULTRA-COMPLET:")
        print(f"   Total: {total} avocats")
        print(f"   Noms: {with_names} ({with_names/total*100:.1f}%)")
        print(f"   Emails: {with_email} ({with_email/total*100:.1f}%)")
        print(f"   Téléphones: {with_phone} ({with_phone/total*100:.1f}%)")
        print(f"   Années serment: {with_year} ({with_year/total*100:.1f}%)")
        print(f"   🎯 ACTIVITÉS: {with_specializations} ({with_specializations/total*100:.1f}%)")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper Final Ultra-Complet Nouméa')
    parser.add_argument('--test', action='store_true', help='Mode test (5 fiches)')
    
    args = parser.parse_args()
    
    scraper = NoumeeaFichesFinalScraper()
    scraper.run_extraction(test_mode=args.test)