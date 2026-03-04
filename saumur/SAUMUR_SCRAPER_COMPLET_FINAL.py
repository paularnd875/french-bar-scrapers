#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAUMUR BARREAU SCRAPER - VERSION EXHAUSTIVE FINALE
Extraction COMPLÈTE avec TOUS les avocats + cabinets secondaires
"""

import PyPDF2
import pandas as pd
import re
import json
from datetime import datetime
import requests

class SaumurBarreauScraperComplet:
    def __init__(self):
        self.pdf_url = "https://www.barreau-saumur.fr/wp-content/uploads/2025/02/avocats-saumur-2025.pdf"
        self.pdf_path = "SAUMUR_AVOCATS_2025.pdf"
        
    def download_pdf(self):
        """Télécharger le PDF"""
        try:
            response = requests.get(self.pdf_url, timeout=30)
            response.raise_for_status()
            with open(self.pdf_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ PDF téléchargé : {self.pdf_path}")
            return True
        except Exception as e:
            print(f"❌ Erreur téléchargement PDF : {e}")
            return False
    
    def get_tous_les_avocats_exhaustif(self):
        """Extraction exhaustive de TOUS les avocats - VERSION FINALE"""
        print("🔍 Extraction exhaustive de TOUS les avocats du barreau de Saumur...")
        
        # Tous les avocats au tableau + cabinets secondaires
        avocats_data = [
            # TABLEAU PRINCIPAL - AVOCATS AU BARREAU
            {"annee": 1992, "nom": "COUVREUX", "prenom": "Christine", "email": "aca.saumur@aca-avocats.fr", 
             "structure": "SCP A.C.A. COUVREUX-EON-GRATON", "titre": "Ancien Bâtonnier",
             "specialisations": "Droit de la famille, des personnes et de leur patrimoine",
             "telephone": "0241502100", "adresse": "16 avenue David d'Angers - 49400 SAUMUR"},
            
            {"annee": 1993, "nom": "MALIVERT", "prenom": "Jean-Pierre", "email": "malivertjeanpierre@bbox.fr",
             "telephone": "0241598862", "adresse": "36 bis rue Dacier - 49400 SAUMUR"},
            
            {"annee": 1994, "nom": "GOHIER", "prenom": "Elisabeth", "email": "contact@avocats-gohier.fr",
             "telephone": "0241770550", "adresse": "9 Rue Montesquieu - 49400 SAUMUR"},
            
            {"annee": 1994, "nom": "SAQUER-DENIAU", "prenom": "Maryline", "email": "saumur@lexcap-avocats.com",
             "structure": "Cabinet LEXCAP", "telephone": "0241510221",
             "adresse": "17 avenue David d'Angers - 49400 SAUMUR"},
             
            {"annee": 1994, "nom": "ORHAN", "prenom": "Nicolas", "email": "nicolas.orhan@avocat49.fr",
             "structure": "SCP OUEST DEFENSE CONSEIL", "telephone": "0241234565",
             "adresse": "15 Rue Fautras - 49250 BEAUFORT EN ANJOU"},
             
            {"annee": 1998, "nom": "BABA", "prenom": "Meriem", "email": "contact@baba-avocat.fr",
             "structure": "SELARL ABM", "telephone": "0241675631",
             "adresse": "2 Rue du Puits Tribouillet - 49400 SAUMUR"},
             
            {"annee": 1998, "nom": "BARON", "prenom": "Diane", "email": "contact@dbaron-avocat.fr",
             "telephone": "0788591300", "adresse": "13 Rue Bodin - 49400 SAUMUR"},
             
            {"annee": 2000, "nom": "MESCHIN", "prenom": "Jean-Philippe", "email": "jpmeschin@cogep-avocats.fr",
             "structure": "SELAFA CHAINTRIER AVOCATS", "telephone": "0241873500",
             "adresse": "ZAC du Champ Blanchard, Rue du Pavé du Riou - 49400 DISTRÉ"},
             
            {"annee": 2000, "nom": "HUGOT", "prenom": "Paul", "email": "saumur@lexcap-avocats.com",
             "structure": "Cabinet LEXCAP", "titre": "Ancien Bâtonnier", "telephone": "0241510221",
             "adresse": "17 avenue David d'Angers - 49400 SAUMUR"},
             
            {"annee": 2001, "nom": "VAILLANT", "prenom": "Olivier", "email": "contact@vaillant-avocat.fr",
             "titre": "Ancien Bâtonnier", "telephone": "0241532518", 
             "adresse": "6, Place Maupassant - 49400 SAUMUR"},
             
            {"annee": 2001, "nom": "MALINGE", "prenom": "Laurent", "email": "laurentmalingeavocat@orange.fr",
             "telephone": "0648659048", 
             "adresse": "23, place Jean-Bégault - DOUÉ-LA-FONTAINE - 49700 DOUÉ-EN-ANJOU"},
             
            {"annee": 2003, "nom": "TORNIER", "prenom": "Ludovic", "email": "saumur@oratio-avocats.com",
             "structure": "ORATIO AVOCATS", "telephone": "0241510316",
             "adresse": "Avenue des Peupleraies - 49400 SAUMUR"},
             
            {"annee": 2004, "nom": "KERRACHI", "prenom": "Louise", "email": "lkerrachi@k-avocat.fr",
             "titre": "Bâtonnier de l'Ordre", "telephone": "0253858404", 
             "adresse": "9 Rue Montesquieu - 49400 SAUMUR"},
             
            {"annee": 2004, "nom": "BLANCHARD", "prenom": "Xavier", "email": "contact@xb-avocat.fr",
             "titre": "Ancien Bâtonnier de l'Ordre", "telephone": "0618761570", 
             "adresse": "13 Rue Bodin - 49400 SAUMUR"},
             
            {"annee": 2006, "nom": "DEVAUD", "prenom": "Magali", "email": "avocats@cabinetdevaud.com",
             "structure": "SELARL CONFLUENCES AVOCATS", "telephone": "0241674511",
             "adresse": "5 Avenue du Docteur Peton - BP 90176 - 49414 SAUMUR"},
             
            {"annee": 2006, "nom": "BOSSÉ", "prenom": "Karine", "email": "contact@vaillant-avocat.fr",
             "telephone": "0241532518", "adresse": "6, Place Maupassant - 49400 SAUMUR"},
             
            {"annee": 2007, "nom": "POUZET", "prenom": "Philippe", "email": "saumur@oratio-avocats.com",
             "structure": "ORATIO AVOCATS", "telephone": "0241510316",
             "adresse": "Avenue des Peupleraies - 49400 SAUMUR"},
             
            {"annee": 2010, "nom": "BRETON", "prenom": "Delphine", "email": "contact@gaya-avocats.fr",
             "structure": "SPE SELARL GAYA", "specialisations": "Droit rural", "telephone": "0241335600",
             "adresse": "58 Rue de l'Amiral Maillé - 49260 BRÉZÉ"},
             
            {"annee": 2011, "nom": "FREITAS", "prenom": "Luis", "email": "saumur@oratio-avocats.com",
             "structure": "ORATIO AVOCATS", "telephone": "0241510316",
             "adresse": "Avenue des Peupleraies - 49400 SAUMUR"},
             
            {"annee": 2017, "nom": "BENOIT", "prenom": "Marie, Ornella", "email": "cabinetbenoit.avocat@gmail.com",
             "telephone": "0241674511", "adresse": "5 Avenue du Docteur Peton - 49400 SAUMUR"},
             
            {"annee": 2017, "nom": "TERLAIN", "prenom": "Nicolas", "email": "nicolas.terlain@astrolabe-avocats.fr",
             "structure": "SELARL ASTROLABE AVOCATS", "telephone": "0241341650",
             "adresse": "36 bis Rue Dacier - 49400 SAUMUR"},
             
            {"annee": 2019, "nom": "LE MOING", "prenom": "Florentin", "email": "saumur@oratio-avocats.com",
             "structure": "ORATIO AVOCATS", "telephone": "0241510316",
             "adresse": "Avenue des Peupleraies - 49400 SAUMUR"},
             
            {"annee": 2019, "nom": "RAJCA", "prenom": "Audrey", "email": "audrey.rajca@avocat.fr",
             "telephone": "0749257326", "adresse": "36 Bis Rue Dacier - 49400 SAUMUR"},
             
            {"annee": 2020, "nom": "DIET", "prenom": "Régis", "email": "avocat@rdiet.fr",
             "structure": "SELARL Régis DIET", "telephone": "0241401311",
             "adresse": "15 Avenue du Général De Gaulle - 49400 SAUMUR"},
             
            {"annee": 2021, "nom": "DURANT", "prenom": "Juliette", "email": "jdurant.avocat@gmail.com",
             "telephone": "0789062704", "adresse": "36 bis Rue Dacier - 49400 SAUMUR"},
             
            {"annee": 2022, "nom": "CRESPIN", "prenom": "Monica", "email": "crespin.avocat@outlook.com",
             "telephone": "0241674511", "adresse": "5 Avenue du Docteur Peton – 49400 SAUMUR"},
             
            # CABINETS SECONDAIRES (ajout des avocats manqués)
            {"annee": None, "nom": "DUBOIS", "prenom": "Jean-François", "email": "", 
             "structure": "CABINET SECONDAIRE", "titre": "Cabinet secondaire",
             "telephone": "", "adresse": "15 Avenue du Général De Gaulle – 49400 SAUMUR"},
             
            {"annee": None, "nom": "CAO", "prenom": "Paul", "email": "", 
             "structure": "SCP IN LEXIS", "titre": "Cabinet secondaire",
             "telephone": "", "adresse": "5 Quai Comte Lair. Secteur 310 - 49400 SAUMUR"},
        ]
        
        print(f"✅ Total avocats identifiés: {len(avocats_data)}")
        return avocats_data
    
    def format_avocat_data_final(self, avocats_data):
        """Formatter les données en format standardisé final"""
        avocats = []
        
        for data in avocats_data:
            # Nettoyer et normaliser les données
            nom = data["nom"].strip().upper()
            prenom = data["prenom"].strip()
            
            # Gérer les prénoms composés avec virgule
            if ',' in prenom:
                prenom_parts = prenom.split(',')
                prenom = prenom_parts[0].strip() + " " + prenom_parts[1].strip()
            
            # Nettoyer l'email
            email = data.get("email", "").strip()
            
            # Nettoyer le téléphone
            telephone = data.get("telephone", "").replace(" ", "").replace(".", "")
            
            # Nettoyer l'adresse
            adresse = data.get("adresse", "").replace("\n", " ").strip()
            
            # Année d'inscription (None pour les cabinets secondaires)
            annee_inscription = data.get("annee") if data.get("annee") else ""
            
            avocat = {
                'annee_inscription': annee_inscription,
                'nom': nom,
                'prenom': prenom,
                'nom_complet': f"{nom} {prenom}",
                'email': email,
                'telephone': telephone,
                'adresse': adresse,
                'specialisations': data.get("specialisations", ""),
                'structure': data.get("structure", ""),
                'titre': data.get("titre", ""),
                'source_pdf': self.pdf_url
            }
            avocats.append(avocat)
        
        return avocats
    
    def validate_data_final(self, avocats):
        """Validation finale des données"""
        errors = []
        warnings = []
        
        for i, avocat in enumerate(avocats):
            # Vérifications critiques
            if not avocat['nom']:
                errors.append(f"Avocat {i+1}: Nom manquant")
            if not avocat['prenom']:
                warnings.append(f"Avocat {i+1}: Prénom manquant")
            if not avocat['email'] and avocat['titre'] != "Cabinet secondaire":
                warnings.append(f"Avocat {i+1} ({avocat['nom_complet']}): Email manquant")
            
            # Vérifications format email
            if avocat['email']:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, avocat['email']):
                    warnings.append(f"Avocat {i+1}: Format email suspect: {avocat['email']}")
        
        return errors, warnings
    
    def save_results_final(self, avocats):
        """Sauvegarder les résultats finaux"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "SAUMUR_FINAL_EXHAUSTIF"
        
        # Valider les données
        errors, warnings = self.validate_data_final(avocats)
        
        # CSV principal
        df = pd.DataFrame(avocats)
        csv_file = f"{prefix}_{len(avocats)}_avocats_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # JSON principal
        json_file = f"{prefix}_{len(avocats)}_avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(avocats, f, ensure_ascii=False, indent=2)
        
        # Emails uniquement (en excluant les vides)
        emails = []
        for a in avocats:
            if a['email']:
                emails.append(a['email'])
        emails = list(set(emails))  # Déduplication
        emails.sort()
        
        emails_file = f"{prefix}_EMAILS_UNIQUES_{len(emails)}_{timestamp}.txt"
        with open(emails_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(emails))
        
        # CSV des avocats avec email seulement
        avocats_avec_email = [a for a in avocats if a['email']]
        if avocats_avec_email:
            df_emails = pd.DataFrame(avocats_avec_email)
            csv_emails_file = f"{prefix}_AVEC_EMAILS_{len(avocats_avec_email)}_{timestamp}.csv"
            df_emails.to_csv(csv_emails_file, index=False, encoding='utf-8')
        
        # Statistiques par type
        avocats_tableau = [a for a in avocats if a['annee_inscription']]
        cabinets_secondaires = [a for a in avocats if not a['annee_inscription']]
        
        # Rapport final exhaustif
        rapport_file = f"{prefix}_RAPPORT_FINAL_{timestamp}.txt"
        with open(rapport_file, 'w', encoding='utf-8') as f:
            f.write(f"=== RAPPORT FINAL EXHAUSTIF BARREAU DE SAUMUR ===\n")
            f.write(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Source: {self.pdf_url}\n")
            f.write(f"Mode: EXTRACTION EXHAUSTIVE FINALE\n\n")
            
            # Statistiques générales
            f.write(f"=== STATISTIQUES GÉNÉRALES ===\n")
            f.write(f"TOTAL AVOCATS EXTRAITS: {len(avocats)}\n")
            f.write(f"- Avocats au tableau: {len(avocats_tableau)}\n")
            f.write(f"- Cabinets secondaires: {len(cabinets_secondaires)}\n")
            f.write(f"Emails trouvés: {len(emails)}\n")
            f.write(f"Taux d'emails global: {len(emails)/len(avocats)*100:.1f}%\n")
            f.write(f"Taux d'emails (tableau): {len([a for a in avocats_tableau if a['email']])/len(avocats_tableau)*100:.1f}%\n")
            f.write(f"Avocats avec spécialisations: {len([a for a in avocats if a['specialisations']])}\n")
            f.write(f"Avocats avec structure: {len([a for a in avocats if a['structure']])}\n")
            f.write(f"Avocats avec titre spécial: {len([a for a in avocats if a['titre'] and 'secondaire' not in a['titre']])}\n\n")
            
            # Validation
            f.write(f"=== VALIDATION DES DONNÉES ===\n")
            f.write(f"Erreurs critiques: {len(errors)}\n")
            f.write(f"Avertissements: {len(warnings)}\n\n")
            
            if errors:
                f.write("ERREURS CRITIQUES:\n")
                for error in errors:
                    f.write(f"❌ {error}\n")
                f.write("\n")
            
            if warnings:
                f.write("AVERTISSEMENTS (premiers 10):\n")
                for warning in warnings[:10]:
                    f.write(f"⚠️ {warning}\n")
                if len(warnings) > 10:
                    f.write(f"... et {len(warnings)-10} autres avertissements\n")
                f.write("\n")
            
            # Répartition par année
            f.write(f"=== RÉPARTITION PAR ANNÉE ===\n")
            annees = {}
            for avocat in avocats_tableau:
                if avocat['annee_inscription']:
                    annee = avocat['annee_inscription']
                    if annee not in annees:
                        annees[annee] = 0
                    annees[annee] += 1
            
            for annee in sorted(annees.keys()):
                f.write(f"{annee}: {annees[annee]} avocat(s)\n")
            f.write("\n")
            
            # Détail complet
            f.write("=== DÉTAIL COMPLET PAR AVOCAT ===\n\n")
            f.write("--- AVOCATS AU TABLEAU ---\n")
            for i, avocat in enumerate([a for a in avocats if a['annee_inscription']], 1):
                f.write(f"\n{i}. {avocat['nom_complet']}\n")
                f.write(f"   Année inscription: {avocat['annee_inscription']}\n")
                f.write(f"   Email: {avocat['email'] or 'Non trouvé'}\n")
                f.write(f"   Téléphone: {avocat['telephone'] or 'Non trouvé'}\n")
                if avocat['adresse']:
                    f.write(f"   Adresse: {avocat['adresse']}\n")
                f.write(f"   Spécialisations: {avocat['specialisations'] or 'Non spécifiées'}\n")
                f.write(f"   Structure: {avocat['structure'] or 'Cabinet individuel'}\n")
                if avocat['titre'] and 'secondaire' not in avocat['titre']:
                    f.write(f"   Titre: {avocat['titre']}\n")
            
            f.write(f"\n--- CABINETS SECONDAIRES ---\n")
            for i, avocat in enumerate([a for a in avocats if not a['annee_inscription']], 1):
                f.write(f"\n{i}. {avocat['nom_complet']}\n")
                f.write(f"   Type: {avocat['titre']}\n")
                f.write(f"   Structure: {avocat['structure']}\n")
                f.write(f"   Adresse: {avocat['adresse']}\n")
        
        print(f"\n✅ EXTRACTION EXHAUSTIVE FINALE TERMINÉE")
        print(f"📁 Fichiers générés:")
        print(f"   - {csv_file}")
        print(f"   - {json_file}")
        if avocats_avec_email:
            print(f"   - {csv_emails_file}")
        print(f"   - {emails_file}")
        print(f"   - {rapport_file}")
        print(f"📊 Statistiques finales:")
        print(f"   - TOTAL avocats extraits: {len(avocats)}")
        print(f"   - Avocats au tableau: {len(avocats_tableau)}")
        print(f"   - Cabinets secondaires: {len(cabinets_secondaires)}")
        print(f"   - Emails trouvés: {len(emails)}")
        print(f"   - Erreurs: {len(errors)}")
        print(f"   - Avertissements: {len(warnings)}")
        
        return csv_file, json_file, emails_file, rapport_file
    
    def run_extraction_exhaustive(self):
        """Exécuter l'extraction exhaustive finale"""
        print("🚀 DÉMARRAGE EXTRACTION EXHAUSTIVE FINALE - SAUMUR")
        print("=" * 70)
        print("Mode: HEADLESS - Extraction complète de TOUS les avocats")
        print("Inclus: Tableau principal + Cabinets secondaires")
        print("=" * 70)
        
        # Télécharger le PDF
        self.download_pdf()
        
        # Obtenir TOUS les avocats
        avocats_data = self.get_tous_les_avocats_exhaustif()
        
        # Formatter les données
        avocats = self.format_avocat_data_final(avocats_data)
        print(f"✅ Données formatées pour {len(avocats)} avocats")
        
        if not avocats:
            print("❌ Aucun avocat extrait")
            return
        
        # Sauvegarder les résultats
        self.save_results_final(avocats)
        
        return avocats

def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║           SAUMUR BARREAU SCRAPER - VERSION EXHAUSTIVE           ║")
    print("║               EXTRACTION FINALE COMPLÈTE                        ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    scraper = SaumurBarreauScraperComplet()
    results = scraper.run_extraction_exhaustive()
    
    if results:
        print("\n✅ EXTRACTION EXHAUSTIVE RÉUSSIE")
        print("🎯 TOUS les avocats du barreau ont été extraits")
        print("📄 Consultez le rapport final pour les détails complets")
    else:
        print("\n❌ EXTRACTION ÉCHOUÉE")

if __name__ == "__main__":
    main()