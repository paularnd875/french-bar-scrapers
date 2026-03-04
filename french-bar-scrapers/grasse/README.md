# Scraper Barreau de Grasse

## 🎯 Description
Scraper pour extraire la liste complète des avocats du barreau de Grasse depuis leur annuaire officiel.

**Site source :** https://www.avocats-grasse.com/fr/annuaire-avocats/

## 📊 Données extraites
- **Nom et prénom** de l'avocat
- **Email professionnel** 
- **Numéro de téléphone**
- **Adresse complète** (rue, ville, code postal)
- **Spécialisations juridiques**
- **Structure/Cabinet** (quand disponible)
- **Année d'inscription** (quand mentionnée)

## 🚀 Utilisation

### Installation des dépendances
```bash
pip install selenium webdriver-manager
```

### Lancement du scraper
```bash
python grasse_scraper_production.py
```

## ⚙️ Fonctionnalités

- **Mode headless** : Aucune fenêtre de navigateur n'apparaît
- **Navigation automatique** : Traite les 14 pages de l'annuaire
- **Gestion des cookies** : Acceptation automatique si nécessaire
- **Sauvegardes multiples** : JSON, CSV, TXT (emails), rapport détaillé
- **Sauvegardes intermédiaires** : Tous les 5 pages pour éviter les pertes
- **Robustesse** : Gestion des erreurs et timeouts

## 📁 Fichiers générés

Après exécution, le scraper génère automatiquement :

1. **JSON** : `GRASSE_PRODUCTION_FINALE_XXX_avocats_TIMESTAMP.json`
   - Données structurées complètes
   
2. **CSV** : `GRASSE_PRODUCTION_FINALE_XXX_avocats_TIMESTAMP.csv`
   - Format tableur (Excel, Google Sheets)
   
3. **TXT** : `GRASSE_PRODUCTION_FINALE_EMAILS_SEULEMENT_TIMESTAMP.txt`
   - Liste pure d'emails pour mailing
   
4. **Rapport** : `GRASSE_PRODUCTION_FINALE_RAPPORT_COMPLET_TIMESTAMP.txt`
   - Statistiques détaillées et analyses

## 📈 Statistiques de performance

- **280 avocats** extraits au total (dernière exécution)
- **96.8%** de taux de récupération d'emails (271/280)
- **2.1 minutes** de traitement pour l'annuaire complet
- **63 villes** représentées dans la région

### Répartition géographique principale :
- **Cannes** : 91 avocats (32.5%)
- **Antibes** : 33 avocats (11.8%)
- **Grasse** : 31 avocats (11.1%)
- **Cagnes-sur-Mer** : 14 avocats (5.0%)

### Spécialisations les plus représentées :
- Droit Commercial (10.4%)
- Droit du Travail (8.6%)
- Droit de la Famille (6.8%)
- Droit des Sociétés (5.0%)

## 🛠️ Structure technique

### Approche d'extraction :
1. **Selenium WebDriver** avec Chrome en mode headless
2. **Parsing HTML** avec sélecteurs CSS optimisés
3. **Regex** pour extraction précise des données spécifiques
4. **Validation** des données avant sauvegarde

### Gestion des éléments :
- **Articles** : Conteneurs principaux des fiches avocats
- **Google Maps** : Extraction d'adresses depuis les liens cartographiques
- **Domaines d'activités** : Parsing des spécialisations juridiques
- **Pagination** : Navigation automatique entre les 14 pages

## ⚠️ Notes techniques

- Nécessite **Chrome/Chromium** installé sur le système
- Temps d'exécution : ~2-3 minutes pour l'annuaire complet
- Mode headless par défaut (pas d'interface graphique)
- Gestion automatique des timeouts et erreurs réseau

## 📝 Changelog

### Version 1.0 (12/02/2026)
- ✅ Extraction complète de l'annuaire (280 avocats)
- ✅ Mode headless stabilisé
- ✅ Parsing amélioré des spécialisations
- ✅ Génération de rapports détaillés
- ✅ Sauvegardes multiples formats

## 🔧 Développement

Le scraper a été développé et testé avec :
- Python 3.8+
- Selenium 4.x
- Chrome WebDriver automatique
- macOS (compatible Linux/Windows)

Pour des modifications, consulter le code source avec commentaires détaillés.