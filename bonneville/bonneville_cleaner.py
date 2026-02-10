#!/usr/bin/env python3
"""
Nettoyeur et déduplicateur pour les données Bonneville
Nettoie les 166 avocats pour obtenir la liste finale propre
"""

import json
import csv
import re
from datetime import datetime
from collections import defaultdict

class BonnevilleCleaner:
    def __init__(self):
        self.clean_lawyers = []
        self.duplicates_removed = 0
        self.invalid_removed = 0
        
    def load_raw_data(self, json_filename):
        """Charge les données brutes"""
        print(f"📂 Chargement des données : {json_filename}")
        
        with open(json_filename, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        print(f"✅ {len(raw_data)} entrées chargées")
        return raw_data
    
    def clean_name(self, name):
        """Nettoie un nom"""
        if not name:
            return ""
            
        # Supprimer les préfixes/suffixes indésirables
        name = re.sub(r'^(Selarl|Scp|Selas|Sarl|Sas|Cabinet|Association|Société)\s*-?\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*-?\s*(Selarl|Scp|Selas|Sarl|Sas|Cabinet|Association|Société)$', '', name, flags=re.IGNORECASE)
        
        # Supprimer les caractères indésirables
        name = re.sub(r'[^\w\s\'-]', '', name)
        
        # Corriger les noms tronqués communs
        corrections = {
            'Stid': 'Bastid',
            'Hantélot': 'Chantelot', 
            'Udray': 'Coudray',
            'Huta': 'Plahuta',
            'Ggio': 'Boggio',
            'Hambél': 'Chambel',
            'Hambét': 'Chambet',
            'Uvard': 'Bouvard',
            'Hervé': 'Caillon',
            'Ubréuil': 'Dubreuil',
            'Ud-Marjou': 'Baud-Marjou',
            'Hristinaz': 'Christinaz',
            'Sséy-Magnifiqué': 'Pessey-Magnifique',
            'Urniér-Framborét': 'Burnier-Framboret',
            'Ël': 'Noel',
            'Solléuz': 'Le Solleuz',
            'Hon': 'Lorichon',
            'Mond': 'Raimond',
            'Happaz': 'Chappaz',
            'Uéil': 'Vercueil',
            'Hurin': 'Thurin',
            'Méuniér': 'Meunier',
            'Sépulvéda': 'Sepulveda',
            'Saugé': 'Sauge',
            'Kowski': 'Diakowski',
            'Mugniér': 'Mugnier',
            'Mbrét': 'Ombret',
            'Zia': 'Cauzia',
            'Sov': 'Volosova',
            'Hilairé': 'Hilaire',
            'Yron': 'Peyron'
        }
        
        for wrong, correct in corrections.items():
            name = re.sub(rf'\b{re.escape(wrong)}\b', correct, name, flags=re.IGNORECASE)
        
        return name.strip().title()
    
    def is_valid_lawyer_entry(self, lawyer):
        """Vérifie si l'entrée est valide"""
        # Doit avoir un email valide
        if not lawyer.get('email') or '@' not in lawyer['email']:
            return False
            
        # Doit avoir au moins un nom
        nom = lawyer.get('nom', '').strip()
        prenom = lawyer.get('prenom', '').strip()
        
        if not nom and not prenom:
            return False
            
        # Exclure les entrées qui sont clairement des structures/organisations
        excluded_terms = ['selarl', 'cabinet', 'scp', 'selas', 'sarl', 'sas', 'association', 
                         'société', 'juris', 'avocats', 'epsilon', 'arcane', 'actys']
        
        full_name = f"{nom} {prenom}".lower()
        if any(term in full_name for term in excluded_terms):
            return False
            
        # Exclure les noms trop courts ou étranges
        if len(nom) < 2 or len(prenom) < 2:
            return False
            
        return True
    
    def deduplicate_by_email(self, lawyers):
        """Déduplique par email en gardant la meilleure entrée"""
        email_groups = defaultdict(list)
        
        # Grouper par email
        for lawyer in lawyers:
            email = lawyer['email'].lower().strip()
            email_groups[email].append(lawyer)
        
        deduplicated = []
        
        for email, group in email_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Choisir la meilleure entrée du groupe
                best = self.choose_best_entry(group)
                deduplicated.append(best)
                self.duplicates_removed += len(group) - 1
                
        return deduplicated
    
    def choose_best_entry(self, group):
        """Choisit la meilleure entrée parmi les doublons"""
        # Scorer chaque entrée
        scored = []
        
        for entry in group:
            score = 0
            
            # Points pour informations complètes
            if entry.get('telephone') and len(entry['telephone']) > 8:
                score += 10
            if entry.get('ville') and len(entry['ville']) > 3:
                score += 5
            if entry.get('annee_inscription') and entry['annee_inscription'].isdigit():
                score += 3
                
            # Points pour noms propres (pas tronqués)
            nom = entry.get('nom', '')
            prenom = entry.get('prenom', '')
            
            if len(nom) > 4:
                score += 2
            if len(prenom) > 4:
                score += 2
                
            # Pénalités pour noms tronqués ou étranges
            if nom.endswith('-'):
                score -= 5
            if len(nom) <= 3:
                score -= 3
                
            scored.append((score, entry))
        
        # Retourner la meilleure
        best = max(scored, key=lambda x: x[0])[1]
        return best
    
    def enhance_with_common_names(self, lawyers):
        """Enrichit avec des noms d'avocats communs connus"""
        
        # Mapping email -> nom complet connu
        known_mappings = {
            'contact@bastid-avocat.com': ('BASTID', 'Arnaud'),
            'contact@chantelot-avocats.fr': ('CHANTELOT', 'Xavier'),
            'bonneville@scp-ballaloud.fr': ('COUDRAY', 'Véronique'),
            'plahuta@aol.com': ('PLAHUTA', 'Bernard'),
            'contact@avocats-boggio.fr': ('BOGGIO', 'Isabelle'),
            'contact@chambelassocies-avocats.fr': ('CHAMBEL', 'Sylvie'),
            'sallanches@arcane-juris.fr': ('MOLLARD-PERRIN', 'Catherine'),
            'corinne.perini@aol.com': ('PERINI', 'Corinne'),
            'l.mourot@arcane-juris.fr': ('MOUROT', 'Lionel'),
            'contact@cabinet-chambet-avocats.com': ('CHAMBET', 'Valérie'),
            'contact@cabinet-bouvard.com': ('BOUVARD', 'Alex'),
            'p.ribes@avocats-online.com': ('RIBES', 'Agnès'),
            'h.caillon@arcane-juris.fr': ('CAILLON', 'Hervé'),
            'fallion-dubreuil@wanadoo.fr': ('FALLION', 'Caroline'),
            'contact@anne-fallion-avocat.fr': ('FALLION', 'Anne'),
            'contact@peters.avocat.fr': ('PETERS', 'Marc'),
            'selarl@avocat-baudmarjou.fr': ('BAUD-MARJOU', 'Catherine'),
            'contact@avocats-cpm.fr': ('PESSEY-MAGNIFIQUE', 'Jean-François'),
            'jurismontblanc@jurismontblanc.com': ('JURIS', 'Mont-Blanc'),
            'catherine@levant-avocat.fr': ('LEVANT', 'Catherine'),
            'l.noel@actys-avocats.com': ('NOEL', 'Laetitia'),
            'contact@phdidier.avocat.fr': ('DIDIER', 'Pierre-Henri'),
            'contact@lesolleuz-avocat.com': ('LE SOLLEUZ', 'Hélène'),
            'contact@avocatlorichon.com': ('LORICHON', 'Fabian'),
            'gaellebreteau-avocat@orange.fr': ('BRETEAU', 'Gaëlle'),
            'raimond@avocats-associes.eu': ('RAIMOND', 'Antoine'),
            'cabinet@briffod-avocats.fr': ('BRIFFOD', 'Lucie'),
            'cabinet@vercueil-avocat.fr': ('VERCUEIL', 'Céline'),
            'aurelie.thurin@legisalp-avocats.fr': ('THURIN', 'Aurélie'),
            'cabinet@maschio-avocat.fr': ('MASCHIO', 'Nathalie'),
            'fmeunier-avocat@protonmail.com': ('MEUNIER', 'Frédéric'),
            'j.sepulveda@epsilon-avocats.net': ('SEPULVEDA', 'Jonathan'),
            'valerie.sauge@aol.fr': ('SAUGE', 'Valérie'),
            'diakowski.avocat@outlook.com': ('DIAKOWSKI', 'Ludmilla'),
            'ysoline.mugnier@legisalp-avocats.fr': ('MUGNIER', 'Ysoline'),
            'contact@ombret-avocat.fr': ('OMBRET', 'Amélie'),
            'j.ledan@arcane-justice.fr': ('LEDAN', 'Jessica'),
            'sarah@volosovavocat.com': ('VOLOSOVA', 'Sarah'),
            'm.hilaire@arcane-juris.fr': ('HILAIRE', 'Marjorie'),
            'peyron@avocats-boggio.fr': ('PEYRON', 'Léa'),
        }
        
        enhanced = []
        for lawyer in lawyers:
            email = lawyer['email'].lower().strip()
            
            if email in known_mappings:
                nom_correct, prenom_correct = known_mappings[email]
                lawyer['nom'] = nom_correct
                lawyer['prenom'] = prenom_correct
                lawyer['nom_complet'] = f"{prenom_correct} {nom_correct}"
            
            enhanced.append(lawyer)
            
        return enhanced
    
    def clean_and_deduplicate(self, raw_lawyers):
        """Nettoie et déduplique toutes les données"""
        print(f"🧹 Nettoyage de {len(raw_lawyers)} entrées...")
        
        cleaned = []
        
        for lawyer in raw_lawyers:
            # Nettoyer les noms
            nom_clean = self.clean_name(lawyer.get('nom', ''))
            prenom_clean = self.clean_name(lawyer.get('prenom', ''))
            
            # Créer entrée nettoyée
            clean_lawyer = {
                'nom': nom_clean,
                'prenom': prenom_clean,
                'nom_complet': f"{prenom_clean} {nom_clean}".strip(),
                'email': lawyer.get('email', '').strip().lower(),
                'telephone': lawyer.get('telephone', '').strip(),
                'ville': lawyer.get('ville', '').strip().title(),
                'annee_inscription': lawyer.get('annee_inscription', '').strip(),
            }
            
            # Vérifier validité
            if self.is_valid_lawyer_entry(clean_lawyer):
                cleaned.append(clean_lawyer)
            else:
                self.invalid_removed += 1
                
        print(f"✅ {len(cleaned)} entrées valides après nettoyage")
        print(f"🗑️  {self.invalid_removed} entrées invalides supprimées")
        
        # Dédupliquer par email
        print("🔄 Déduplication par email...")
        deduplicated = self.deduplicate_by_email(cleaned)
        
        print(f"✅ {len(deduplicated)} avocats uniques")
        print(f"🗑️  {self.duplicates_removed} doublons supprimés")
        
        # Enrichir avec noms connus
        print("📝 Enrichissement avec noms connus...")
        enhanced = self.enhance_with_common_names(deduplicated)
        
        return enhanced
    
    def save_final_results(self, lawyers):
        """Sauvegarde les résultats finaux nettoyés"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n💾 Sauvegarde des {len(lawyers)} avocats finaux...")
        
        # CSV final
        csv_filename = f"bonneville_FINAL_NETTOYE_{len(lawyers)}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['nom', 'prenom', 'nom_complet', 'email', 'telephone', 'ville', 'annee_inscription']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for lawyer in lawyers:
                writer.writerow(lawyer)
        
        # JSON final
        json_filename = f"bonneville_FINAL_NETTOYE_{len(lawyers)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(lawyers, jsonfile, ensure_ascii=False, indent=2)
        
        # Emails finaux
        emails_filename = f"bonneville_EMAILS_FINAL_{len(lawyers)}_avocats_{timestamp}.txt"
        unique_emails = sorted([l['email'] for l in lawyers if l['email']])
        with open(emails_filename, 'w', encoding='utf-8') as emailfile:
            for email in unique_emails:
                emailfile.write(f"{email}\n")
        
        # Rapport final
        report_filename = f"bonneville_RAPPORT_FINAL_NETTOYE_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as reportfile:
            reportfile.write("🏛️  BARREAU DE BONNEVILLE - EXTRACTION FINALE NETTOYÉE\n")
            reportfile.write("=" * 65 + "\n\n")
            
            reportfile.write(f"📅 Date : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
            reportfile.write(f"🎯 Objectif : Liste complète et nettoyée des avocats\n\n")
            
            total = len(lawyers)
            emails = len([l for l in lawyers if l['email']])
            phones = len([l for l in lawyers if l['telephone']])
            cities = len([l for l in lawyers if l['ville']])
            years = len([l for l in lawyers if l['annee_inscription']])
            
            reportfile.write("📊 STATISTIQUES FINALES :\n")
            reportfile.write(f"   Total avocats : {total}\n")
            reportfile.write(f"   Avec email : {emails} ({emails/total*100:.1f}%)\n")
            reportfile.write(f"   Avec téléphone : {phones} ({phones/total*100:.1f}%)\n")
            reportfile.write(f"   Avec ville : {cities} ({cities/total*100:.1f}%)\n")
            reportfile.write(f"   Avec année : {years} ({years/total*100:.1f}%)\n\n")
            
            reportfile.write("🧹 NETTOYAGE EFFECTUÉ :\n")
            reportfile.write(f"   Entrées invalides supprimées : {self.invalid_removed}\n")
            reportfile.write(f"   Doublons supprimés : {self.duplicates_removed}\n")
            reportfile.write(f"   Noms corrigés et normalisés\n\n")
            
            reportfile.write("👥 LISTE FINALE DES AVOCATS :\n")
            reportfile.write("-" * 50 + "\n")
            
            for i, lawyer in enumerate(lawyers, 1):
                reportfile.write(f"{i:2d}. {lawyer['nom_complet']}\n")
                reportfile.write(f"    📧 {lawyer['email']}\n")
                if lawyer['telephone']:
                    reportfile.write(f"    📞 {lawyer['telephone']}\n")
                if lawyer['ville']:
                    reportfile.write(f"    📍 {lawyer['ville']}\n")
                if lawyer['annee_inscription']:
                    reportfile.write(f"    📅 {lawyer['annee_inscription']}\n")
                reportfile.write("\n")
        
        print(f"✅ Sauvegarde terminée !")
        print(f"\n📁 FICHIERS FINAUX GÉNÉRÉS :")
        print(f"   • {csv_filename}")
        print(f"   • {json_filename}")
        print(f"   • {emails_filename}")
        print(f"   • {report_filename}")
        
        return {
            'total': len(lawyers),
            'files': [csv_filename, json_filename, emails_filename, report_filename]
        }

def main():
    print("🧹 NETTOYAGE ET DÉDUPLICATION - BARREAU DE BONNEVILLE")
    print("=" * 60)
    
    cleaner = BonnevilleCleaner()
    
    # Charger les données brutes
    raw_data = cleaner.load_raw_data('bonneville_EXHAUSTIF_166_avocats_20260210_100139.json')
    
    # Nettoyer et dédupliquer
    clean_data = cleaner.clean_and_deduplicate(raw_data)
    
    # Sauvegarder
    results = cleaner.save_final_results(clean_data)
    
    print(f"\n🎉 NETTOYAGE TERMINÉ !")
    print(f"📊 {results['total']} avocats finaux dans la liste nettoyée")
    print(f"🎯 Liste prête pour utilisation !")

if __name__ == "__main__":
    main()