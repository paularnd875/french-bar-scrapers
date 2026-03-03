# Scraper du Barreau de Chambéry

## 📋 Présentation

Ce dossier contient les scripts pour extraire automatiquement tous les avocats du barreau de Chambéry depuis leur annuaire en ligne.

**URL source** : https://www.barreau-chambery.fr/annuaire/

## 🎯 Résultats

- ✅ **266 avocats** extraits (100% du barreau)
- ✅ **255 emails uniques** récupérés (96% de taux de succès) 
- ✅ **101 structures/cabinets** identifiés
- ✅ **26 spécialisations** détectées
- ✅ **Extraction en < 1 seconde** ⚡

## 📁 Fichiers

### Scripts principaux

- `chambery_scraper_final.py` - **Script de production final** (extraction complète)
- `chambery_scraper_corrected.py` - Script de test (20 avocats)

### Scripts d'utilisation

```bash
# Extraction complète de tous les avocats
python3 chambery_scraper_final.py

# Test avec 20 avocats seulement  
python3 chambery_scraper_corrected.py
```

## 🔧 Caractéristiques techniques

### ✅ Points forts
- **Mode headless** : Pas d'ouverture de fenêtres
- **Pas de Selenium** : Utilise requests + BeautifulSoup (plus rapide)
- **Pas de cookies bloquants** : Extraction directe possible
- **Structure simple** : Toutes les données sur une seule page
- **Emails visibles** : Aucun email obfusqué ou caché

### 📊 Données extraites

Pour chaque avocat :
- **Prénom** (correctement séparé)
- **Nom** (correctement séparé)  
- **Nom complet**
- **Structure/Cabinet** (quand disponible)
- **Spécialisations** (liste complète)
- **Activités dominantes**
- **Adresse complète**
- **Ville**
- **Téléphone**
- **Email**
- **Année de serment**
- **URL source** (pour vérification)

## 📈 Statistiques des dernières données

### Distribution des spécialisations
- Procédure d'appel : 7 avocats
- Droit du dommage corporel : 4 avocats
- Droit pénal, sociétés, travail : 3 chacun
- + 10 autres spécialisations

### Principales structures
- SELAS CABINET GOUTAGNY : 7 avocats
- SCP ARMAND - CHAT & ASSOCIÉS : 4 avocats
- SELAS CABINET FIDAL : 4 avocats
- + 65 autres structures

### Années de serment
- Plus ancienne : 1976
- Plus récente : 2025
- Médiane : 2008

## 📋 Dépendances

```bash
pip install requests beautifulsoup4
```

## 🚀 Utilisation rapide

```bash
# Cloner le repository
git clone https://github.com/paularnd875/french-bar-scrapers.git
cd french-bar-scrapers/chambery

# Installer les dépendances
pip install -r ../requirements.txt

# Lancer l'extraction complète
python3 chambery_scraper_final.py
```

## 📄 Fichiers générés

Après exécution, le script génère :

1. **CSV** : `CHAMBERY_PRODUCTION_FINAL_266avocats_YYYYMMDD_HHMMSS.csv`
2. **JSON** : `CHAMBERY_PRODUCTION_FINAL_266avocats_YYYYMMDD_HHMMSS.json`
3. **Emails** : `CHAMBERY_EMAILS_FINAUX_XXXuniques_YYYYMMDD_HHMMSS.txt`
4. **Rapport** : `CHAMBERY_RAPPORT_PRODUCTION_FINAL_YYYYMMDD_HHMMSS.txt`

## ⚡ Performance

- **Temps d'extraction** : < 1 seconde
- **Taux de succès emails** : 96%
- **Aucune limite de taux** détectée
- **Pas de mesures anti-scraping**

## 🔄 Maintenance

Le script peut être relancé à tout moment pour mettre à jour les données. La structure du site étant stable, aucune modification n'est normalement nécessaire.

## 📅 Dernière mise à jour

- **Date** : 03/03/2026
- **Version** : 1.0
- **Statut** : ✅ Opérationnel

## 🛠️ Résolution de problèmes

### Erreurs courantes

1. **Timeout de connexion**
   ```bash
   # Relancer le script, le site peut être temporairement indisponible
   python3 chambery_scraper_final.py
   ```

2. **Changement de structure du site**
   ```bash
   # Tester d'abord avec le script de test
   python3 chambery_scraper_corrected.py
   ```

3. **Problème d'encodage**
   ```bash
   # S'assurer que l'environnement supporte UTF-8
   export LC_ALL=fr_FR.UTF-8
   ```

## 📞 Support

En cas de problème, vérifier :
1. La connexion internet
2. Que le site source est accessible
3. Les dépendances Python installées
4. Les permissions d'écriture dans le répertoire

---

*Script développé pour l'extraction automatisée des données du barreau de Chambéry*