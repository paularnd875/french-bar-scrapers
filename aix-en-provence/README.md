# Scraper Barreau d'Aix-en-Provence

## 🎯 Description

Scraper complet et automatisé pour extraire tous les avocats du Barreau d'Aix-en-Provence avec leurs informations détaillées.

**URL Source :** https://barreauaix.com/grand-public/annuaire/

## 📊 Performances validées

- ✅ **940 avocats** extraits (100%)
- ✅ **939 emails** récupérés (99.9%)
- ✅ **940 téléphones** (100%)
- ✅ **940 adresses** (100%)
- ✅ **940 dates de serment** (100%)
- ✅ **219 spécialisations** (23.3%)

## 📁 Fichiers

### Scripts principaux
- `aix_scraper_production.py` - Script de production pour extraction complète
- `test_scraper.py` - Script de test (5 avocats) pour validation
- `requirements.txt` - Dépendances Python

### Documentation
- `README.md` - Ce fichier
- `GUIDE_UTILISATION.md` - Guide détaillé d'utilisation

## 🚀 Installation rapide

```bash
# 1. Cloner le repo
git clone https://github.com/paularnd875/french-bar-scrapers.git
cd french-bar-scrapers/aix-en-provence

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Tester (5 avocats)
python3 test_scraper.py

# 4. Production complète (940 avocats)
python3 aix_scraper_production.py
```

## 📋 Colonnes extraites

| Colonne | Description | Exemple |
|---------|-------------|---------|
| `prenom` | Prénom de l'avocat | `Abdallah-Martin` |
| `nom` | Nom de famille | `Nadine` |
| `nom_complet` | Nom complet | `Abdallah-Martin Nadine` |
| `email` | Email professionnel | `nadine.abdallah.martin@gmail.com` |
| `telephone` | Téléphone | `0442381589` |
| `adresse` | Adresse complète | `2. Rue Goyrand 13100 AIX EN PROVENCE` |
| `date_serment` | Date complète du serment | `3 novembre 2010` |
| `annee_inscription` | Année d'inscription | `2010` |
| `specialisations` | Domaines d'expertise | `Droit des affaires; Droit pénal` |
| `url_fiche` | URL de la fiche | `https://barreauaix.com/avocat/...` |
| `latitude` | Coordonnée GPS | `43.525896` |
| `longitude` | Coordonnée GPS | `5.450724` |
| `source` | URL source | `https://barreauaix.com/grand-public/annuaire/` |

## ⚙️ Fonctionnalités techniques

- **Mode headless** : Aucune fenêtre ne s'ouvre
- **Acceptation automatique des cookies**
- **Extraction via FacetWP JavaScript** (ultra-rapide)
- **Parsing HTML précis** avec sélecteurs spécifiques
- **Sauvegardes multiples** : CSV, JSON, emails séparés
- **Sauvegardes intermédiaires** tous les 100 avocats
- **Gestion d'erreurs robuste**
- **Respect des serveurs** (pauses de 2s entre requêtes)

## 📈 Résultats attendus

### Temps d'exécution
- **Test (5 avocats)** : ~30 secondes
- **Production (940 avocats)** : ~50 minutes

### Fichiers générés
- `AIX_FINAL_COMPLET_940_avocats_[timestamp].csv` - Base complète
- `AIX_FINAL_COMPLET_EMAILS_SEULEMENT_[timestamp].txt` - Emails purs
- `AIX_FINAL_COMPLET_[timestamp].json` - Format JSON
- `AIX_FINAL_COMPLET_RAPPORT_[timestamp].txt` - Rapport détaillé

## 🛠️ Maintenance

Pour mettre à jour la base de données :

1. Relancer simplement : `python3 aix_scraper_production.py`
2. Les nouveaux fichiers auront un timestamp différent
3. Comparer les totaux d'avocats pour détecter les changements

## 📞 Support

Ce scraper a été développé et testé avec succès en février 2026.

**Dernière extraction réussie :** 24/02/2026 - 940 avocats
**Taux de succès :** 99.9% emails, 100% autres données