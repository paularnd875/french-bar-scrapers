#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPER PDF BARREAU GUADELOUPE
==============================
Extrait les informations des avocats depuis un PDF du barreau de Guadeloupe

Structure détectée:
- Chaque avocat sur 3-4 lignes
- Ligne 1: NOM Prénom Adresse Code_postal Ville Date_serment
- Ligne 2: email Tel: téléphone [Fax: fax]
- Ligne 3: Numéro de case (optionnel)

Usage: python3 scraper_barreau_guadeloupe.py [fichier.pdf]
Sortie: avocats_guadeloupe_[timestamp].csv
"""

import pdfplumber
import re
import csv
import sys
import os
from datetime import datetime
from collections import defaultdict

class ScraperBarreauGuadeloupe:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.avocats = []
        
    def log(self, message):
        """Log avec timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def nettoyer_texte(self, text):
        """Nettoie et normalise le texte"""
        if not text:
            return ""
        return re.sub(r'\\s+', ' ', text.strip())
    
    def extraire_email(self, text):
        """Extrait l'email d'un texte"""
        emails = re.findall(r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b', text)
        return emails[0] if emails else ""
    
    def extraire_telephone(self, text):
        """Extrait le numéro de téléphone principal"""
        # Pattern pour téléphones Guadeloupe (0590/0690/0691...)
        phones = re.findall(r'Tel\\s*:\\s*(0[56]90\\d{6})', text)
        if not phones:
            # Pattern plus large
            phones = re.findall(r'Tel\\s*:\\s*(0\\d{9})', text)
        return phones[0] if phones else ""
    
    def extraire_fax(self, text):
        """Extrait le numéro de fax"""
        fax = re.findall(r'Fax\\s*:\\s*(0\\d{9})', text)
        return fax[0] if fax else ""
    
    def extraire_date_serment(self, text):
        """Extrait la date de prestation de serment"""
        # Pattern DD/MM/YYYY
        dates = re.findall(r'(\\d{2}/\\d{2}/\\d{4})', text)
        return dates[-1] if dates else ""  # Prendre la dernière date trouvée
    
    def extraire_code_postal_ville(self, text):
        """Extrait le code postal et la ville"""
        # Pattern code postal Guadeloupe/Saint-Martin/Saint-Barthélemy
        match = re.search(r'(97\\d{3})\\s+([A-Z\\s-]+?)(?=\\s+\\d{2}/\\d{2}/\\d{4}|$)', text)
        if match:
            code_postal = match.group(1)
            ville = self.nettoyer_texte(match.group(2))
            return code_postal, ville
        return "", ""
    
    def extraire_adresse(self, text, code_postal=""):
        """Extrait l'adresse avant le code postal"""
        if code_postal:
            # Tout ce qui est entre le nom et le code postal
            pattern = rf'^([^0-9]+?)\\s+{re.escape(code_postal)}'
            match = re.search(pattern, text)
            if match:
                adresse_brute = match.group(1).strip()
                # Enlever les parties qui ressemblent à un nom (majuscules)
                adresse_parts = adresse_brute.split()
                adresse = []
                for i, part in enumerate(adresse_parts):
                    # Garder les parties qui ne sont pas entièrement en majuscules 
                    # ou qui contiennent des chiffres
                    if not part.isupper() or re.search(r'\\d', part) or i >= 2:
                        adresse.append(part)
                return ' '.join(adresse).strip()
        return ""
    
    def extraire_nom_prenom(self, text):
        """Extrait nom et prénom depuis la première ligne"""
        # Le nom/prénom est au début de la ligne, avant l'adresse
        parts = text.split()
        if len(parts) >= 2:
            # Généralement NOM Prénom au début
            nom = parts[0].strip()
            prenom = parts[1].strip()
            return nom, prenom
        return "", ""
    
    def parser_bloc_avocat(self, lignes):
        """Parse un bloc de 2-4 lignes représentant un avocat"""
        if not lignes or len(lignes) < 2:
            return None
        
        ligne1 = lignes[0]  # Nom Prénom Adresse Code_postal Ville Date_serment
        ligne2 = lignes[1]  # email Tel: téléphone [Fax: fax]
        
        # Extraction des données
        nom, prenom = self.extraire_nom_prenom(ligne1)
        email = self.extraire_email(ligne2)
        telephone = self.extraire_telephone(ligne2)
        fax = self.extraire_fax(ligne2)
        date_serment = self.extraire_date_serment(ligne1)
        code_postal, ville = self.extraire_code_postal_ville(ligne1)
        adresse = self.extraire_adresse(ligne1, code_postal)
        
        # Numéro de case (ligne 3 si présente)
        numero_case = ""
        if len(lignes) >= 3 and re.search(r'\\d+/\\d+|B\\d+/P\\d+|---', lignes[2]):
            numero_case = lignes[2].strip()
        
        avocat = {
            'nom': nom,
            'prenom': prenom,
            'adresse': adresse,
            'code_postal': code_postal,
            'ville': ville,
            'telephone': telephone,
            'fax': fax,
            'email': email,
            'date_serment': date_serment,
            'numero_case': numero_case
        }
        
        # Validation: un avocat valide doit avoir au moins nom ET (email OU téléphone)
        if nom and (email or telephone):
            return avocat
        
        return None
    
    def extraire_avocats_page(self, page_text):
        """Extrait les avocats d'une page"""
        lignes = page_text.split('\\n')
        avocats_page = []
        
        # Filtrer les lignes de header/footer
        lignes_utiles = []
        for ligne in lignes:
            ligne_clean = ligne.strip()
            if (ligne_clean and 
                not ligne_clean.startswith('Page ') and
                not ligne_clean.startswith('Nom Prénom') and
                not ligne_clean.startswith('prestation') and
                not ligne_clean.startswith('serment')):
                lignes_utiles.append(ligne_clean)
        
        i = 0
        while i < len(lignes_utiles):
            # Essayer de regrouper 2-4 lignes pour former un avocat
            for nb_lignes in [4, 3, 2]:  # Essayer 4, 3, puis 2 lignes
                if i + nb_lignes <= len(lignes_utiles):
                    bloc = lignes_utiles[i:i + nb_lignes]
                    avocat = self.parser_bloc_avocat(bloc)
                    if avocat:
                        avocats_page.append(avocat)
                        i += nb_lignes
                        break
            else:
                # Aucune combinaison ne marche, passer à la ligne suivante
                i += 1
        
        return avocats_page
    
    def extraire_tous_avocats(self):
        """Extrait tous les avocats du PDF"""
        self.log(f"Début extraction du fichier: {self.pdf_path}")
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self.log(f"PDF ouvert: {len(pdf.pages)} pages")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    self.log(f"Traitement page {page_num}/{len(pdf.pages)}")
                    
                    text = page.extract_text()
                    if text:
                        avocats_page = self.extraire_avocats_page(text)
                        self.avocats.extend(avocats_page)
                        self.log(f"  Page {page_num}: {len(avocats_page)} avocats trouvés")
                
                self.log(f"Extraction terminée: {len(self.avocats)} avocats au total")
                return self.avocats
                
        except Exception as e:
            self.log(f"Erreur lors de l'extraction: {e}")
            return []
    
    def sauvegarder_csv(self, filename="avocats_guadeloupe.csv"):
        """Sauvegarde les avocats en CSV"""
        if not self.avocats:
            self.log("Aucune donnée à sauvegarder")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_final = filename.replace('.csv', f'_{timestamp}.csv')
        
        self.log(f"Sauvegarde: {filename_final}")
        
        fieldnames = [
            'nom', 'prenom', 'adresse', 'code_postal', 'ville',
            'telephone', 'fax', 'email', 'date_serment', 'numero_case'
        ]
        
        with open(filename_final, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for avocat in self.avocats:
                writer.writerow(avocat)
        
        self.log(f"✅ {len(self.avocats)} avocats sauvegardés")
        return filename_final
    
    def afficher_statistiques(self):
        """Affiche des statistiques sur les données extraites"""
        if not self.avocats:
            return
        
        total = len(self.avocats)
        emails_trouves = sum(1 for a in self.avocats if a['email'])
        telephones_trouves = sum(1 for a in self.avocats if a['telephone'])
        dates_trouvees = sum(1 for a in self.avocats if a['date_serment'])
        
        self.log("")
        self.log("=" * 60)
        self.log("STATISTIQUES D'EXTRACTION")
        self.log("=" * 60)
        self.log(f"Total avocats: {total}")
        self.log(f"Emails trouvés: {emails_trouves}/{total} ({(emails_trouves/total*100):.1f}%)")
        self.log(f"Téléphones trouvés: {telephones_trouves}/{total} ({(telephones_trouves/total*100):.1f}%)")
        self.log(f"Dates serment trouvées: {dates_trouvees}/{total} ({(dates_trouvees/total*100):.1f}%)")
        
        # Échantillon de données
        self.log("")
        self.log("Échantillon de 3 premiers avocats:")
        for i, avocat in enumerate(self.avocats[:3], 1):
            self.log(f"  {i}. {avocat['nom']} {avocat['prenom']}")
            self.log(f"     📧 {avocat['email']}")
            self.log(f"     📞 {avocat['telephone']}")
            self.log(f"     📅 {avocat['date_serment']}")

def main():
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "barreau_guadeloupe.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        print(f"Usage: python3 {sys.argv[0]} [fichier.pdf]")
        return
    
    print("")
    print("=" * 60)
    print("🔍 SCRAPER PDF BARREAU GUADELOUPE")
    print("=" * 60)
    
    scraper = ScraperBarreauGuadeloupe(pdf_path)
    
    try:
        # Extraction
        avocats = scraper.extraire_tous_avocats()
        
        if avocats:
            # Statistiques
            scraper.afficher_statistiques()
            
            # Sauvegarde
            fichier = scraper.sauvegarder_csv()
            
            print("")
            print("🎉 EXTRACTION TERMINÉE!")
            print(f"📊 {len(avocats)} avocats extraits")
            print(f"📄 Fichier: {fichier}")
        else:
            print("❌ Aucune donnée extraite")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()