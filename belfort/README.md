# Scraper Barreau de Belfort

Scraper pour extraire les données des avocats du Barreau de Belfort depuis https://www.avocats-belfort.com/annuaire-avocats.htm

## 🎯 Données extraites

Pour chaque avocat :
- Prénom et nom
- Email ✅
- Téléphone 
- Adresse complète
- Année d'inscription au barreau
- Spécialisations juridiques (filtrées intelligemment)
- Structure/Cabinet

## 📊 Résultats

- **36 avocats** extraits avec succès
- **36 emails** récupérés (taux de réussite : 100%)
- **Durée :** 3.2 minutes
- **Mode :** Headless (sans interface graphique)

## 🚀 Utilisation

### Script de test (3 avocats)
```bash
python3 belfort_scraper_test.py
```

### Script complet (tous les avocats)
```bash
python3 belfort_scraper_production.py
```

## 📁 Fichiers générés

- `belfort_avocats_COMPLET_[timestamp].json` - Données complètes JSON
- `belfort_avocats_COMPLET_[timestamp].csv` - Format tableur
- `belfort_EMAILS_SEULEMENT_[timestamp].txt` - Liste d'emails uniquement
- `belfort_RAPPORT_COMPLET_[timestamp].txt` - Rapport détaillé

## ⚙️ Fonctionnalités

- ✅ Acceptation automatique des cookies
- ✅ Mode headless par défaut
- ✅ Sauvegarde progressive (toutes les 10 extractions)
- ✅ Anti-détection avancé
- ✅ Filtrage intelligent des spécialisations
- ✅ Extraction robuste avec multiples sélecteurs

## 📋 Dépendances

```bash
pip3 install selenium
```

Chrome/Chromium requis pour Selenium.

## 📈 Statistiques

- **Site :** https://www.avocats-belfort.com/annuaire-avocats.htm
- **Total avocats :** 36
- **Taux de réussite emails :** 100%
- **Date dernière extraction :** 10 février 2026