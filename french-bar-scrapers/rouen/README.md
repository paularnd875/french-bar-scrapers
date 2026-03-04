# Scraper Barreau de Rouen

## Description

Ce scraper extrait automatiquement les informations complètes de tous les avocats du Barreau de Rouen avec une correction spéciale pour les noms composés français.

**Site source:** https://www.barreau-rouen.avocat.fr

**Résultats:** 533+ avocats extraits avec correction des noms composés

## Fonctionnalités

✅ **Extraction complète des données:**
- Nom complet, prénom, nom de famille
- Email, téléphone, fax
- Année d'inscription au barreau
- Adresse complète
- URL source du profil

✅ **Correction des noms composés français:**
- "ABDOU Sophia" → prénom="Sophia", nom="ABDOU"
- "ALVES DA COSTA David" → prénom="David", nom="ALVES DA COSTA" 
- "CHAILLÉ DE NÉRÉ Dixie" → prénom="Dixie", nom="CHAILLÉ DE NÉRÉ"
- Gestion des particules (de, du, des, la, etc.)

✅ **Formats de sortie multiples:**
- CSV pour tableurs
- JSON pour applications
- TXT avec emails uniquement
- Rapport détaillé d'extraction

## Installation

1. Cloner le repository:
```bash
git clone https://github.com/paularnd875/french-bar-scrapers.git
cd french-bar-scrapers/rouen
```

2. Installer les dépendances:
```bash
pip install -r requirements.txt
```

3. S'assurer que Chrome/Chromium est installé pour Selenium.

## Utilisation

### Extraction complète (recommandé)
```bash
python3 run_extraction.py
```

### Test de la logique de noms
```bash
python3 test_name_separation.py
```

### Utilisation programmatique
```python
from rouen_scraper import RouenBarScraper

# Créer le scraper
scraper = RouenBarScraper()

# Lancer l'extraction (tous les avocats)
results = scraper.run_extraction(headless=True)

# Ou limiter le nombre d'avocats pour test
results = scraper.run_extraction(max_lawyers=10, headless=False)
```

## Structure des données extraites

### Format CSV/JSON
```
prenom,nom,nom_complet,email,telephone,fax,annee_inscription,adresse,source
Sophia,ABDOU,ABDOU Sophia,sophia.abdou@outlook.fr,02.35.71.16.32,,2022,1760433589.jpg,https://...
David,ALVES DA COSTA,M. ALVES DA COSTA David,david-alvesdacosta@orange.fr,02.35.88.20.84,,2004,2 boulevard de la Marne...
```

## Correction des noms composés

Le scraper utilise une logique avancée basée sur:

1. **Détection majuscules/minuscules:** 
   - "ABDOU Sophia" (nom en maj, prénom en min) → correctement séparé

2. **Noms avec particules:**
   - "CHAILLÉ DE NÉRÉ Dixie" → détecte "Dixie" comme prénom
   - "DE LA BRUNIÈRE Arnaud" → gère la particule en début

3. **Noms composés complexes:**
   - "ALVES DA COSTA David" → garde ensemble le nom portugais

## Fichiers générés

Après extraction, plusieurs fichiers sont créés:

- `ROUEN_EXTRACTION_FINAL_XXX_avocats_YYYYMMDD_HHMMSS.csv`
- `ROUEN_EXTRACTION_FINAL_XXX_avocats_YYYYMMDD_HHMMSS.json` 
- `ROUEN_EMAILS_FINAL_XXX_avocats_YYYYMMDD_HHMMSS.txt`
- `ROUEN_RAPPORT_FINAL_XXX_avocats_YYYYMMDD_HHMMSS.txt`

## Performance

- **Durée:** ~30-60 minutes pour 533 avocats
- **Sauvegarde automatique** tous les 50 avocats
- **Mode headless** pour performance optimale
- **Gestion des timeouts** et erreurs réseau

## Historique des corrections

### Version 1.0 - Correction noms composés
- ✅ Problème résolu: "CHAILLÉ DE NÉRÉ Dixie" mal séparé
- ✅ Logique basée sur majuscules/minuscules ajoutée
- ✅ Gestion des particules françaises améliorée
- ✅ Tests complets de validation

## Support

En cas de problème:
1. Vérifier que Chrome est installé
2. S'assurer d'une connexion internet stable
3. Les sauvegardes automatiques permettent de reprendre en cas d'interruption

## Notes techniques

- Utilise Selenium WebDriver avec Chrome headless
- Gestion Unicode complète pour les accents français
- Normalisation des données avec regex appropriés
- Logging détaillé pour debugging