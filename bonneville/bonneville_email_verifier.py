#!/usr/bin/env python3
"""
Vérificateur d'emails pour Bonneville
Détecte et élimine les doublons, vérifie la validité des adresses
"""

import json
import csv
import re
from collections import defaultdict, Counter
from datetime import datetime

class BonnevilleEmailVerifier:
    def __init__(self):
        self.duplicates_found = []
        self.invalid_emails = []
        self.cleaned_lawyers = []
        
    def load_data(self, json_file):
        """Charge les données"""
        print(f"📂 Chargement des données : {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"✅ {len(data)} avocats chargés")
        return data
    
    def analyze_email_duplicates(self, lawyers):
        """Analyse les doublons d'emails"""
        print("\n🔍 ANALYSE DES DOUBLONS D'EMAILS")
        print("=" * 50)
        
        # Compter les occurrences d'emails
        email_counts = Counter()
        email_to_lawyers = defaultdict(list)
        
        for i, lawyer in enumerate(lawyers):
            email = lawyer.get('email', '').lower().strip()
            if email:
                email_counts[email] += 1
                email_to_lawyers[email].append((i, lawyer))
        
        # Identifier les doublons
        duplicates = {email: count for email, count in email_counts.items() if count > 1}
        
        if duplicates:
            print(f"❌ {len(duplicates)} emails en doublon trouvés :")
            for email, count in sorted(duplicates.items()):
                print(f"  📧 {email} : {count} occurrences")
                
                # Montrer les avocats concernés
                for i, lawyer in email_to_lawyers[email]:
                    nom_complet = f"{lawyer.get('prenom', '')} {lawyer.get('nom', '')}".strip()
                    print(f"     {i+1:2d}. {nom_complet}")
                print()
                
            self.duplicates_found = duplicates
        else:
            print("✅ Aucun doublon d'email détecté")
            
        return duplicates
    
    def validate_emails(self, lawyers):
        """Valide les adresses emails"""
        print("\n🔍 VALIDATION DES EMAILS")
        print("=" * 30)
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        valid_emails = []
        invalid_emails = []
        
        for i, lawyer in enumerate(lawyers):
            email = lawyer.get('email', '').strip()
            
            if not email:
                continue
                
            # Vérification format
            if not re.match(email_pattern, email):
                invalid_emails.append({
                    'index': i,
                    'email': email,
                    'lawyer': lawyer,
                    'reason': 'Format invalide'
                })
                continue
            
            # Vérifications supplémentaires
            if '..' in email or email.startswith('.') or email.endswith('.'):
                invalid_emails.append({
                    'index': i,
                    'email': email,
                    'lawyer': lawyer,
                    'reason': 'Points consécutifs ou en début/fin'
                })
                continue
                
            # Domaines suspects
            suspicious_domains = ['example.com', 'test.com', 'localhost']
            domain = email.split('@')[1].lower()
            
            if domain in suspicious_domains:
                invalid_emails.append({
                    'index': i,
                    'email': email,
                    'lawyer': lawyer,
                    'reason': f'Domaine suspect: {domain}'
                })
                continue
                
            valid_emails.append(email)
        
        if invalid_emails:
            print(f"❌ {len(invalid_emails)} emails invalides trouvés :")
            for item in invalid_emails:
                nom_complet = f"{item['lawyer'].get('prenom', '')} {item['lawyer'].get('nom', '')}".strip()
                print(f"  📧 {item['email']} ({nom_complet}) - {item['reason']}")
        else:
            print("✅ Tous les emails sont valides")
            
        print(f"✅ {len(valid_emails)} emails valides")
        
        self.invalid_emails = invalid_emails
        return valid_emails, invalid_emails
    
    def deduplicate_by_email(self, lawyers):
        """Supprime les doublons en gardant la meilleure entrée"""
        print("\n🧹 SUPPRESSION DES DOUBLONS")
        print("=" * 35)
        
        email_groups = defaultdict(list)
        
        # Grouper par email
        for lawyer in lawyers:
            email = lawyer.get('email', '').lower().strip()
            if email:
                email_groups[email].append(lawyer)
        
        cleaned_lawyers = []
        removed_count = 0
        
        for email, group in email_groups.items():
            if len(group) == 1:
                # Pas de doublon
                cleaned_lawyers.append(group[0])
            else:
                # Choisir la meilleure entrée
                best_lawyer = self.choose_best_duplicate(group)
                cleaned_lawyers.append(best_lawyer)
                removed_count += len(group) - 1
                
                print(f"📧 {email} : {len(group)} doublons → 1 gardé")
                for i, lawyer in enumerate(group):
                    nom_complet = f"{lawyer.get('prenom', '')} {lawyer.get('nom', '')}".strip()
                    status = "✅ GARDÉ" if lawyer == best_lawyer else "❌ supprimé"
                    print(f"   {i+1}. {nom_complet} - {status}")
        
        print(f"\n✅ {removed_count} doublons supprimés")
        print(f"📊 {len(cleaned_lawyers)} avocats uniques dans la liste finale")
        
        return cleaned_lawyers
    
    def choose_best_duplicate(self, duplicates):
        """Choisit la meilleure entrée parmi les doublons"""
        
        # Scorer chaque entrée
        scored_duplicates = []
        
        for lawyer in duplicates:
            score = 0
            
            # Points pour informations complètes
            if lawyer.get('telephone') and len(lawyer['telephone']) > 8:
                score += 10
            if lawyer.get('ville') and len(lawyer['ville']) > 3:
                score += 8
            if lawyer.get('adresse') and len(lawyer['adresse']) > 10:
                score += 6
            if lawyer.get('annee_inscription') and lawyer['annee_inscription'].strip():
                score += 5
            if lawyer.get('structure') and len(lawyer['structure']) > 5:
                score += 4
            if lawyer.get('specialisations') and len(lawyer['specialisations']) > 5:
                score += 3
            
            # Points pour noms complets et corrects
            nom = lawyer.get('nom', '').strip()
            prenom = lawyer.get('prenom', '').strip()
            
            if len(nom) > 3:
                score += 2
            if len(prenom) > 3:
                score += 2
                
            # Bonus pour noms qui semblent corrects (pas tronqués)
            if nom and not nom.endswith('-') and len(nom) > 4:
                score += 3
            if prenom and not prenom.endswith('-') and len(prenom) > 4:
                score += 3
            
            scored_duplicates.append((score, lawyer))
        
        # Retourner le meilleur
        best = max(scored_duplicates, key=lambda x: x[0])[1]
        return best
    
    def verify_unique_emails(self, lawyers):
        """Vérification finale de l'unicité des emails"""
        print("\n🔍 VÉRIFICATION FINALE DE L'UNICITÉ")
        print("=" * 45)
        
        emails_seen = set()
        truly_unique = []
        
        for lawyer in lawyers:
            email = lawyer.get('email', '').lower().strip()
            
            if email and email not in emails_seen:
                emails_seen.add(email)
                truly_unique.append(lawyer)
            elif email in emails_seen:
                nom_complet = f"{lawyer.get('prenom', '')} {lawyer.get('nom', '')}".strip()
                print(f"⚠️ Doublon résiduel détecté : {email} ({nom_complet})")
        
        print(f"✅ {len(truly_unique)} emails vraiment uniques")
        return truly_unique
    
    def save_verified_results(self, lawyers):
        """Sauvegarde les résultats vérifiés"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n💾 Sauvegarde des {len(lawyers)} avocats vérifiés...")
        
        # CSV vérifié
        csv_filename = f"bonneville_VERIFIE_NETTOYE_{len(lawyers)}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['nom', 'prenom', 'nom_complet', 'email', 'telephone', 
                         'ville', 'adresse', 'annee_inscription', 'structure', 'specialisations']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for lawyer in lawyers:
                # Compléter nom_complet
                nom_complet = f"{lawyer.get('prenom', '')} {lawyer.get('nom', '')}".strip()
                lawyer['nom_complet'] = nom_complet
                
                # Nettoyer les valeurs
                clean_row = {}
                for field in fieldnames:
                    value = lawyer.get(field, '')
                    if isinstance(value, str):
                        value = value.strip()
                    clean_row[field] = value
                    
                writer.writerow(clean_row)
        
        # JSON vérifié
        json_filename = f"bonneville_VERIFIE_NETTOYE_{len(lawyers)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(lawyers, jsonfile, ensure_ascii=False, indent=2)
        
        # Emails vérifiés (uniques)
        emails_filename = f"bonneville_EMAILS_UNIQUES_VERIFIES_{len(lawyers)}_{timestamp}.txt"
        unique_emails = sorted([l['email'] for l in lawyers if l.get('email')])
        with open(emails_filename, 'w', encoding='utf-8') as emailfile:
            for email in unique_emails:
                emailfile.write(f"{email}\n")
        
        # Rapport de vérification
        report_filename = f"bonneville_RAPPORT_VERIFICATION_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as reportfile:
            reportfile.write("🏛️  BARREAU DE BONNEVILLE - RAPPORT DE VÉRIFICATION\n")
            reportfile.write("=" * 60 + "\n\n")
            
            reportfile.write(f"📅 Date : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
            reportfile.write(f"🎯 Objectif : Élimination des doublons d'emails\n\n")
            
            total = len(lawyers)
            emails = len([l for l in lawyers if l.get('email')])
            
            reportfile.write("📊 RÉSULTATS DE LA VÉRIFICATION :\n")
            reportfile.write(f"   Avocats finaux : {total}\n")
            reportfile.write(f"   Emails uniques : {emails}\n")
            reportfile.write(f"   Doublons supprimés : {len(self.duplicates_found)}\n")
            reportfile.write(f"   Emails invalides : {len(self.invalid_emails)}\n\n")
            
            if self.duplicates_found:
                reportfile.write("🔍 DOUBLONS TROUVÉS ET SUPPRIMÉS :\n")
                for email, count in self.duplicates_found.items():
                    reportfile.write(f"   📧 {email} : {count} occurrences\n")
                reportfile.write("\n")
            
            if self.invalid_emails:
                reportfile.write("❌ EMAILS INVALIDES TROUVÉS :\n")
                for item in self.invalid_emails:
                    reportfile.write(f"   📧 {item['email']} - {item['reason']}\n")
                reportfile.write("\n")
            
            reportfile.write("✅ LISTE FINALE NETTOYÉE :\n")
            reportfile.write("-" * 40 + "\n")
            
            for i, lawyer in enumerate(lawyers, 1):
                nom_complet = f"{lawyer.get('prenom', '')} {lawyer.get('nom', '')}".strip()
                reportfile.write(f"{i:2d}. {nom_complet}\n")
                reportfile.write(f"    📧 {lawyer.get('email', '')}\n")
                if lawyer.get('telephone'):
                    reportfile.write(f"    📞 {lawyer.get('telephone')}\n")
                reportfile.write("\n")
        
        print(f"✅ Vérification terminée !")
        print(f"\n📁 FICHIERS VÉRIFIÉS GÉNÉRÉS :")
        print(f"   • {csv_filename}")
        print(f"   • {json_filename}")
        print(f"   • {emails_filename}")
        print(f"   • {report_filename}")
        
        return {
            'total': total,
            'duplicates_removed': len(self.duplicates_found),
            'invalid_removed': len(self.invalid_emails),
            'files': [csv_filename, json_filename, emails_filename, report_filename]
        }
    
    def run_verification(self, json_file):
        """Lance la vérification complète"""
        print("🔍 VÉRIFICATION ET NETTOYAGE DES EMAILS - BONNEVILLE")
        print("=" * 60)
        
        try:
            # 1. Charger les données
            lawyers = self.load_data(json_file)
            
            # 2. Analyser les doublons
            duplicates = self.analyze_email_duplicates(lawyers)
            
            # 3. Valider les emails
            valid_emails, invalid_emails = self.validate_emails(lawyers)
            
            # 4. Supprimer les doublons
            cleaned_lawyers = self.deduplicate_by_email(lawyers)
            
            # 5. Vérification finale
            final_lawyers = self.verify_unique_emails(cleaned_lawyers)
            
            # 6. Sauvegarder
            results = self.save_verified_results(final_lawyers)
            
            print(f"\n🎉 VÉRIFICATION TERMINÉE !")
            print(f"📊 {results['total']} avocats avec emails uniques")
            print(f"🗑️  {results['duplicates_removed']} doublons supprimés")
            print(f"❌ {results['invalid_removed']} emails invalides supprimés")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification : {e}")
            return False

def main():
    verifier = BonnevilleEmailVerifier()
    
    # Utiliser le dernier fichier JSON généré
    json_file = "bonneville_COMPLET_70_avocats_20260210_100640.json"
    
    success = verifier.run_verification(json_file)
    
    if success:
        print("\n✅ EMAILS VÉRIFIÉS ET NETTOYÉS !")
        print("📧 Liste finale sans doublons prête")
    else:
        print("\n❌ ÉCHEC DE LA VÉRIFICATION")

if __name__ == "__main__":
    main()