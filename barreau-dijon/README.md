# Scraper Barreau de Dijon 🎯

Ce scraper permet d'extraire **TOUS les avocats** du Barreau de Dijon avec leurs informations complètes.

## 📊 Résultats
- **384 avocats extraits** (vs 22 avec l'ancienne version)
- **97.1% de taux de réussite** 
- **Gestion cookies corrigée** pour pagination complète
- **19 pages explorées** automatiquement

## 🚀 Utilisation

### Installation des dépendances
```bash
pip install selenium beautifulsoup4 pandas webdriver-manager
```

### Lancement du scraper
```bash
python dijon_scraper_final.py
```

### Modes disponibles
1. **Mode Test** : 10 avocats pour validation
2. **Mode Production** : Extraction complète (~384 avocats)

## 📁 Fichiers générés
- `DIJON_PRODUCTION_COMPLETE_XXX_avocats_YYYYMMDD_HHMMSS.csv` - Données complètes
- `DIJON_PRODUCTION_COMPLETE_XXX_avocats_YYYYMMDD_HHMMSS.json` - Format JSON
- `DIJON_PRODUCTION_COMPLETE_XXX_avocats_YYYYMMDD_HHMMSS_RAPPORT_COMPLET.txt` - Rapport détaillé
- `DIJON_PRODUCTION_COMPLETE_XXX_avocats_YYYYMMDD_HHMMSS_EMAILS_UNIQUES_XX.txt` - Liste emails

## 📈 Données extraites
- ✅ **Noms et prénoms** (parsing corrigé)
- ✅ **Années de serment** (96.9%)
- ✅ **Spécialisations** (97.1%)
- ✅ **Téléphones** (96.9%)
- ✅ **Adresses** (96.9%)
- ✅ **Emails** (34.9%)
- ✅ **URLs des fiches** (100%)

## 🔧 Correctifs apportés
- **Gestion cookies robuste** : Acceptation automatique des cookies RGPD
- **Pagination complète** : Navigation sur les 19 pages de résultats
- **Parsing amélioré** : Extraction propre des noms et adresses
- **Retry automatique** : 3 tentatives en cas d'échec
- **Sauvegardes** : Backup automatique tous les 50 avocats

## ⏱️ Performance
- **Temps d'exécution** : ~25 minutes pour 384 avocats
- **Vitesse moyenne** : 4 secondes par avocat
- **Mode headless** : Aucune interface graphique

## 🎯 URL cible
https://www.barreau-dijon.avocat.fr/annuaire-des-avocats-barreau-de-dijon/

## 📝 Notes techniques
- Le scraper gère automatiquement la bannière de cookies RGPD
- Navigation par construction d'URLs de pagination
- Extraction détaillée depuis les fiches individuelles
- Compatible avec Chrome/Chromium via webdriver-manager

## 🔄 Mise à jour
Pour relancer une extraction mise à jour, il suffit de relancer le script. Les fichiers de résultats sont horodatés automatiquement.