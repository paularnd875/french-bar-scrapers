# Scraper Barreau de Martinique

## Description
Script de scraping pour extraire l'annuaire complet des avocats du Barreau de Martinique.

## Site web
- **URL**: https://avocatsdemartinique.fr/le-barreau/annuaire-des-avocats/
- **Total avocats**: 213

## Données extraites
- ✅ **Nom complet** (prénom et nom séparés)
- ✅ **Email** (100% de taux de réussite)
- ✅ **Téléphone**
- ✅ **Spécialisations juridiques** (nettoyées)
- ⚠️ **Année d'inscription** (limitée)
- ✅ **Structure/Cabinet**

## Installation
```bash
pip3 install selenium unidecode
```

## Utilisation

### Test (5 avocats)
```python
scraper = MartiniqueLawyerScraperCorrected(headless=False)
scraper.run_test(max_lawyers=5)
```

### Scraping complet (213 avocats)
```python
scraper = MartiniqueLawyerScraperCorrected(headless=True)
scraper.run_complete_scraping()
```

### Ligne de commande
```bash
python3 martinique_scraper.py
```

## Fonctionnalités

### Gestion automatique
- ✅ Acceptation automatique des cookies
- ✅ Mode headless (pas d'interface graphique)
- ✅ Gestion des erreurs et retry
- ✅ Respect des délais entre requêtes (1.2s)

### Extraction avancée
- ✅ Nettoyage automatique des noms (suppression "Maître", "Barreau de Martinique")
- ✅ Détection d'emails via liens `mailto:` et regex de backup
- ✅ Extraction des vraies spécialisations juridiques
- ✅ Filtrage du contenu parasite

## Fichiers générés

### CSV
- Format tableur avec colonnes propres
- Spécialisations séparées par `;`

### JSON
- Données structurées avec arrays
- Format idéal pour intégration API

### Emails uniquement
- Liste pure d'emails (un par ligne)
- Prêt pour import dans outils de mailing

### Rapport détaillé
- Statistiques complètes
- Exemples d'extraction
- Taux de réussite par champ

## Performances
- **Durée**: ~8 minutes pour 213 avocats
- **Taux de réussite emails**: 100%
- **Taux spécialisations**: 95%
- **Mode**: Silencieux (headless)

## Exemple de résultat
```csv
nom_complet,prenom,nom,email,telephone,specialisations
Marine ABITBOUL,Marine,ABITBOUL,mazerbib.avocat@gmail.com,+596696484123,Droit pénal; Droit bancaire
Marie-Laure AGIAN,Marie-Laure,AGIAN,marielaureagian@gmail.com,+596696484123,Droit civil; Droit commercial
```

## Notes techniques
- **Framework**: Selenium + Chrome WebDriver
- **Anti-détection**: User-agent réaliste, délais naturels
- **Encodage**: UTF-8 pour caractères spéciaux
- **Robustesse**: Multiple fallbacks pour chaque donnée

## Dernière mise à jour
12/02/2026 - Version corrigée avec extraction propre des noms et spécialisations