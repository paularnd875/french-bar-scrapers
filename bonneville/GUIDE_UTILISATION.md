# Guide d'Utilisation - Scraper Barreau de Bonneville

## 🚀 Démarrage Rapide

### Installation
```bash
pip3 install -r requirements.txt
```

### Utilisation Simple
```bash
python3 run_scraper.py
```

## 📋 Scripts Disponibles

### Scripts Principaux

1. **`run_scraper.py`** - Script principal avec menu interactif
2. **`bonneville_scraper_final_optimise.py`** - Scraper complet optimisé
3. **`bonneville_email_verifier.py`** - Vérificateur et nettoyeur d'emails

### Scripts de Développement

4. **`bonneville_exhaustive_scraper.py`** - Extraction exhaustive (166+ entrées)
5. **`bonneville_cleaner.py`** - Nettoyage et déduplication
6. **`bonneville_final_parser.py`** - Parser final du PDF
7. **`bonneville_analyzer.py`** - Analyseur de structure de site
8. **`bonneville_test_scraper.py`** - Tests et validation

## 🎯 Résultats Attendus

- **53 avocats uniques** avec emails vérifiés
- **Informations complètes** : nom, prénom, email, téléphone, adresse, spécialisations
- **Formats multiples** : CSV, JSON, TXT
- **Mode headless** - aucune fenêtre

## 📁 Fichiers Générés

- `bonneville_VERIFIE_NETTOYE_53_avocats_YYYYMMDD_HHMMSS.csv`
- `bonneville_EMAILS_UNIQUES_VERIFIES_53_YYYYMMDD_HHMMSS.txt`
- `bonneville_RAPPORT_VERIFICATION_YYYYMMDD_HHMMSS.txt`

## 🔧 Personnalisation

Modifiez les variables dans `bonneville_scraper_final_optimise.py` :

- `pdf_url` - URL du PDF officiel
- `headless` - Mode sans fenêtre (True/False)
- Patterns de parsing dans `get_known_lawyers_database()`

## ⚠️ Dépannage

### Erreur Chrome/Selenium
```bash
brew install chromedriver
```

### Erreur PyMuPDF
```bash
pip3 install --upgrade PyMuPDF
```

### Fichier non trouvé
Vérifiez que vous êtes dans le bon dossier et que les fichiers JSON existent.

## 📊 Workflow Recommandé

1. **Extraction** - `python3 run_scraper.py` → Option 1
2. **Vérification** - Option 2 ou automatique
3. **Utilisation** - Fichiers CSV/JSON générés

## 🎉 Support

Tous les scripts sont documentés et autonomes. En cas de problème, vérifiez :

1. Dépendances installées
2. Connexion internet
3. Permissions d'écriture
4. Version Python >= 3.8