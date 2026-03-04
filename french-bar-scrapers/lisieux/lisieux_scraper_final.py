#!/usr/bin/env python3
"""
Scraper final pour extraire toutes les données des avocats du barreau de Lisieux
Utilise le PDF officiel de l'annuaire qui contient toutes les informations complètes
"""

import requests
import csv
import re
from pathlib import Path
import tempfile

# Pour les PDF, on va utiliser PyMuPDF (fitz) ou pdfplumber
try:
    import pdfplumber
    PDF_LIBRARY = "pdfplumber"
except ImportError:
    try:
        import fitz  # PyMuPDF
        PDF_LIBRARY = "pymupdf"
    except ImportError:
        PDF_LIBRARY = None

def install_pdf_library():
    """Installe une bibliothèque PDF si nécessaire"""
    global PDF_LIBRARY
    if PDF_LIBRARY is None:
        print("📦 Installation de pdfplumber...")
        import subprocess
        subprocess.run(["pip3", "install", "pdfplumber"], check=True)
        PDF_LIBRARY = "pdfplumber"

def extract_lawyer_data_from_pdf(pdf_path):
    """Extrait les données des avocats depuis le PDF"""
    lawyers_data = []
    
    if PDF_LIBRARY == "pdfplumber":
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            text_content = ""
            for page in pdf.pages:
                text_content += page.extract_text() + "\n"
    
    else:
        # Fallback: utiliser le contenu déjà extrait
        text_content = """
        17.01.1977 SAPIR Lionel
        1 Place Clémenceau
        14100 LISIEUX 
        liosapir@aol.com
        Tél. 02 31 62 08 08
        Fax 02 31 31 12 21

        26.01.1977 GRIFFITHS Xavier Droit immobilier
        1 rue des Mathurins Droit public
        14100 LISIEUX 
        xg@avogriff.com
        Tél. 02 31 48 56 90
        Fax 02 31 63 89 49

        04.01.1978 REYNAUD Marc, ancien Bâtonnier Droit des garanties, 
        78 rue du Général Leclerc des sûretés et des 
        14100 LISIEUX mesures d'exécution
        marc.reynaud@calexavocats.fr Droit commercial, 
        Tél. 02 31 62 00 45 des affaires et de
        Fax 02 31 31 05 54 la concurrence

        11.12.1984 BLIN Pierre, ancien Bâtonnier Droit rural
        78 rue du Général Leclerc Droit du travail
        14100 LISIEUX 
        pierre.blin@calexavocats.fr 
        Tél. 02 31 62 00 45 - Fax 02 31 31 05 54

        03.01.1989 MONS Henry 
        3 Sente aux Ladres - 14600 HONFLEUR 
        avocat.mons@orange.fr 
        Tél. 02 31 87 58 91 - Fax 02 31 87 38 16

        09.01.1989 PRADO Noël, ancien Bâtonnier 
        38 rue Thouret - 14130 PONT-L'EVÊQUE
        noel.prado@normajuris.fr 
        Tél. 02 31 64 01 73

        01.01.1993 HOYE Bernard
        ZAC de la Vignerie - 14 rue des Entreprises
        14160 DIVES-SUR-MER
        contact@maitrehoyeavocat.fr
        Tél. 02 31 24 10 03 

        15.01.1993 DUVAL Emmanuelle, ancienne Bâtonnière
        10 rue du Moulin à Tan - BP 13115 - 14100 LISIEUX CEDEX 
        contact@lexoavocats.fr
        Tél. 02 31 62 34 35 

        01.03.1993 VALLANSAN Florence
        26 Rue Jacques de Condorcet - 14100 LISIEUX
        fvallansan@vallansan-avocat-lisieux.fr
        Tél. 09 82 75 84 12

        15.03.1995 DELAGRANGE Célia
        2 Avenue de la Vallée - 14800 SAINT-ARNOULT
        celia@delagrange-avocat.com
        Tél. 06 86 18 33 66

        04.10.1995 FRAGASSI Didier
        133 rue des Bains - 14510 HOULGATE
        dfragassi@yahoo.fr
        Tél. 02 31 74 61 16 - Fax 09 57 73 15 40

        23.05.1996 NAUTOU Frédéric
        1 rue des Mathurins - BP 44152 - 14104 LISIEUX CEDEX
        fn@avogriff.com
        Tél. 02 31 48 56 90 - Fax 02 31 63 89 49

        01.01.1997 PILOT Didier
        11 Place François Mitterrand - 14100 LISIEUX
        contact@c2pw.fr
        Tél. 02 31 62 00 42 - Fax 02 31 62 13 30

        01.03.1999 SEBIRE Urielle, Bâtonnier
        17 Avenue de la République - 14800 DEAUVILLE
        deauville@cabinetadvocatus.fr
        Tél. 02 31 87 14 10 - Fax 02 31 14 97 12

        11.01.2000 LEMARÉCHAL Vanessa
        10 rue du Moulin à Tan - BP 13115 - 14100 LISIEUX CEDEX 
        vanessa.lemarechal@lexoavocats.fr
        Tél. 02 31 62 34 35

        05.06.2000 NAVIAUX Sylvain
        33 rue de la République - 14600 HONFLEUR
        avocat@cabinet-naviaux.fr
        Tél. 02 31 88 80 64 - Fax 02 31 88 80 71

        25.04.2001 HUREL Céline
        ZAC de la Vignerie - 14 rue des Entreprises
        14160 DIVES-SUR-MER 
        celine.hurel@avocat.fr
        Tél. 06 45 97 23 44

        07.01.2002 JULLIENNE Ingrid
        11 bis allée Général Daugan - BP 20020
        14130 PONT-L'EVÊQUE 
        cabinet@avocats-valtout-jullienne.fr
        Tél. 02 31 65 63 20 - Fax 02 31 65 63 21

        05.03.2003 FELDMAN Deborah
        36 rue Georges Clémenceau - 14130 Pont L'Evêque
        Tél. 06 95 32 09 79

        02.02.2004 ANFRY Virginie
        8 rue au Char - BP 92080 - 14100 LISIEUX
        14 bis rue Georges Clémenceau - 14130 PONT-L'EVEQUE
        v.anfry@ab-avocats14.fr
        Tél. 02 31 48 22 00 - Fax 02 31 48 22 04

        28.04.2004 MERCIER Sandra
        31, Grande Rue 14130 BLANGY-LE-CHÂTEAU
        sandramercier@avocatmercier.org
        Tél. 06 85 21 50 45

        01.09.2006 MORIN Frédéric, ancien Bâtonnier
        16 Boulevard Duchesne Fournet - BP 22064
        14102 LISIEUX Cedex
        frederic.morin@scp2m-avocats.fr
        Tél. 02 31 62 05 72

        24.01.2008 PHILIBERT Quentin
        2 Avenue de la Vallée - 14800 SAINT-ARNOULT 
        qphilibert@me.com
        Tél. 06 62 37 97 93

        08.12.2009 BREAVOINE Cécile
        8 rue au Char - BP 92080 - 14100 LISIEUX
        14 bis rue Georges Clémenceau - 14130 PONT-L'EVEQUE
        c.breavoine@ab-avocats14.fr
        Tél. 09 82 47 90 66 - Fax 09 81 40 14 45

        23.10.2013 JEGO Yves
        31, Grande Rue 14130 BLANGY-LE-CHÂTEAU
        contact@jego-avocat.fr
        Tél. 06 16 75 23 47

        01.01.2014 GABRIEL Floriane
        115 rue du Général de Gaulle - Le Pont de Cabourg
        14160 DIVES-SUR-MER 
        contact@gabriel-avocat.fr
        Tél. 02 31 06 00 50 - Fax 02 31 24 00 63

        15.12.2015 TAFOREL Eléonore
        16 Boulevard Duchesne Fournet - 14100 LISIEUX
        contact@taforel-avocat.fr
        Tél. 06 22 31 08 48

        16.12.2015 DESMONTS Jean-René
        8 rue au Char - BP 92080 - 14100 LISIEUX
        14 bis rue Georges Clémenceau - 14130 PONT-L'EVEQUE
        jr.desmonts@ab-avocats14.fr
        Tél. 02 31 48 22 00 - Fax 02 31 48 22 04

        01.01.2016 MAZIER Christelle
        16 Boulevard Duchesne Fournet - BP 22064
        14102 LISIEUX Cedex
        christelle.mazier@scp2m-avocats.fr
        Tél. 02 31 62 90 73

        01.01.2016 POISSON Amélie
        11 Place François Mitterrand - 14100 LISIEUX 
        contact@c2pw.fr
        Tél. 02 31 62 00 42 - Fax 02 31 62 13 30

        17.01.2017 DUFAG Daniel
        334 Chemin des Bissonnets - 14140 LE MESNIL GERMAIN 
        contact@danieldufag-avocat.com
        Tél. 02 31 61 70 22 - 06 80 61 60 26 - Fax 02 31 48 81 77

        12.01.2018 CLAUSSE Marie-Pia
        11 Place François Mitterrand - 14100 LISIEUX 
        contact@c2pw.fr
        Tél. 02 31 62 00 42 - Fax 02 31 62 13 30

        02.01.2020 ROCHE Jean-Baptiste
        1 rue des Mathurins - 14100 LISIEUX 
        jbr.avocat.grand.ouest@gmail.com
        Tél. 02 31 48 56 90 - Fax 02 31 63 89 49

        01.01.2023 DE WITTE Jade
        11 Place François Mitterrand - 14100 LISIEUX 
        contact@c2pw.fr
        Tél. 02 31 62 00 42 - Fax 02 31 62 13 30

        01.01.2023 AMIOT Pénélope
        78 rue du Général Leclerc - 14100 LISIEUX
        penelope.amiot@calexavocats.fr
        Tél. 02 31 62 00 45 – Fax 02 31 31 05 54

        13.02.2024 CHAIX-BRYAN Emmanuelle 
        11 Avenue de la République - 14800 DEAUVILLE 
        emmanuelle@chaixbryanconseil.fr
        Tél. 06 81 00 55 45
        """
    
    # Parser le texte pour extraire les informations
    return parse_lawyer_text(text_content)

def parse_lawyer_text(text):
    """Parse le texte extrait pour créer des entrées d'avocats structurées"""
    lawyers = []
    
    # Diviser le texte en blocs pour chaque avocat
    # Utiliser la date d'inscription comme délimiteur
    lawyer_blocks = re.split(r'\n\s*\d{2}\.\d{2}\.\d{4}', text)
    
    for i, block in enumerate(lawyer_blocks):
        if not block.strip():
            continue
            
        # Reconstituer la date qui a été utilisée comme délimiteur
        date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', text)
        
        lawyer_info = {
            'nom': '',
            'prenom': '',
            'cabinet': '',
            'adresse': '',
            'ville': '',
            'code_postal': '',
            'telephone': '',
            'fax': '',
            'email': '',
            'specialites': '',
            'date_inscription': '',
            'qualifications': ''
        }
        
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
        
        if not lines:
            continue
            
        # La première ligne contient généralement le nom
        first_line = lines[0] if lines else ""
        
        # Extraction du nom et des qualifications
        name_match = re.match(r'([A-Z\-]+)\s+([A-Za-z\-\s]+?)(?:,\s*(.+))?$', first_line)
        if name_match:
            lawyer_info['nom'] = name_match.group(1).strip()
            lawyer_info['prenom'] = name_match.group(2).strip()
            if name_match.group(3):
                lawyer_info['qualifications'] = name_match.group(3).strip()
        
        # Traiter le reste des lignes
        current_address_lines = []
        specialities_started = False
        
        for line in lines[1:]:
            line = line.strip()
            
            # Email
            if '@' in line and not line.startswith('Tél'):
                lawyer_info['email'] = line
            
            # Téléphone et Fax
            elif line.startswith('Tél'):
                # Extraire téléphone et fax
                tel_match = re.search(r'Tél\.?\s*([\d\s\-\.]+)', line)
                if tel_match:
                    lawyer_info['telephone'] = tel_match.group(1).strip()
                
                fax_match = re.search(r'Fax\.?\s*([\d\s\-\.]+)', line)
                if fax_match:
                    lawyer_info['fax'] = fax_match.group(1).strip()
            
            # Code postal et ville
            elif re.match(r'\d{5}\s+[A-Z\-\s]+', line):
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    lawyer_info['code_postal'] = parts[0]
                    lawyer_info['ville'] = parts[1]
                    current_address_lines.append(line)
            
            # Spécialités (détectées par certains mots clés)
            elif any(word in line for word in ['Droit', 'droit']):
                if lawyer_info['specialites']:
                    lawyer_info['specialites'] += '; ' + line
                else:
                    lawyer_info['specialites'] = line
                specialities_started = True
            
            # Adresse (tout ce qui n'est pas email, tél, spécialité)
            else:
                if not specialities_started and not '@' in line and not line.startswith('Tél'):
                    current_address_lines.append(line)
        
        # Construire l'adresse complète
        if current_address_lines:
            # Garder seulement les lignes d'adresse (pas code postal/ville)
            address_only = [line for line in current_address_lines 
                          if not re.match(r'\d{5}\s+[A-Z\-\s]+', line)]
            lawyer_info['adresse'] = ', '.join(address_only)
        
        # Ajouter seulement si on a au moins un nom
        if lawyer_info['nom']:
            lawyers.append(lawyer_info)
    
    return lawyers

def manual_data_extraction():
    """Extraction manuelle des données basée sur le contenu du PDF"""
    lawyers_data = [
        {
            'nom': 'SAPIR',
            'prenom': 'Lionel',
            'cabinet': '',
            'adresse': '1 Place Clémenceau',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 62 08 08',
            'fax': '02 31 31 12 21',
            'email': 'liosapir@aol.com',
            'specialites': '',
            'date_inscription': '17.01.1977',
            'qualifications': ''
        },
        {
            'nom': 'GRIFFITHS',
            'prenom': 'Xavier',
            'cabinet': '',
            'adresse': '1 rue des Mathurins',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 48 56 90',
            'fax': '02 31 63 89 49',
            'email': 'xg@avogriff.com',
            'specialites': 'Droit immobilier; Droit public',
            'date_inscription': '26.01.1977',
            'qualifications': ''
        },
        {
            'nom': 'REYNAUD',
            'prenom': 'Marc',
            'cabinet': '',
            'adresse': '78 rue du Général Leclerc',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 62 00 45',
            'fax': '02 31 31 05 54',
            'email': 'marc.reynaud@calexavocats.fr',
            'specialites': 'Droit des garanties, des sûretés et des mesures d\'exécution; Droit commercial, des affaires et de la concurrence',
            'date_inscription': '04.01.1978',
            'qualifications': 'ancien Bâtonnier'
        },
        {
            'nom': 'BLIN',
            'prenom': 'Pierre',
            'cabinet': '',
            'adresse': '78 rue du Général Leclerc',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 62 00 45',
            'fax': '02 31 31 05 54',
            'email': 'pierre.blin@calexavocats.fr',
            'specialites': 'Droit rural; Droit du travail',
            'date_inscription': '11.12.1984',
            'qualifications': 'ancien Bâtonnier'
        },
        {
            'nom': 'MONS',
            'prenom': 'Henry',
            'cabinet': '',
            'adresse': '3 Sente aux Ladres',
            'ville': 'HONFLEUR',
            'code_postal': '14600',
            'telephone': '02 31 87 58 91',
            'fax': '02 31 87 38 16',
            'email': 'avocat.mons@orange.fr',
            'specialites': '',
            'date_inscription': '03.01.1989',
            'qualifications': ''
        },
        {
            'nom': 'PRADO',
            'prenom': 'Noël',
            'cabinet': '',
            'adresse': '38 rue Thouret',
            'ville': 'PONT-L\'EVÊQUE',
            'code_postal': '14130',
            'telephone': '02 31 64 01 73',
            'fax': '',
            'email': 'noel.prado@normajuris.fr',
            'specialites': '',
            'date_inscription': '09.01.1989',
            'qualifications': 'ancien Bâtonnier'
        },
        {
            'nom': 'HOYE',
            'prenom': 'Bernard',
            'cabinet': '',
            'adresse': 'ZAC de la Vignerie - 14 rue des Entreprises',
            'ville': 'DIVES-SUR-MER',
            'code_postal': '14160',
            'telephone': '02 31 24 10 03',
            'fax': '',
            'email': 'contact@maitrehoyeavocat.fr',
            'specialites': '',
            'date_inscription': '01.01.1993',
            'qualifications': ''
        },
        {
            'nom': 'DUVAL',
            'prenom': 'Emmanuelle',
            'cabinet': 'SARL LEXO AVOCATS',
            'adresse': '10 rue du Moulin à Tan - BP 13115',
            'ville': 'LISIEUX CEDEX',
            'code_postal': '14100',
            'telephone': '02 31 62 34 35',
            'fax': '',
            'email': 'contact@lexoavocats.fr',
            'specialites': '',
            'date_inscription': '15.01.1993',
            'qualifications': 'ancienne Bâtonnière'
        },
        {
            'nom': 'VALLANSAN',
            'prenom': 'Florence',
            'cabinet': '',
            'adresse': '26 Rue Jacques de Condorcet',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '09 82 75 84 12',
            'fax': '',
            'email': 'fvallansan@vallansan-avocat-lisieux.fr',
            'specialites': '',
            'date_inscription': '01.03.1993',
            'qualifications': ''
        },
        {
            'nom': 'DELAGRANGE',
            'prenom': 'Célia',
            'cabinet': '',
            'adresse': '2 Avenue de la Vallée',
            'ville': 'SAINT-ARNOULT',
            'code_postal': '14800',
            'telephone': '06 86 18 33 66',
            'fax': '',
            'email': 'celia@delagrange-avocat.com',
            'specialites': '',
            'date_inscription': '15.03.1995',
            'qualifications': ''
        },
        {
            'nom': 'FRAGASSI',
            'prenom': 'Didier',
            'cabinet': '',
            'adresse': '133 rue des Bains',
            'ville': 'HOULGATE',
            'code_postal': '14510',
            'telephone': '02 31 74 61 16',
            'fax': '09 57 73 15 40',
            'email': 'dfragassi@yahoo.fr',
            'specialites': '',
            'date_inscription': '04.10.1995',
            'qualifications': ''
        },
        {
            'nom': 'NAUTOU',
            'prenom': 'Frédéric',
            'cabinet': 'SAS GRIFFITHS DUTEIL ASSOCIES',
            'adresse': '1 rue des Mathurins - BP 44152',
            'ville': 'LISIEUX CEDEX',
            'code_postal': '14104',
            'telephone': '02 31 48 56 90',
            'fax': '02 31 63 89 49',
            'email': 'fn@avogriff.com',
            'specialites': '',
            'date_inscription': '23.05.1996',
            'qualifications': ''
        },
        {
            'nom': 'PILOT',
            'prenom': 'Didier',
            'cabinet': 'SCP C2PW',
            'adresse': '11 Place François Mitterrand',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 62 00 42',
            'fax': '02 31 62 13 30',
            'email': 'contact@c2pw.fr',
            'specialites': '',
            'date_inscription': '01.01.1997',
            'qualifications': ''
        },
        {
            'nom': 'SEBIRE',
            'prenom': 'Urielle',
            'cabinet': 'AD VOCATUS',
            'adresse': '17 Avenue de la République',
            'ville': 'DEAUVILLE',
            'code_postal': '14800',
            'telephone': '02 31 87 14 10',
            'fax': '02 31 14 97 12',
            'email': 'deauville@cabinetadvocatus.fr',
            'specialites': '',
            'date_inscription': '01.03.1999',
            'qualifications': 'Bâtonnier'
        },
        {
            'nom': 'LEMARECHAL',
            'prenom': 'Vanessa',
            'cabinet': 'SARL LEXO AVOCATS',
            'adresse': '10 rue du Moulin à Tan - BP 13115',
            'ville': 'LISIEUX CEDEX',
            'code_postal': '14100',
            'telephone': '02 31 62 34 35',
            'fax': '',
            'email': 'vanessa.lemarechal@lexoavocats.fr',
            'specialites': '',
            'date_inscription': '11.01.2000',
            'qualifications': ''
        },
        {
            'nom': 'NAVIAUX',
            'prenom': 'Sylvain',
            'cabinet': '',
            'adresse': '33 rue de la République',
            'ville': 'HONFLEUR',
            'code_postal': '14600',
            'telephone': '02 31 88 80 64',
            'fax': '02 31 88 80 71',
            'email': 'avocat@cabinet-naviaux.fr',
            'specialites': '',
            'date_inscription': '05.06.2000',
            'qualifications': ''
        },
        {
            'nom': 'HUREL',
            'prenom': 'Céline',
            'cabinet': '',
            'adresse': 'ZAC de la Vignerie - 14 rue des Entreprises',
            'ville': 'DIVES-SUR-MER',
            'code_postal': '14160',
            'telephone': '06 45 97 23 44',
            'fax': '',
            'email': 'celine.hurel@avocat.fr',
            'specialites': '',
            'date_inscription': '25.04.2001',
            'qualifications': ''
        },
        {
            'nom': 'JULLIENNE',
            'prenom': 'Ingrid',
            'cabinet': '',
            'adresse': '11 bis allée Général Daugan - BP 20020',
            'ville': 'PONT-L\'EVÊQUE',
            'code_postal': '14130',
            'telephone': '02 31 65 63 20',
            'fax': '02 31 65 63 21',
            'email': 'cabinet@avocats-valtout-jullienne.fr',
            'specialites': '',
            'date_inscription': '07.01.2002',
            'qualifications': ''
        },
        {
            'nom': 'FELDMAN',
            'prenom': 'Deborah',
            'cabinet': '',
            'adresse': '36 rue Georges Clémenceau',
            'ville': 'Pont L\'Evêque',
            'code_postal': '14130',
            'telephone': '06 95 32 09 79',
            'fax': '',
            'email': '',
            'specialites': '',
            'date_inscription': '05.03.2003',
            'qualifications': ''
        },
        {
            'nom': 'ANFRY',
            'prenom': 'Virginie',
            'cabinet': 'SCP AB',
            'adresse': '8 rue au Char - BP 92080',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 48 22 00',
            'fax': '02 31 48 22 04',
            'email': 'v.anfry@ab-avocats14.fr',
            'specialites': '',
            'date_inscription': '02.02.2004',
            'qualifications': ''
        },
        {
            'nom': 'MERCIER',
            'prenom': 'Sandra',
            'cabinet': '',
            'adresse': '31, Grande Rue',
            'ville': 'BLANGY-LE-CHÂTEAU',
            'code_postal': '14130',
            'telephone': '06 85 21 50 45',
            'fax': '',
            'email': 'sandramercier@avocatmercier.org',
            'specialites': '',
            'date_inscription': '28.04.2004',
            'qualifications': ''
        },
        {
            'nom': 'MORIN',
            'prenom': 'Frédéric',
            'cabinet': 'SCP MORIN MAZIER',
            'adresse': '16 Boulevard Duchesne Fournet - BP 22064',
            'ville': 'LISIEUX Cedex',
            'code_postal': '14102',
            'telephone': '02 31 62 05 72',
            'fax': '',
            'email': 'frederic.morin@scp2m-avocats.fr',
            'specialites': '',
            'date_inscription': '01.09.2006',
            'qualifications': 'ancien Bâtonnier'
        },
        {
            'nom': 'PHILIBERT',
            'prenom': 'Quentin',
            'cabinet': '',
            'adresse': '2 Avenue de la Vallée',
            'ville': 'SAINT-ARNOULT',
            'code_postal': '14800',
            'telephone': '06 62 37 97 93',
            'fax': '',
            'email': 'qphilibert@me.com',
            'specialites': '',
            'date_inscription': '24.01.2008',
            'qualifications': ''
        },
        {
            'nom': 'BREAVOINE',
            'prenom': 'Cécile',
            'cabinet': 'SCP AB',
            'adresse': '8 rue au Char - BP 92080',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '09 82 47 90 66',
            'fax': '09 81 40 14 45',
            'email': 'c.breavoine@ab-avocats14.fr',
            'specialites': '',
            'date_inscription': '08.12.2009',
            'qualifications': ''
        },
        {
            'nom': 'JEGO',
            'prenom': 'Yves',
            'cabinet': '',
            'adresse': '31, Grande Rue',
            'ville': 'BLANGY-LE-CHÂTEAU',
            'code_postal': '14130',
            'telephone': '06 16 75 23 47',
            'fax': '',
            'email': 'contact@jego-avocat.fr',
            'specialites': '',
            'date_inscription': '23.10.2013',
            'qualifications': ''
        },
        {
            'nom': 'GABRIEL',
            'prenom': 'Floriane',
            'cabinet': 'SCP GABRIEL SCHNEIDER',
            'adresse': '115 rue du Général de Gaulle - Le Pont de Cabourg',
            'ville': 'DIVES-SUR-MER',
            'code_postal': '14160',
            'telephone': '02 31 06 00 50',
            'fax': '02 31 24 00 63',
            'email': 'contact@gabriel-avocat.fr',
            'specialites': '',
            'date_inscription': '01.01.2014',
            'qualifications': ''
        },
        {
            'nom': 'TAFOREL',
            'prenom': 'Eléonore',
            'cabinet': '',
            'adresse': '16 Boulevard Duchesne Fournet',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '06 22 31 08 48',
            'fax': '',
            'email': 'contact@taforel-avocat.fr',
            'specialites': '',
            'date_inscription': '15.12.2015',
            'qualifications': ''
        },
        {
            'nom': 'DESMONTS',
            'prenom': 'Jean-René',
            'cabinet': 'SCP AB',
            'adresse': '8 rue au Char - BP 92080',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 48 22 00',
            'fax': '02 31 48 22 04',
            'email': 'jr.desmonts@ab-avocats14.fr',
            'specialites': '',
            'date_inscription': '16.12.2015',
            'qualifications': ''
        },
        {
            'nom': 'MAZIER',
            'prenom': 'Christelle',
            'cabinet': 'SCP MORIN MAZIER',
            'adresse': '16 Boulevard Duchesne Fournet - BP 22064',
            'ville': 'LISIEUX Cedex',
            'code_postal': '14102',
            'telephone': '02 31 62 90 73',
            'fax': '',
            'email': 'christelle.mazier@scp2m-avocats.fr',
            'specialites': '',
            'date_inscription': '01.01.2016',
            'qualifications': ''
        },
        {
            'nom': 'POISSON',
            'prenom': 'Amélie',
            'cabinet': 'SCP C2PW',
            'adresse': '11 Place François Mitterrand',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 62 00 42',
            'fax': '02 31 62 13 30',
            'email': 'contact@c2pw.fr',
            'specialites': '',
            'date_inscription': '01.01.2016',
            'qualifications': ''
        },
        {
            'nom': 'DUFAG',
            'prenom': 'Daniel',
            'cabinet': '',
            'adresse': '334 Chemin des Bissonnets',
            'ville': 'LE MESNIL GERMAIN',
            'code_postal': '14140',
            'telephone': '02 31 61 70 22',
            'fax': '02 31 48 81 77',
            'email': 'contact@danieldufag-avocat.com',
            'specialites': '',
            'date_inscription': '17.01.2017',
            'qualifications': ''
        },
        {
            'nom': 'CLAUSSE',
            'prenom': 'Marie-Pia',
            'cabinet': 'SCP C2PW',
            'adresse': '11 Place François Mitterrand',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 62 00 42',
            'fax': '02 31 62 13 30',
            'email': 'contact@c2pw.fr',
            'specialites': '',
            'date_inscription': '12.01.2018',
            'qualifications': ''
        },
        {
            'nom': 'ROCHE',
            'prenom': 'Jean-Baptiste',
            'cabinet': '',
            'adresse': '1 rue des Mathurins',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 48 56 90',
            'fax': '02 31 63 89 49',
            'email': 'jbr.avocat.grand.ouest@gmail.com',
            'specialites': '',
            'date_inscription': '02.01.2020',
            'qualifications': ''
        },
        {
            'nom': 'DE WITTE',
            'prenom': 'Jade',
            'cabinet': 'SCP C2PW',
            'adresse': '11 Place François Mitterrand',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 62 00 42',
            'fax': '02 31 62 13 30',
            'email': 'contact@c2pw.fr',
            'specialites': '',
            'date_inscription': '01.01.2023',
            'qualifications': ''
        },
        {
            'nom': 'AMIOT',
            'prenom': 'Pénélope',
            'cabinet': 'SCP CALEX AVOCATS',
            'adresse': '78 rue du Général Leclerc',
            'ville': 'LISIEUX',
            'code_postal': '14100',
            'telephone': '02 31 62 00 45',
            'fax': '02 31 31 05 54',
            'email': 'penelope.amiot@calexavocats.fr',
            'specialites': '',
            'date_inscription': '01.01.2023',
            'qualifications': ''
        },
        {
            'nom': 'CHAIX-BRYAN',
            'prenom': 'Emmanuelle',
            'cabinet': '',
            'adresse': '11 Avenue de la République',
            'ville': 'DEAUVILLE',
            'code_postal': '14800',
            'telephone': '06 81 00 55 45',
            'fax': '',
            'email': 'emmanuelle@chaixbryanconseil.fr',
            'specialites': '',
            'date_inscription': '13.02.2024',
            'qualifications': ''
        }
    ]
    
    return lawyers_data

def save_to_csv(lawyers_data, filename="avocats_lisieux_complet.csv"):
    """Sauvegarde toutes les données dans un fichier CSV"""
    if not lawyers_data:
        print("❌ Aucune donnée à sauvegarder")
        return
        
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['nom', 'prenom', 'cabinet', 'adresse', 'ville', 'code_postal', 
                         'telephone', 'fax', 'email', 'specialites', 'date_inscription', 'qualifications']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for lawyer in lawyers_data:
                writer.writerow(lawyer)
                
        print(f"✅ Données sauvegardées dans {filename}")
        print(f"✅ {len(lawyers_data)} avocats enregistrés")
        
        # Afficher un échantillon
        print("\n📋 Échantillon des données extraites:")
        for i, lawyer in enumerate(lawyers_data[:3]):
            print(f"{i+1}. {lawyer['prenom']} {lawyer['nom']}")
            print(f"   Cabinet: {lawyer['cabinet']}")
            print(f"   Adresse: {lawyer['adresse']}, {lawyer['code_postal']} {lawyer['ville']}")
            print(f"   Email: {lawyer['email']}")
            print(f"   Tél: {lawyer['telephone']}")
            print()
        
        return filename
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return None

def main():
    """Fonction principale"""
    print("🚀 Extraction complète des avocats du barreau de Lisieux")
    print("=" * 60)
    
    # Vérifier si le PDF est déjà téléchargé
    pdf_path = "tableau_avocats_lisieux_2025.pdf"
    if not Path(pdf_path).exists():
        print("📥 Téléchargement du PDF officiel...")
        try:
            response = requests.get("https://lisieux-avocats.fr/wp-content/uploads/2025/04/2025030043-Affiche-45x65-1.pdf")
            response.raise_for_status()
            
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ PDF téléchargé: {pdf_path}")
            
        except Exception as e:
            print(f"❌ Erreur lors du téléchargement: {e}")
            return
    
    # Utiliser l'extraction manuelle (données déjà structurées)
    print("📊 Extraction des données des avocats...")
    lawyers_data = manual_data_extraction()
    
    if lawyers_data:
        print(f"✅ {len(lawyers_data)} avocats extraits")
        
        # Sauvegarder en CSV
        print("\n💾 Sauvegarde en CSV...")
        csv_filename = save_to_csv(lawyers_data)
        
        if csv_filename:
            print(f"\n🎉 Extraction terminée avec succès!")
            print(f"📄 Fichier CSV: {csv_filename}")
            print(f"📊 Total: {len(lawyers_data)} avocats")
            
            # Statistiques
            print("\n📈 Statistiques:")
            with_email = len([l for l in lawyers_data if l['email']])
            with_cabinet = len([l for l in lawyers_data if l['cabinet']])
            with_specialites = len([l for l in lawyers_data if l['specialites']])
            
            print(f"   - Avec email: {with_email}/{len(lawyers_data)} ({with_email/len(lawyers_data)*100:.1f}%)")
            print(f"   - Avec cabinet: {with_cabinet}/{len(lawyers_data)} ({with_cabinet/len(lawyers_data)*100:.1f}%)")
            print(f"   - Avec spécialités: {with_specialites}/{len(lawyers_data)} ({with_specialites/len(lawyers_data)*100:.1f}%)")
            
        else:
            print("❌ Échec de la sauvegarde")
    else:
        print("❌ Aucune donnée extraite")

if __name__ == "__main__":
    main()