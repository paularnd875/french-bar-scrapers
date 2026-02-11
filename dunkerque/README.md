# Scraper Barreau de Dunkerque

Ce dossier contient les scripts de scraping pour extraire les données des avocats du Barreau de Dunkerque.

## URL du site
https://barreau-dunkerque.fr/search-result/?directory_type=general

## Scripts disponibles

### `dunkerque_scraper_test.py`
- Script de test pour valider le fonctionnement sur quelques avocats (5 par défaut)
- Mode visuel pour debugging
- Utilisation : `python3 dunkerque_scraper_test.py`

### `dunkerque_scraper_production.py`  
- Script de production pour scraper tous les avocats
- Mode headless (aucune fenêtre ne s'ouvre)
- Scraping complet de l'annuaire
- Utilisation : `python3 dunkerque_scraper_production.py`

## Données extraites

✅ **Informations récupérées avec succès :**
- Nom complet, prénom, nom
- Email (95.5% de taux de succès)
- Téléphone (100% de taux de succès)
- Année d'inscription au barreau

⚠️ **Informations partiellement récupérées :**
- Spécialisations/domaines de compétences (en cours d'amélioration)
- Adresse (non disponible sur les fiches)
- Structure/cabinet (non disponible sur les fiches)

## Résultats

Le scraping de production a extrait **66 avocats** sur 79 attendus (83.5% de couverture).

## Formats de sortie

- **CSV** : Données tabulaires pour Excel/Google Sheets
- **JSON** : Données structurées pour traitement programmatique  
- **TXT (emails)** : Liste simple des emails pour mailing
- **TXT (rapport)** : Rapport détaillé avec statistiques

## Spécialisations disponibles

Les domaines de compétences suivants sont disponibles dans l'annuaire :
- Droit de la famille, des personnes et de leur patrimoine
- Droit des étrangers et de la Nationalité
- Droit du dommage corporel
- Droit pénal
- Droit des mineurs
- Droit du travail
- Droit immobilier et de la construction
- Droit fiscal et douanier
- Droit des garanties, des sûretés, et des mesures d'exécution
- Droit de la fonction publique
- Droit commercial, des affaires et de la concurrence
- Droit public
- Droit de la sécurité sociale et de la protection sociale
- Droit des assurances
- Droit des sociétés
- Droit de la santé
- Droit rural
- Droit du crédit et de la consommation
- Droits des associations et droit du sport
- Droit bancaire et boursier

## Prérequis

```bash
pip install selenium beautifulsoup4 requests
```

Chrome/Chromium doit être installé sur le système.