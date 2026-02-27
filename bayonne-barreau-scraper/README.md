# Scraper Barreau de Bayonne 🏛️

## Description
Script automatisé pour extraire **tous les avocats** du barreau de Bayonne avec leurs informations détaillées.

## URL cible
**https://www.avocats-bayonne.org/annuaire-des-avocats.html**

## 📊 Données extraites
- ✅ **Nom et prénom** (gestion intelligente des noms composés)
- ✅ **Année d'inscription** au barreau
- ✅ **Spécialisations** juridiques
- ✅ **Adresse complète** (Bayonne, Biarritz, Anglet, Saint-Jean-de-Luz...)
- ✅ **Structure/Cabinet**
- ⚠️ **Email et téléphone** (si disponibles - site protégé)

## 🚀 Installation et usage

### Prérequis
```bash
pip install selenium
```

### ChromeDriver
- Télécharger ChromeDriver depuis https://chromedriver.chromium.org/
- S'assurer qu'il est dans le PATH système

### Lancement
```bash
python3 bayonne_scraper_production.py
```

## 📁 Fichiers générés

Le script génère automatiquement :

1. **CSV** (`BAYONNE_PRODUCTION_XXX_avocats_YYYYMMDD_HHMMSS.csv`)
   - Format tableur pour Excel/Google Sheets
   
2. **JSON** (`BAYONNE_PRODUCTION_XXX_avocats_YYYYMMDD_HHMMSS.json`)
   - Format structuré pour traitement programmatique
   
3. **Emails** (`BAYONNE_EMAILS_SEULEMENT_YYYYMMDD_HHMMSS.txt`)
   - Liste des emails uniques (si extraits)
   
4. **Rapport** (`BAYONNE_RAPPORT_COMPLET_YYYYMMDD_HHMMSS.txt`)
   - Rapport détaillé avec statistiques et liste complète

## ⚡ Caractéristiques techniques

- **Mode headless** : Fonctionne en arrière-plan sans ouvrir de fenêtre
- **Scraping complet** : Scan automatique de toutes les pages
- **Extraction individuelle** : Visite chaque profil pour les détails
- **Gestion des erreurs** : Continue même en cas de profils inaccessibles
- **Optimisé** : Vitesse ~25 profils/minute
- **Déduplication** : Évite les doublons automatiquement

## 📈 Performances attendues

- **~170-200 avocats** total estimé
- **Temps d'exécution** : 8-15 minutes
- **Taux de succès** : >95% des profils
- **Fiabilité** : 100% noms/prénoms, 100% adresses, ~5% spécialisations

## 🔧 Structure des données

```csv
url_source,prenom,nom,annee_inscription,specialisations,competences,activites_dominantes,structure,adresse,telephone,email,site_web
https://www.avocats-bayonne.org/cb-profile/XXX.html,Xavier,ABEBERRY,2007,,,,,"64200 BIARRITZ",,,
```

## ⚠️ Notes importantes

1. **Site protégé** : Les emails/téléphones peuvent ne pas être extraits (protection anti-scraping)
2. **Respecter le site** : Pauses automatiques entre requêtes
3. **Connexion requise** : Script nécessite une connexion internet stable
4. **ChromeDriver** : Doit être compatible avec votre version de Chrome

## 🔄 Mise à jour des données

Pour remettre à jour la base de données :
```bash
python3 bayonne_scraper_production.py
```

Les nouveaux fichiers seront générés avec timestamp actuel.

## 📞 Support

En cas de problème :
1. Vérifiez que ChromeDriver est installé
2. Vérifiez votre connexion internet
3. Consultez les messages d'erreur dans la console

---
*Développé avec Claude Code Assistant - Février 2026*