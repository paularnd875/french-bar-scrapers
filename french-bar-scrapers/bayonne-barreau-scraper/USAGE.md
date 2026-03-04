# Guide d'utilisation - Scraper Bayonne

## 🚀 Lancement rapide

### Option 1: Script automatique
```bash
./run_bayonne_scraper.sh
```

### Option 2: Lancement direct Python
```bash
python3 bayonne_scraper_production.py
```

## 📁 Résultats attendus

Le script génère automatiquement 4 fichiers :

1. **`BAYONNE_PRODUCTION_XXX_avocats_YYYYMMDD_HHMMSS.csv`**
   - Données pour Excel/tableurs
   - Format: prenom,nom,adresse,annee_inscription,specialisations...

2. **`BAYONNE_PRODUCTION_XXX_avocats_YYYYMMDD_HHMMSS.json`** 
   - Format structuré pour traitement programmatique

3. **`BAYONNE_EMAILS_SEULEMENT_YYYYMMDD_HHMMSS.txt`**
   - Liste des emails extraits (si disponibles)

4. **`BAYONNE_RAPPORT_COMPLET_YYYYMMDD_HHMMSS.txt`**
   - Rapport détaillé avec statistiques

## ⚡ Performances

- **~171 avocats** extraits
- **Temps:** 8-15 minutes
- **Mode:** Headless (arrière-plan)
- **Fiabilité:** >95% des profils

## 🔄 Mise à jour régulière

Pour remettre à jour vos données :

```bash
# 1. Récupérer le script
git clone https://github.com/paularnd875/french-bar-scrapers.git
cd french-bar-scrapers/bayonne-barreau-scraper

# 2. Lancer
./run_bayonne_scraper.sh

# 3. Les nouveaux fichiers sont générés avec timestamp actuel
```

## ⚠️ Prérequis

- Python 3.7+
- ChromeDriver installé
- Connexion internet stable

```bash
pip3 install selenium
```

## 📊 Données extraites

✅ **Garanties:** Nom, prénom, adresse, année inscription  
⚠️ **Variables:** Email, téléphone (protection anti-scraping)  
✅ **Bonus:** Spécialisations juridiques quand disponibles  

---
*Dernière mise à jour: Février 2026*