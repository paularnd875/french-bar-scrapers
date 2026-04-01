#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POITIERS BAR ASSOCIATION - FINAL SCRAPER
Version finale optimisée pour extraction complète des avocats
Source: https://www.avocats-poitiers.com/espaceprive/annuaire/

Auteur: Paul Arnould
Date: Mars 2026
Repository: https://github.com/paularnd875/french-bar-scrapers
"""

import requests
import json
import csv
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup

class PoitiersBarreScraper:
    def __init__(self):
        self.base_url = "https://www.avocats-poitiers.com"
        self.ajax_url = f"{self.base_url}/espaceprive/wp-admin/admin-ajax.php"
        
        # Configuration AJAX validée
        self.nonce = "52b4077f34"
        self.form_hash = "6328a" 
        self.post_id = "11"
        
        self.avocats = []
        self.doublons_detectes = set()
        self.session = None
        
        # Statistiques découvertes
        self.total_expected = 293
        self.total_pages = 20
        
    def setup_session(self):
        """Configuration de la session HTTP"""
        print("🔧 Configuration de la session...")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f"{self.base_url}/espaceprive/annuaire/"
        })
        
        print("✅ Session configurée")
    
    def get_page_data(self, page=1):
        """Récupération des données d'une page via AJAX"""
        print(f"📄 Récupération page {page}...")
        
        data = {
            'action': 'um_get_members',
            'nonce': self.nonce,
            'form_id': self.form_hash,
            'directory_id': self.form_hash,
            'page': page,
            'search': '',
            'view_type': 'grid',
            'sorting': 'last_first_name',
            'searched': '1',
            'must_search': '0',
            'post_id': self.post_id
        }
        
        try:
            response = self.session.post(self.ajax_url, data=data, timeout=15)
            
            if response.status_code == 200:
                json_data = response.json()
                
                if json_data.get('success'):
                    page_data = json_data.get('data', {})
                    users = page_data.get('users', [])
                    pagination = page_data.get('pagination', {})
                    
                    print(f"   ✅ {len(users)} avocats trouvés")
                    
                    return users, pagination
                else:
                    error = json_data.get('data', 'Erreur inconnue')
                    print(f"   ❌ Erreur API: {error}")
                    return [], {}
            else:
                print(f"   ❌ Erreur HTTP {response.status_code}")
                return [], {}
                
        except Exception as e:
            print(f"   ❌ Erreur requête: {e}")
            return [], {}
    
    def separer_nom_prenom_intelligent(self, nom_complet):
        """Séparation intelligente nom/prénom pour gérer les noms composés"""
        if not nom_complet:
            return "", ""
        
        nom_complet = nom_complet.strip()
        parts = nom_complet.split()
        
        if len(parts) <= 1:
            return nom_complet, ""
        
        # Cas spéciaux connus avec patterns exacts
        special_patterns = [
            # Particules nobiliaires et préfixes
            (r'^(AL MIAH)\s+(.+)$', 1),               # AL MIAH Emmanuel
            (r'^(DA ROCHA)\s+(.+)$', 1),              # DA ROCHA Laura  
            (r'^(DE BEAUMONT)\s+(.+)$', 1),           # DE BEAUMONT Brice
            (r'^(DE CAMBOURG)\s+(.+)$', 1),           # DE CAMBOURG Anne
            (r'^(DE LA ROCCA)\s+(.+)$', 1),           # DE LA ROCCA Aurélia
            (r'^(LE BORGNE)\s+(.+)$', 1),             # LE BORGNE Kristelle
            (r'^(LE BOURNAULT)\s+(.+)$', 1),          # LE BOURNAULT Hélène
            (r'^(LE BRETON)\s+(.+)$', 1),             # LE BRETON Mathilde
            (r'^(LE FORT)\s+(.+)$', 1),               # LE FORT Baptiste
            (r'^(LE LAIN)\s+(.+)$', 1),               # LE LAIN Marion
            (r'^(LE ROUX)\s+(.+)$', 1),               # LE ROUX Estelle
            
            # Noms avec tirets
            (r'^([A-Z-]+)\s+(.+)$', 1),               # CARTIER-LIMOGES Jézabel
            
            # Noms composés avec BETOULLE BENABEN Marion -> BETOULLE et BENABEN Marion
            (r'^(BETOULLE)\s+(BENABEN)\s+(.+)$', 2),  # Cas spécial BETOULLE BENABEN Marion
        ]
        
        # Test des patterns spéciaux
        for pattern, nom_groups in special_patterns:
            match = re.match(pattern, nom_complet, re.IGNORECASE)
            if match:
                if nom_groups == 1:
                    return match.group(1), match.group(2)
                elif nom_groups == 2:
                    return f"{match.group(1)} {match.group(2)}", match.group(3)
        
        # Logique générale améliorée
        # Stratégie : identifier le point de rupture nom/prénom
        
        # 1. Chercher des prénoms évidents (première lettre maj + reste min)
        prenom_start = -1
        for i, part in enumerate(parts):
            # Prénom typique : Emmanuel, Marie-Claire, Jean-René
            if len(part) > 1 and part[0].isupper() and (
                part[1:].islower() or  # Emmanuel
                ('-' in part and all(p[0].isupper() and p[1:].islower() for p in part.split('-') if p))  # Jean-René
            ):
                prenom_start = i
                break
        
        if prenom_start > 0:
            nom = ' '.join(parts[:prenom_start])
            prenom = ' '.join(parts[prenom_start:])
            return nom, prenom
        
        # 2. Si tous les mots sont en MAJUSCULES sauf le dernier
        if len(parts) >= 2 and parts[-1][0].isupper() and (
            len(parts[-1]) == 1 or parts[-1][1:].islower()
        ):
            nom = ' '.join(parts[:-1])
            prenom = parts[-1]
            return nom, prenom
        
        # 3. Fallback : dernier mot = prénom
        nom = ' '.join(parts[:-1])
        prenom = parts[-1]
        return nom, prenom
    
    def extract_lawyer_info(self, user_data):
        """Extraction des informations d'un avocat depuis les données JSON"""
        try:
            # Nom complet - Parsing intelligent
            display_name = user_data.get('display_name', '')
            nom, prenom = self.separer_nom_prenom_intelligent(display_name)
            
            # Email - extraction depuis le HTML
            email = ""
            email_html = user_data.get('adressemail_contact', '')
            if email_html:
                soup = BeautifulSoup(email_html, 'html.parser')
                email_link = soup.find('a', href=lambda x: x and x.startswith('mailto:'))
                if email_link:
                    email = email_link.get('href', '').replace('mailto:', '').strip()
            
            # Téléphone - extraction depuis le HTML
            telephone = ""
            phone_html = user_data.get('phone_number', '')
            if phone_html:
                soup = BeautifulSoup(phone_html, 'html.parser')
                phone_link = soup.find('a', href=lambda x: x and x.startswith('tel:'))
                if phone_link:
                    telephone = phone_link.get('href', '').replace('tel:', '').strip()
            
            # Année de serment - regex corrigée
            annee_serment = ""
            serment_text = user_data.get('prestation_serment', '')
            if serment_text:
                annee_match = re.search(r'\b(19|20)\d{2}\b', serment_text)
                if annee_match:
                    annee_serment = annee_match.group()
            
            # Autres informations
            barreau = user_data.get('Barreau_select', '')
            adresse = user_data.get('ville', '')
            specialisation = user_data.get('Domaine_spe', '')
            cabinet = user_data.get('cabinet', '')
            profile_url = user_data.get('profile_url', '')
            user_id = user_data.get('id', '')
            
            # Vérification doublon
            if self.est_doublon(prenom, nom, email):
                print(f"     ⚠️  Doublon détecté: {prenom} {nom}")
                return None
            
            avocat = {
                'nom': nom,
                'prenom': prenom,
                'email': email,
                'telephone': telephone,
                'annee_serment': annee_serment,
                'barreau': barreau,
                'adresse': adresse,
                'specialisation': specialisation,
                'cabinet': cabinet,
                'lien_profil': profile_url,
                'user_id': str(user_id),
                'source': 'JSON_AJAX'
            }
            
            return avocat
            
        except Exception as e:
            print(f"     ❌ Erreur extraction: {e}")
            return None
    
    def est_doublon(self, prenom, nom, email):
        """Détection des doublons"""
        identifiants = [
            f"{nom.upper()}_{prenom.upper()}",
            email.lower() if email else "",
            f"{prenom.upper()}_{nom.upper()}"
        ]
        
        for ident in identifiants:
            if ident and ident in self.doublons_detectes:
                return True
        
        # Ajouter les identifiants
        for ident in identifiants:
            if ident:
                self.doublons_detectes.add(ident)
        
        return False
    
    def scrape_all_lawyers(self):
        """Scraping complet de tous les avocats"""
        print("🚀 DÉBUT DU SCRAPING POITIERS")
        print(f"🎯 Objectif: {self.total_expected} avocats")
        print("=" * 60)
        
        # Test de la première page
        users, pagination = self.get_page_data(1)
        
        if not users:
            print("❌ Impossible de récupérer la première page")
            return False
        
        # Mise à jour des statistiques 
        if pagination:
            self.total_pages = pagination.get('total_pages', self.total_pages)
            self.total_expected = pagination.get('total_users', self.total_expected)
        
        print(f"✅ Détection: {self.total_expected} avocats sur {self.total_pages} pages\n")
        
        # Scraping de toutes les pages
        for page in range(1, self.total_pages + 1):
            if page > 1:
                print(f"\n📄 Page {page}/{self.total_pages}...")
                users, pagination = self.get_page_data(page)
                
                if not users:
                    print(f"   ⚠️  Page {page} vide")
                    continue
            
            page_count = 0
            for i, user in enumerate(users, 1):
                avocat = self.extract_lawyer_info(user)
                if avocat:
                    self.avocats.append(avocat)
                    page_count += 1
                    print(f"     ✅ {i:2d}. {avocat['nom']} {avocat['prenom']} - {avocat['email']} ({avocat['annee_serment']})")
            
            print(f"   📊 Page {page}: +{page_count} avocats (Total: {len(self.avocats)})")
            time.sleep(1)
        
        print(f"\n🎉 SCRAPING TERMINÉ!")
        print(f"📊 Total: {len(self.avocats)}/{self.total_expected} avocats ({len(self.avocats)/self.total_expected*100:.1f}%)")
        
        return True
    
    def sauvegarder_donnees(self):
        """Sauvegarde des données extraites"""
        if not self.avocats:
            print("❌ Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV
        csv_filename = f"POITIERS_FINAL_{len(self.avocats)}_avocats_{timestamp}.csv"
        fieldnames = ['nom', 'prenom', 'email', 'telephone', 'annee_serment', 'barreau', 
                     'adresse', 'specialisation', 'cabinet', 'lien_profil', 'user_id', 'source']
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.avocats)
        
        # JSON
        json_filename = f"POITIERS_FINAL_{len(self.avocats)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.avocats, f, indent=2, ensure_ascii=False)
        
        # Emails uniquement
        emails_valides = [a['email'] for a in self.avocats if a['email']]
        emails_uniques = sorted(set(emails_valides))
        emails_filename = f"POITIERS_FINAL_EMAILS_{len(emails_uniques)}_uniques_{timestamp}.txt"
        
        with open(emails_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(emails_uniques))
        
        # Statistiques finales
        emails_count = len(emails_uniques)
        phones_count = len([a for a in self.avocats if a['telephone']])
        annees_count = len([a for a in self.avocats if a['annee_serment']])
        
        print("\n" + "=" * 70)
        print("🎉 EXTRACTION POITIERS TERMINÉE!")
        print("=" * 70)
        print(f"🎯 OBJECTIF: {self.total_expected} avocats")
        print(f"✅ EXTRAITS: {len(self.avocats)} avocats ({len(self.avocats)/self.total_expected*100:.1f}%)")
        print(f"📧 EMAILS: {emails_count} valides")
        print(f"📞 TÉLÉPHONES: {phones_count} valides")
        print(f"📅 ANNÉES: {annees_count} valides ({annees_count/len(self.avocats)*100:.1f}%)")
        print(f"📄 FICHIERS:")
        print(f"   - {csv_filename}")
        print(f"   - {json_filename}")
        print(f"   - {emails_filename}")
        print("=" * 70)
    
    def run(self):
        """Exécution complète du scraper"""
        print("=" * 70)
        print("🏛️  BARREAU DE POITIERS - SCRAPER FINAL")
        print("=" * 70)
        
        try:
            self.setup_session()
            success = self.scrape_all_lawyers()
            
            if success:
                self.sauvegarder_donnees()
            else:
                print("❌ Échec du scraping")
                
        except Exception as e:
            print(f"❌ Erreur critique: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Point d'entrée principal"""
    scraper = PoitiersBarreScraper()
    scraper.run()

if __name__ == "__main__":
    main()