# Scraper du Barreau de Sens

## Description

Scraper complet pour extraire tous les avocats du Barreau de Sens depuis leur annuaire officiel.

**URL source**: https://www.barreau-sens-avocat.fr/annuaire

## Caractéristiques

### ✅ Données extraites
- **30 avocats** (totalité du barreau)
- **Prénoms et noms** séparés dans des colonnes distinctes
- **Adresses complètes** avec codes postaux
- **Numéros de téléphone** (100% des avocats)
- **Répartition géographique** (Sens, Saint-Julien-du-Sault, Charny)

### 🔧 Fonctionnalités techniques
- **Séparation intelligente** des prénoms/noms avec gestion des cas complexes
- **Gestion des caractères spéciaux** (Españita, Véronique, Céline, etc.)
- **Support des noms composés** (Anne-Gaëlle, Marie-Marguerite, etc.)
- **Gestion des particules** (LE CHEVOIR, etc.)
- **Format de sortie multiple** (CSV, JSON, rapport détaillé)

### ⚠️ Limitations connues
- **Emails** : Non disponibles publiquement sur le site
- **Spécialisations** : Non affichées dans l'annuaire
- **Dates de serment** : Non disponibles
- **Structures d'exercice** : Non précisées

## Installation

### Prérequis
```bash
pip install requests beautifulsoup4 pandas
```

### Téléchargement
```bash
wget https://raw.githubusercontent.com/paularnd875/french-bar-scrapers/main/sens/sens_barreau_scraper.py
```

## Utilisation

### Exécution simple
```bash
python3 sens_barreau_scraper.py
```

### Depuis un autre script
```python
from sens_barreau_scraper import SensBarreauScraper

scraper = SensBarreauScraper()
lawyers_data = scraper.scrape_all_lawyers()
files = scraper.save_results(lawyers_data)
```

## Structure des données

### Format CSV
```csv
nom_complet,prenom,nom_famille,adresse,code_postal,ville,telephone,email,structure,specialisations,annee_serment,source
Denis EVRARD,Denis,EVRARD,"4 et 6 boulevard du Mail, rez-de-chaussée",89100,SENS,03.86.83.55.32,,,,,https://www.barreau-sens-avocat.fr/annuaire
```

### Colonnes principales
| Colonne | Description | Exemple |
|---------|-------------|---------|
| `nom_complet` | Nom complet original | "Anne-Gaëlle LECOUR" |
| `prenom` | Prénom(s) séparé(s) | "Anne-Gaëlle" |
| `nom_famille` | Nom de famille | "LECOUR" |
| `adresse` | Adresse complète | "22 rue des Vieilles Etuves" |
| `code_postal` | Code postal | "89100" |
| `ville` | Ville | "SENS" |
| `telephone` | Numéro de téléphone | "03.73.61.02.70" |
| `source` | URL source | "https://www.barreau-sens-avocat.fr/annuaire" |

## Exemples de cas complexes traités

### Prénoms composés
- Anne-Gaëlle LECOUR → `prenom: "Anne-Gaëlle"`, `nom: "LECOUR"`
- Marie-Marguerite FIUMÉ → `prenom: "Marie-Marguerite"`, `nom: "FIUMÉ"`

### Noms composés
- Chantal DEVELAY-BARDE → `prenom: "Chantal"`, `nom: "DEVELAY-BARDE"`
- Véronique BOICHÉ-CALLUS → `prenom: "Véronique"`, `nom: "BOICHÉ-CALLUS"`

### Noms avec particules
- Laure LE CHEVOIR → `prenom: "Laure"`, `nom: "LE CHEVOIR"`

### Noms multiples
- Laure LICHÈRE LEMONNIER → `prenom: "Laure"`, `nom: "LICHÈRE LEMONNIER"`
- Magali DUBREUCQ TRUDDAÏU → `prenom: "Magali"`, `nom: "DUBREUCQ TRUDDAÏU"`

### Caractères spéciaux
- Españita ORTEGA → `prenom: "Españita"`, `nom: "ORTEGA"`
- Léonce KOLIMEDJE → `prenom: "Léonce"`, `nom: "KOLIMEDJE"`

## Fichiers de sortie

### Fichiers générés automatiquement
1. **CSV principal** : `SENS_BARREAU_PRODUCTION_30_avocats_YYYYMMDD_HHMMSS.csv`
2. **JSON complet** : `SENS_BARREAU_PRODUCTION_30_avocats_YYYYMMDD_HHMMSS.json`
3. **Liste téléphones** : `SENS_BARREAU_PRODUCTION_30_avocats_YYYYMMDD_HHMMSS_TELEPHONES_30.txt`
4. **Rapport détaillé** : `SENS_BARREAU_PRODUCTION_30_avocats_YYYYMMDD_HHMMSS_RAPPORT_COMPLET.txt`

## Statistiques du barreau

### Données générales
- **Total avocats** : 30
- **Taux de complétude téléphones** : 100%
- **Taux de complétude adresses** : 100%
- **Prénoms composés** : 2 (Anne-Gaëlle, Marie-Marguerite)
- **Noms composés** : 6 (DEVELAY-BARDE, BOICHÉ-CALLUS, etc.)

### Répartition géographique
- **SENS (89100)** : 28 avocats (93.3%)
- **SAINT JULIEN DU SAULT (89330)** : 1 avocat (3.3%)
- **CHARNY (89120)** : 1 avocat (3.3%)

## Maintenance et mise à jour

### Pour mettre à jour les données
```bash
# Relancer le scraper
python3 sens_barreau_scraper.py

# Les nouveaux fichiers seront générés avec un timestamp
ls SENS_BARREAU_PRODUCTION_*
```

### En cas de problème
1. **Vérifier la connectivité** : `ping barreau-sens-avocat.fr`
2. **Vérifier les dépendances** : `pip list | grep -E "requests|beautifulsoup4|pandas"`
3. **Consulter les logs** : Le script affiche des logs détaillés
4. **Contacter le développeur** : Ouvrir une issue sur GitHub

## Évolutions possibles

### Améliorations futures
- ✅ Séparation prénoms/noms (implémentée)
- ✅ Gestion des caractères spéciaux (implémentée)
- ✅ Rapport statistique détaillé (implémenté)
- ⚠️ Extraction emails (limitée par le site)
- ⚠️ Spécialisations (non disponibles sur le site)
- ⚠️ Dates de serment (non disponibles sur le site)

### Contact du barreau
- **Email général** : ordre@avocats-sens.fr
- **Site web** : https://www.barreau-sens-avocat.fr

---

*Scraper développé par Claude Code - Mars 2026*  
*Repository : https://github.com/paularnd875/french-bar-scrapers*