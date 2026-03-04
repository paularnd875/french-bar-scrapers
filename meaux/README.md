# Scraper Barreau de Meaux

Extraction complète des avocats du Barreau de Meaux avec découverte automatique des pages cachées et optimisation des données de cabinets.

## 📊 Résultats Attendus

- **~185 avocats** (incluant pages cachées 15-19)
- **99%+ d'emails** collectés
- **55%+ de cabinets** identifiés (après post-traitement)
- **Formats de sortie**: CSV, JSON, TXT

## 🚀 Utilisation Rapide

### Option 1: Script Automatique (Recommandé)
```bash
python3 run_complete_extraction.py
```

### Option 2: Étapes Manuelles

#### 1. Extraction Principale
```bash
python3 meaux_scraper_main.py
```

#### 2. Post-Traitement des Cabinets (Optionnel)
```bash
python3 meaux_cabinet_enhancer.py MEAUX_AVOCATS_185avocats_YYYYMMDD_HHMMSS.json
```

## 📁 Structure des Fichiers

### Scripts Principaux
- `meaux_scraper_main.py` - Scraper principal avec découverte pages cachées
- `meaux_cabinet_enhancer.py` - Post-traitement intelligent des cabinets
- `run_complete_extraction.py` - Script automatique complet
- `README.md` - Cette documentation
- `requirements.txt` - Dépendances Python

### Fichiers Générés
- `MEAUX_AVOCATS_XXXavocats_YYYYMMDD_HHMMSS.csv` - Données principales CSV
- `MEAUX_AVOCATS_XXXavocats_YYYYMMDD_HHMMSS.json` - Données principales JSON  
- `MEAUX_EMAILS_XXXuniques_YYYYMMDD_HHMMSS.txt` - Liste emails uniquement
- `MEAUX_ENHANCED_XXXavocats_ENHANCED_YYYYMMDD_HHMMSS.*` - Données avec cabinets améliorés

## 🔧 Installation

```bash
pip install selenium beautifulsoup4 requests
```

**Chrome/Chromium requis** pour Selenium WebDriver.

## 📊 Données Extraites

### Informations Principales
- Nom et prénom (parsing intelligent des particules)
- Email et téléphone
- Date de serment
- Page source et lien

### Informations Complémentaires
- Cabinet/Structure (optimisé par post-traitement)
- Activités dominantes
- Spécialisations
- Langues supplémentaires

## 🎯 Fonctionnalités Avancées

### Découverte Pages Cachées
Le scraper détecte automatiquement les pages 15-19 non visibles dans la pagination normale, permettant de récupérer les 45 avocats supplémentaires.

### Post-Traitement Intelligent
L'outil `meaux_cabinet_enhancer.py` analyse les emails pour :
- Identifier automatiquement les cabinets via les domaines
- Détecter les groupes d'avocats partageant le même cabinet  
- Passer de ~15% à ~55% de cabinets identifiés

### Exemples d'Améliorations
- `contact@fidal.com` → `FIDAL`
- `avocat@cabinet-martin.fr` → `Cabinet Martin`
- `john.doe@touraut-avocats.com` → `Touraut & Associés`

## 🌐 Source

**URL Cible**: https://ordreavocats-meaux.fr/fr/annuaire  
**Repository**: https://github.com/paularnd875/french-bar-scrapers

## 📈 Historique Performance

| Version | Avocats | Emails | Cabinets | Pages |
|---------|---------|---------|----------|-------|
| v1.0 | 140 | 99% | 30% | 1-14 |
| v2.0 | 185 | 99% | 55% | 1-19 |

## 🛠️ Maintenance

Pour mettre à jour les données :
1. Relancer `python3 run_complete_extraction.py` 
2. Les fichiers sont horodatés automatiquement

## ⚙️ Configuration

### Mode Headless
Par défaut en mode headless (pas d'interface graphique). Pour déboguer :
```python
scraper = MeauxBarreauScraper(headless=False)
```

### Timeout Personnalisé
```python
scraper = MeauxBarreauScraper(timeout=30)  # 30 secondes
```

## 📞 Support

Développé pour le projet **French Bar Scrapers**.  
Issues: https://github.com/paularnd875/french-bar-scrapers/issues