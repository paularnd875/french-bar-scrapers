# Scraper Barreau de Boulogne-sur-Mer

## Description
Scraper pour extraire tous les avocats du Barreau de Boulogne-sur-Mer.

**Site web**: https://avocats-boulogne.fr/annuaire-des-avocats-barreau-de-boulogne-sur-mer/

## Informations extraites
- ✅ **Prénom et Nom** (séparés automatiquement)
- ✅ **Email** (100% de réussite)
- ✅ **Téléphone** (format français)
- ✅ **Adresse complète** (rue, ville, code postal)
- ✅ **Ville et Code postal** (extraction automatique)
- ⚠️ **Année d'inscription** (non disponible sur ce site)
- ⚠️ **Spécialisations** (non disponible sur ce site)
- ⚠️ **Structure** (non disponible sur ce site)

## Résultats
- **120 avocats** extraits
- **100% de réussite** sur les données principales
- **Temps d'exécution**: ~11 secondes
- **Mode headless**: Aucune fenêtre n'interfère avec votre travail

## Utilisation

### Prérequis
```bash
pip install selenium beautifulsoup4
```

### Exécution
```bash
python3 boulogne_scraper_production.py
```

### Fichiers générés
- `boulogne_COMPLET_[timestamp].json` - Données structurées complètes
- `boulogne_COMPLET_[timestamp].csv` - Compatible Excel/Google Sheets
- `boulogne_EMAILS_COMPLET_[timestamp].txt` - Liste pure des emails
- `boulogne_RAPPORT_COMPLET_[timestamp].txt` - Rapport détaillé avec statistiques

## Fonctionnalités
- 🚀 **Mode headless** (sans interface)
- 🍪 **Gestion automatique des cookies** 
- 🔄 **Déduplication automatique** des emails
- 📊 **Rapports détaillés** avec statistiques
- ⚡ **Performances optimisées**
- 🛡️ **Gestion robuste des erreurs**

## Statistiques d'extraction
```
✅ Avec Email:          120 (100.0%)
✅ Avec Téléphone:      120 (100.0%)
✅ Avec Adresse:        120 (100.0%)
✅ Avec Ville:          114 ( 95.0%)
✅ Avec Code postal:    114 ( 95.0%)
❌ Avec Année:            0 (  0.0%) - Non disponible
❌ Avec Spécialisations:  0 (  0.0%) - Non disponible
❌ Avec Structure:        0 (  0.0%) - Non disponible
```

## Structure du site
Le site organise les avocats par année d'inscription (1985-2025) dans des blocs `avia_textblock`. Chaque bloc contient :
- Nom complet de l'avocat
- Numéro de téléphone
- Adresse email
- Adresse professionnelle complète

## Notes techniques
- Utilise **Selenium** pour la navigation
- Utilise **BeautifulSoup** pour l'analyse HTML  
- **Chrome headless** pour éviter les fenêtres
- Extraction basée sur les patterns d'emails
- Déduplication automatique par email unique