#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper PARFAIT pour le Barreau de Saint-Quentin
Version finale corrigée - récupère TOUS les détails avec navigation correcte
"""

import time
import csv
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re

def parse_lawyer_name_perfect(full_name_text):
    """Parse parfait des noms d'avocats"""
    text = full_name_text.replace("Maître", "").replace("Me", "").strip()
    
    # Format "MarcANTONINI"
    match = re.search(r'^([A-Z][a-z]+(?:-[A-Z][a-z]+)*)([A-Z]+(?:-[A-Z]+)*)$', text)
    if match:
        return match.group(1), match.group(2)
    
    # Format "Jean-MarieWENZINGER" 
    match2 = re.search(r'^([A-Z][a-z]+(?:-[A-Z][a-z]+)+)([A-Z]+)$', text)
    if match2:
        return match2.group(1), match2.group(2)
    
    # Format classique
    parts = text.split()
    if len(parts) >= 2:
        for i, part in enumerate(parts):
            if part.isupper() and len(part) > 1:
                return " ".join(parts[:i]), " ".join(parts[i:])
        if parts[-1].isupper():
            return " ".join(parts[:-1]), parts[-1]
    
    # Tout collé
    if len(text.split()) == 1 and len(text) > 3:
        for i in range(2, len(text)-1):
            if text[i].isupper() and text[i-1].islower():
                return text[:i], text[i:]
    
    return text, ""

def clean_specialities_perfect(text):
    """Nettoie et organise les spécialités juridiques - VERSION ULTRA PARFAITE"""
    specialites = []
    
    # Textes à ignorer complètement
    ignored_texts = [
        'Conformément à la loi n°78-17',
        'RGPD',
        'Règlement Général sur la Protection',
        'droit d\'accès, de rectification',
        'Voir le détail',
        'Contact',
        'Spécialités :',
        'assistance et la représentation devant la justice',
        'Annuaire des avocats',
        'spécialités et les domaines de compétences'
    ]
    
    # Patterns précis pour les vraies spécialités juridiques
    specialty_patterns = [
        r'(Droit (?:fiscal|pénal|civil|commercial|social|du travail|de la famille|immobilier|public|douanier|des affaires|de la propriété|bancaire|maritime|de l\'environnement|médical|de la consommation)(?:\s+et\s+(?:droit\s+)?(?:fiscal|pénal|civil|commercial|social|du travail|de la famille|immobilier|public|douanier|des affaires|de la propriété|bancaire|maritime|de l\'environnement|médical|de la consommation))?)',
        r'(Droit de (?:la sécurité sociale|la protection sociale|l\'urbanisme|l\'informatique|la construction))',
        r'((?:Droit|Procédure)s?\s+(?:pénale?s?|civile?s?|commerciale?s?|administrative?s?))',
        r'(Contentieux\s+(?:administratif|civil|commercial|pénal))',
        r'(Divorce|Succession|Bail|Copropriété|Construction|Urbanisme)',
        r'(Propriété intellectuelle|Propriété industrielle)',
        r'(Accidents de la route|Accidents du travail)',
        r'(Responsabilité civile|Responsabilité médicale)',
        r'(Contrats?|Recouvrement)',
        r'(Fiscalité|Douane|Social)',
        r'(Pénal|Civil|Commercial|Administratif)'
    ]
    
    # Chercher dans tout le texte avec les patterns
    for pattern in specialty_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            
            clean_match = match.strip()
            
            # Ignorer si contient du texte générique
            if any(ignored in clean_match for ignored in ignored_texts):
                continue
                
            # Garder seulement les vraies spécialités
            if (len(clean_match) > 3 and len(clean_match) < 100 and 
                clean_match not in specialites and
                not clean_match.isdigit()):
                specialites.append(clean_match)
    
    # Si aucune spécialité trouvée, essayer une approche plus basique
    if not specialites:
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            
            # Ignorer les textes génériques
            if any(ignored in line for ignored in ignored_texts):
                continue
                
            # Chercher des lignes courtes avec des mots-clés juridiques
            if (5 < len(line) < 80 and
                any(keyword in line.lower() for keyword in ['droit', 'pénal', 'civil', 'fiscal', 'social', 'commercial']) and
                not line.startswith('Conformément') and
                'loi n°78-17' not in line):
                
                if line not in specialites:
                    specialites.append(line)
    
    # Nettoyer et limiter
    clean_specialites = []
    for spec in specialites[:5]:  # Max 5 spécialités
        # Nettoyer chaque spécialité
        clean_spec = re.sub(r'^\W+', '', spec)
        clean_spec = re.sub(r'\s+', ' ', clean_spec) 
        clean_spec = clean_spec.strip()
        
        if clean_spec and clean_spec not in clean_specialites:
            clean_specialites.append(clean_spec)
    
    # Retourner un dictionnaire avec les spécialités séparées
    return {
        'specialites': clean_specialites[0] if len(clean_specialites) > 0 else '',
        'competences': clean_specialites[1] if len(clean_specialites) > 1 else '',
        'activites_dominantes': clean_specialites[2] if len(clean_specialites) > 2 else ''
    }

def extract_contact_from_page_perfect(session, lawyer_url):
    """Extraction parfaite depuis la page individuelle - URL corrigée"""
    contact_info = {
        'telephone': '',
        'fax': '',
        'email': '',
        'adresse_complete': '',
        'specialites': '',
        'competences': '',
        'activites_dominantes': '',
        'structure': ''
    }
    
    try:
        print(f"   📄 Navigation: {lawyer_url}")
        response = session.get(lawyer_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()
        
        # Téléphone - extraction améliorée
        phone_patterns = [
            r'(?:Tél|Téléphone|Tel)\s*[:\-]?\s*(0[1-9](?:[.\s-]?\d{2}){4})',
            r'\b(0[1-9](?:[.\s-]?\d{2}){4})\b',
            r'(?:\+33|0033)\s?[1-9](?:[.\s-]?\d{2}){4}'
        ]
        
        for pattern in phone_patterns:
            phone_matches = re.findall(pattern, page_text)
            if phone_matches:
                # Prendre le premier téléphone trouvé
                phone = phone_matches[0]
                if isinstance(phone, tuple):
                    phone = phone[0]
                contact_info['telephone'] = phone.strip()
                print(f"   📞 {contact_info['telephone']}")
                break
        
        # Fax - extraction améliorée
        fax_patterns = [
            r'(?:Fax|Télécopie)\s*[:\-]?\s*(0[1-9](?:[.\s-]?\d{2}){4})',
            r'Fax\s*:?\s*(0[1-9](?:[.\s-]?\d{2}){4})'
        ]
        
        for pattern in fax_patterns:
            fax_matches = re.findall(pattern, page_text)
            if fax_matches:
                contact_info['fax'] = fax_matches[0].strip()
                print(f"   📠 {contact_info['fax']}")
                break
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, page_text)
        if email_matches:
            contact_info['email'] = email_matches[0]
            print(f"   📧 {contact_info['email']}")
        
        # Adresse complète - extraction améliorée
        address_patterns = [
            r'(\d+[^0-9\n]*(?:JF KENNEDY|Kennedy|rue|avenue|place|boulevard)[^\n\r]{5,100})',
            r'([^0-9\n]*(?:02100|Saint-Quentin)[^\n\r]{0,50})',
            r'(\d+[^0-9\n]*[A-Z\s]{10,80})'
        ]
        
        found_addresses = []
        for pattern in address_patterns:
            addr_matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in addr_matches:
                clean_addr = match.strip()
                if len(clean_addr) > 8 and clean_addr not in found_addresses and not clean_addr.isdigit():
                    found_addresses.append(clean_addr)
        
        if found_addresses:
            contact_info['adresse_complete'] = ' - '.join(found_addresses[:2])
            print(f"   📍 {contact_info['adresse_complete']}")
        
        # Spécialités - VERSION PARFAITE
        specialities_dict = clean_specialities_perfect(page_text)
        contact_info['specialites'] = specialities_dict['specialites']
        contact_info['competences'] = specialities_dict['competences'] 
        contact_info['activites_dominantes'] = specialities_dict['activites_dominantes']
        
        if contact_info['specialites']:
            print(f"   ⚖️  {contact_info['specialites'][:50]}...")
        
        # Structure/Cabinet
        structure_patterns = [
            r'(SCP [A-ZÀ-ÿ\s-]+)',
            r'(SELARL [A-ZÀ-ÿ\s-]+)',
            r'([A-ZÀ-ÿ]+ ET [A-ZÀ-ÿ\s]+)',
            r'(ANTONINI ET ASSOCIES)'
        ]
        
        for pattern in structure_patterns:
            struct_matches = re.findall(pattern, page_text, re.IGNORECASE)
            if struct_matches:
                contact_info['structure'] = struct_matches[0].strip()
                print(f"   🏢 {contact_info['structure']}")
                break
        
        print(f"   ✅ Page traitée avec succès")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    return contact_info

def scrape_saint_quentin_parfait():
    """Scraper PARFAIT - version finale corrigée"""
    
    print("🚀 SCRAPER SAINT-QUENTIN PARFAIT")
    print("=" * 70)
    print("🎯 Version finale avec URLs corrigées")
    print("📞 Extraction complète des téléphones, fax, adresses")
    print()
    
    lawyers_data = []
    
    # Session requests
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    try:
        # Page principale
        url = "https://www.avocats-saint-quentin.com/trouver-un-avocat/annuaire-des-avocats.htm"
        base_url = "https://www.avocats-saint-quentin.com"
        
        print(f"🌐 Page principale: {url}")
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        print("✅ Page chargée")
        
        # Trouver tous les avocats
        h4_elements = soup.find_all('h4')
        lawyer_h4s = [h4 for h4 in h4_elements if "Maître" in h4.get_text()]
        
        print(f"📊 {len(lawyer_h4s)} avocats détectés")
        print()
        
        # Traiter chaque avocat
        for i, h4 in enumerate(lawyer_h4s, 1):
            full_name = h4.get_text(strip=True)
            prenom, nom = parse_lawyer_name_perfect(full_name)
            
            print(f"👤 {i:2d}/{len(lawyer_h4s)} - {prenom} {nom}")
            
            # Informations de base
            parent = h4.parent if h4.parent else h4
            context_text = parent.get_text()
            
            # Année d'inscription
            year_pattern = r'\b(19[7-9]\d|20[0-3]\d)\b'
            year_match = re.search(year_pattern, context_text)
            annee_inscription = year_match.group(1) if year_match else ''
            
            # Chercher le lien vers la page individuelle - VERSION CORRIGÉE
            individual_page_url = None
            links = parent.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                if 'annuaire/maitre-' in href.lower() and href.endswith('.htm'):
                    # CORRECTION : Construction correcte de l'URL
                    if href.startswith('/'):
                        individual_page_url = base_url + href
                    elif href.startswith('http'):
                        individual_page_url = href
                    else:
                        # Le href est relatif, le construire correctement
                        individual_page_url = base_url + '/trouver-un-avocat/annuaire-des-avocats/' + href
                    break
            
            # Initialiser les données
            lawyer_data = {
                'prenom': prenom,
                'nom': nom,
                'nom_complet': full_name.replace("Maître", "").strip(),
                'annee_inscription': annee_inscription,
                'specialites': '',
                'competences': '',
                'activites_dominantes': '',
                'structure': '',
                'adresse': 'Saint-Quentin, 02100',
                'telephone': '',
                'fax': '',
                'email': '',
                'source_url': url
            }
            
            # Extraire depuis la page principale d'abord
            main_specialities_dict = clean_specialities_perfect(context_text)
            if main_specialities_dict['specialites']:
                lawyer_data['specialites'] = main_specialities_dict['specialites']
                lawyer_data['competences'] = main_specialities_dict['competences']
                lawyer_data['activites_dominantes'] = main_specialities_dict['activites_dominantes']
            
            # Si lien vers page individuelle, l'explorer
            if individual_page_url:
                contact_details = extract_contact_from_page_perfect(session, individual_page_url)
                
                # Mettre à jour avec les détails trouvés
                if contact_details['telephone']:
                    lawyer_data['telephone'] = contact_details['telephone']
                if contact_details['fax']:
                    lawyer_data['fax'] = contact_details['fax']
                if contact_details['email']:
                    lawyer_data['email'] = contact_details['email']
                if contact_details['adresse_complete']:
                    lawyer_data['adresse'] = contact_details['adresse_complete']
                if contact_details['specialites'] and not lawyer_data['specialites']:
                    lawyer_data['specialites'] = contact_details['specialites']
                if contact_details.get('competences') and not lawyer_data['competences']:
                    lawyer_data['competences'] = contact_details['competences']
                if contact_details.get('activites_dominantes') and not lawyer_data['activites_dominantes']:
                    lawyer_data['activites_dominantes'] = contact_details['activites_dominantes']
                if contact_details['structure']:
                    lawyer_data['structure'] = contact_details['structure']
                
                lawyer_data['source_url'] = individual_page_url
            else:
                print(f"   ⚠️  Pas de lien trouvé")
            
            lawyers_data.append(lawyer_data)
            print(f"   ✅ Ajouté")
            
            # Pause
            time.sleep(0.5)
            print()
    
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    
    return lawyers_data

def save_perfect_results(lawyers_data, test_name="PARFAIT"):
    """Sauvegarde parfaite des résultats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Nettoyer les doublons
    unique_lawyers = []
    seen_names = set()
    
    for lawyer in lawyers_data:
        if not lawyer.get('prenom') or not lawyer.get('nom'):
            continue
            
        name_key = f"{lawyer['prenom'].strip().lower()}_{lawyer['nom'].strip().lower()}"
        
        if name_key not in seen_names and len(lawyer['nom']) > 1:
            seen_names.add(name_key)
            unique_lawyers.append(lawyer)
    
    # Statistiques détaillées
    phones_found = len([l for l in unique_lawyers if l.get('telephone')])
    fax_found = len([l for l in unique_lawyers if l.get('fax')])
    emails_found = len([l for l in unique_lawyers if l.get('email')])
    specialities_found = len([l for l in unique_lawyers if l.get('specialites')])
    structures_found = len([l for l in unique_lawyers if l.get('structure')])
    addresses_found = len([l for l in unique_lawyers if l.get('adresse') and l['adresse'] != 'Saint-Quentin, 02100'])
    
    print(f"\n📊 RÉSULTATS PARFAITS:")
    print(f"- Avocats uniques: {len(unique_lawyers)}")
    print(f"- Téléphones: {phones_found} ({phones_found/len(unique_lawyers)*100:.1f}%)")
    print(f"- Fax: {fax_found} ({fax_found/len(unique_lawyers)*100:.1f}%)")
    print(f"- Emails: {emails_found} ({emails_found/len(unique_lawyers)*100:.1f}%)")
    print(f"- Spécialités: {specialities_found} ({specialities_found/len(unique_lawyers)*100:.1f}%)")
    print(f"- Structures: {structures_found} ({structures_found/len(unique_lawyers)*100:.1f}%)")
    print(f"- Adresses détaillées: {addresses_found} ({addresses_found/len(unique_lawyers)*100:.1f}%)")
    
    if not unique_lawyers:
        print("❌ Aucun avocat valide")
        return
    
    # CSV avec colonnes bien organisées
    csv_filename = f"SAINT_QUENTIN_{test_name}_{len(unique_lawyers)}_avocats_{timestamp}.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'prenom', 'nom', 'nom_complet', 'annee_inscription',
            'specialites', 'competences', 'activites_dominantes', 'structure',
            'adresse', 'telephone', 'fax', 'email', 'source_url'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for lawyer in unique_lawyers:
            # Créer une ligne propre avec toutes les colonnes
            clean_row = {}
            for field in fieldnames:
                clean_row[field] = lawyer.get(field, '')
            writer.writerow(clean_row)
    
    # JSON
    json_filename = f"SAINT_QUENTIN_{test_name}_{len(unique_lawyers)}_avocats_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(unique_lawyers, jsonfile, ensure_ascii=False, indent=2)
    
    # Fichier des téléphones et fax
    contacts_filename = f"SAINT_QUENTIN_CONTACTS_{test_name}_{timestamp}.txt"
    with open(contacts_filename, 'w', encoding='utf-8') as contactsfile:
        contactsfile.write(f"CONTACTS - BARREAU DE SAINT-QUENTIN\n")
        contactsfile.write(f"{'='*60}\n")
        contactsfile.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        contactsfile.write(f"Total avocats: {len(unique_lawyers)}\n")
        contactsfile.write(f"Téléphones: {phones_found}\n")
        contactsfile.write(f"Fax: {fax_found}\n")
        contactsfile.write(f"Emails: {emails_found}\n\n")
        
        for lawyer in unique_lawyers:
            if lawyer.get('telephone') or lawyer.get('fax') or lawyer.get('email'):
                contactsfile.write(f"{lawyer['prenom']} {lawyer['nom']}\n")
                if lawyer.get('telephone'):
                    contactsfile.write(f"  📞 Tél: {lawyer['telephone']}\n")
                if lawyer.get('fax'):
                    contactsfile.write(f"  📠 Fax: {lawyer['fax']}\n")
                if lawyer.get('email'):
                    contactsfile.write(f"  📧 Email: {lawyer['email']}\n")
                contactsfile.write("\n")
    
    # Emails uniquement
    emails_filename = f"SAINT_QUENTIN_EMAILS_{test_name}_{timestamp}.txt"
    unique_emails = set()
    for lawyer in unique_lawyers:
        email = lawyer.get('email', '').strip()
        if email and '@' in email:
            unique_emails.add(email)
    
    with open(emails_filename, 'w', encoding='utf-8') as emailsfile:
        emailsfile.write(f"EMAILS - BARREAU DE SAINT-QUENTIN\n")
        emailsfile.write(f"{'='*50}\n")
        emailsfile.write(f"Total: {len(unique_emails)} emails\n\n")
        for email in sorted(unique_emails):
            emailsfile.write(f"{email}\n")
    
    # Rapport final parfait
    report_filename = f"SAINT_QUENTIN_RAPPORT_{test_name}_{timestamp}.txt"
    with open(report_filename, 'w', encoding='utf-8') as reportfile:
        reportfile.write(f"RAPPORT PARFAIT - BARREAU DE SAINT-QUENTIN\n")
        reportfile.write(f"{'='*70}\n\n")
        reportfile.write(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        reportfile.write(f"🔧 Version: Scraper PARFAIT - URLs corrigées\n")
        reportfile.write(f"🎯 Objectif: Extraction complète de tous les détails\n\n")
        
        reportfile.write(f"📊 PERFORMANCE PARFAITE:\n")
        reportfile.write(f"{'─'*50}\n")
        reportfile.write(f"• Avocats traités: {len(unique_lawyers)}\n")
        reportfile.write(f"• Téléphones: {phones_found} ({phones_found/len(unique_lawyers)*100:.1f}%)\n")
        reportfile.write(f"• Fax: {fax_found} ({fax_found/len(unique_lawyers)*100:.1f}%)\n")
        reportfile.write(f"• Emails: {emails_found} ({emails_found/len(unique_lawyers)*100:.1f}%)\n")
        reportfile.write(f"• Spécialités: {specialities_found} ({specialities_found/len(unique_lawyers)*100:.1f}%)\n")
        reportfile.write(f"• Structures: {structures_found} ({structures_found/len(unique_lawyers)*100:.1f}%)\n")
        reportfile.write(f"• Adresses détaillées: {addresses_found} ({addresses_found/len(unique_lawyers)*100:.1f}%)\n\n")
        
        # Analyse par décennie
        years = [int(l.get('annee_inscription', 0)) for l in unique_lawyers if l.get('annee_inscription')]
        if years:
            reportfile.write(f"📈 ANALYSE TEMPORELLE:\n")
            reportfile.write(f"{'─'*30}\n")
            reportfile.write(f"• 1980-1989: {len([y for y in years if 1980 <= y < 1990])} avocats\n")
            reportfile.write(f"• 1990-1999: {len([y for y in years if 1990 <= y < 2000])} avocats\n")
            reportfile.write(f"• 2000-2009: {len([y for y in years if 2000 <= y < 2010])} avocats\n")
            reportfile.write(f"• 2010-2019: {len([y for y in years if 2010 <= y < 2020])} avocats\n")
            reportfile.write(f"• 2020+: {len([y for y in years if y >= 2020])} avocats\n\n")
        
        reportfile.write(f"📋 LISTE COMPLÈTE:\n")
        reportfile.write(f"{'═'*70}\n\n")
        
        for i, lawyer in enumerate(unique_lawyers, 1):
            reportfile.write(f"{i:2d}. {lawyer.get('prenom', '')} {lawyer.get('nom', '')}\n")
            if lawyer.get('annee_inscription'):
                reportfile.write(f"     📅 Serment: {lawyer['annee_inscription']}\n")
            if lawyer.get('telephone'):
                reportfile.write(f"     📞 Tél: {lawyer['telephone']}\n")
            if lawyer.get('fax'):
                reportfile.write(f"     📠 Fax: {lawyer['fax']}\n")
            if lawyer.get('email'):
                reportfile.write(f"     📧 Email: {lawyer['email']}\n")
            if lawyer.get('adresse') and lawyer['adresse'] != 'Saint-Quentin, 02100':
                reportfile.write(f"     📍 {lawyer['adresse']}\n")
            if lawyer.get('structure'):
                reportfile.write(f"     🏢 {lawyer['structure']}\n")
            if lawyer.get('specialites'):
                reportfile.write(f"     ⚖️  {lawyer['specialites']}\n")
            reportfile.write(f"     🔗 {lawyer.get('source_url', '')}\n")
            reportfile.write("\n")
    
    print(f"\n📁 FICHIERS PARFAITS CRÉÉS:")
    print(f"📄 CSV: {csv_filename}")
    print(f"📋 JSON: {json_filename}")
    print(f"📞 Contacts: {contacts_filename}")
    print(f"📧 Emails: {emails_filename}")
    print(f"📝 Rapport: {report_filename}")
    
    return csv_filename, json_filename, contacts_filename, emails_filename, report_filename

if __name__ == "__main__":
    start_time = time.time()
    
    lawyers = scrape_saint_quentin_parfait()
    
    if lawyers:
        files = save_perfect_results(lawyers)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n🎉 SCRAPING PARFAIT TERMINÉ!")
        print(f"⏱️  Durée: {duration:.1f}s")
        print(f"⚡ Vitesse: {len(lawyers)/duration:.1f} avocats/s")
        
        # Aperçu des meilleurs résultats
        lawyers_with_contacts = [l for l in lawyers if l.get('telephone') or l.get('fax') or l.get('email')]
        lawyers_with_specialties = [l for l in lawyers if l.get('specialites')]
        
        if lawyers_with_contacts:
            print(f"\n📞 AVOCATS AVEC CONTACTS ({len(lawyers_with_contacts)}):")
            for lawyer in lawyers_with_contacts[:5]:
                print(f"• {lawyer['prenom']} {lawyer['nom']}")
                if lawyer.get('telephone'):
                    print(f"  📞 {lawyer['telephone']}")
                if lawyer.get('fax'):
                    print(f"  📠 {lawyer['fax']}")
                if lawyer.get('email'):
                    print(f"  📧 {lawyer['email']}")
        
        if lawyers_with_specialties:
            print(f"\n⚖️  SPÉCIALITÉS ({len(lawyers_with_specialties)}):")
            for lawyer in lawyers_with_specialties[:3]:
                print(f"• {lawyer['prenom']} {lawyer['nom']}: {lawyer['specialites'][:60]}...")
        
    else:
        print("❌ Échec du scraping")
    
    print("\n🔚 Terminé")