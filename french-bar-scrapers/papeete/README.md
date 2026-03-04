# Scraper Barreau de Papeete (Polynésie française)

## Description
Scraper pour extraire la liste complète des avocats inscrits au Barreau de Papeete en Polynésie française.

**Site web**: https://barreau-avocats.pf/avocats-inscrits-au-barreau-de-papeete/

## Fonctionnalités

### ✅ Données extraites
- **Nom de famille** (avec gestion des noms composés polynésiens)
- **Prénom(s)** (incluant prénoms multiples et prénoms tahitiens)
- **Email** (extraction complète des adresses email)
- **Téléphone** (numéros multiples supportés)
- **Adresse** (adresse complète du cabinet)
- **Source** (URL de vérification)

### 🏝️ Spécificités Polynésiennes
- **Séparation nom/prénom perfectionnée** : Gestion correcte des formats "NOM-COMPOSÉ Prénom(s)"
- **Noms tahitiens** : Support des noms polynésiens complexes
- **Prénoms multiples** : Ex: "Annick Hina", "Kari Lee", "Philippe Temauiarii"
- **Noms avec tirets** : Ex: "ALLAIN-SACAULT", "ARMOUR-LAZZARI"

## Utilisation

### Prérequis
```bash
pip install selenium beautifulsoup4 webdriver-manager
```

### Exécution
```bash
python papeete_scraper.py
```

Le script s'exécute automatiquement en mode production headless.

## Résultats

### 📊 Statistiques (dernière extraction)
- **Total d'avocats**: 108
- **Avec email**: 71 (65.7%)
- **Avec téléphone**: 67 (62.0%)
- **Avec adresses**: 74 (68.5%)

### 💾 Fichiers générés
- `PAPEETE_PRODUCTION_PERFECT_[nombre]_[timestamp].csv` - Données complètes
- `PAPEETE_PRODUCTION_PERFECT_[nombre]_[timestamp].json` - Format JSON
- `PAPEETE_PRODUCTION_EMAILS_PERFECT_[nombre]_[timestamp].txt` - Emails uniquement

## Approche technique

### 🔍 Méthode d'extraction
- **Parsing séquentiel HTML** : Analyse de la structure exacte du DOM
- **Gestion des cookies** : Acceptation automatique des bannières
- **Anti-détection** : User-agent et options Chrome optimisées

### 📝 Structure HTML analysée
```html
<div><b>NOM-FAMILLE Prénom(s)</b></div>
<div>40 XX XX XX</div>  <!-- téléphone 1 -->
<div>40 XX XX XX</div>  <!-- téléphone 2 -->
<div><a href="mailto:email@domain.com">email@domain.com</a></div>
<div>Adresse complète du cabinet</div>
<hr>
```

## Exemples de données extraites

```csv
prenom,nom,nom_complet,email,telephone,adresse
Annick Hina,ALLAIN-SACAULT,ALLAIN-SACAULT Annick Hina,allainsacault@yahoo.fr,"40 50 03 75, 40 82 69 66","8, Avenue Pouvanaa a Oopa, 2ème étage"
Kari Lee,ARMOUR-LAZZARI,ARMOUR-LAZZARI Kari Lee,karmourlaz@aol.com,"40 42 20 30, 40 42 20 31","Bureau 127, 4ème étage Centre Vaima"
Philippe Temauiarii,NEUFFER,NEUFFER Philippe Temauiarii,neuffer.avocat@mail.pf,"40 50 36 05, 40 50 36 06",""
```

## Développement

### 🧪 Mode test
Pour activer le mode test (10 avocats, interface visible), modifier le script :
```python
def main():
    scraper = PapeeteLawyerPerfectScraper(headless=False, test_mode=True)
```

### 🔧 Configuration
- **Timeout** : 15 secondes pour le chargement des pages
- **Anti-détection** : User-agent macOS, exclusion des flags automation
- **Gestion d'erreurs** : Try/catch avec logs détaillés

## Support

Ce scraper a été développé spécifiquement pour la structure unique du site du Barreau de Papeete et gère parfaitement les spécificités des noms polynésiens.

**Dernière mise à jour** : Février 2026
**Testé sur** : Site officiel du Barreau de Papeete