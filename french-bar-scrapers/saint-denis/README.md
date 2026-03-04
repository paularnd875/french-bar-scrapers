# Scraper Barreau de Saint-Denis (La Réunion)

## Description
Ce scraper extrait automatiquement les informations de tous les avocats inscrits au Barreau de Saint-Denis de La Réunion depuis leur annuaire en ligne.

## Données extraites
- **Prénom et nom** (parsing corrigé pour format "NOM Prénom" du site)
- **Email** (extraction depuis JSON-LD)
- **Téléphone** (extraction depuis JSON-LD)
- **Domaines d'intervention** (spécialisations légales)
- **Année d'inscription** (si disponible)
- **Adresse** (si disponible)
- **URL source** (lien vers le profil)

## Installation

### Prérequis
- Python 3.8+
- Google Chrome installé
- ChromeDriver (téléchargé automatiquement par Selenium)

### Installation des dépendances
```bash
pip install -r requirements.txt
```

## Utilisation

### Extraction complète
```bash
python saint_denis_scraper.py
```

### Utilisation programmatique
```python
from saint_denis_scraper import SaintDenisScraper

scraper = SaintDenisScraper()
# Extraction complète depuis l'annuaire
files = scraper.run_extraction(collect_urls=True)

# Extraction rapide avec URLs de test  
files = scraper.run_extraction(collect_urls=False)
```

## Fichiers générés
Le scraper génère automatiquement :
- `SAINT_DENIS_FINAL_XX_avocats_YYYYMMDD_HHMMSS.csv` - Base de données complète
- `SAINT_DENIS_FINAL_XX_avocats_YYYYMMDD_HHMMSS.json` - Format JSON
- `SAINT_DENIS_EMAILS_YYYYMMDD_HHMMSS.txt` - Liste des emails uniquement
- `SAINT_DENIS_RAPPORT_YYYYMMDD_HHMMSS.txt` - Rapport détaillé avec statistiques

## Fonctionnalités avancées
- **Reconnexion automatique** : Le driver se reconnecte en cas de déconnexion
- **Sauvegardes intermédiaires** : Toutes les 15 extractions pour éviter les pertes
- **Retry automatique** : 3 tentatives par URL en cas d'échec
- **Parsing intelligent** : Gère les noms composés, particules et traits d'union
- **Mode headless** : Fonctionne sans interface graphique

## Structure des données CSV
```
prenom,nom,annee_inscription,domaines_intervention,structure,source_url,adresse,telephone,email,autres_infos
```

## Exemples de données extraites
```csv
Sanaze,MOUSSA-CARPENTIER,2022,"Droit du crédit; Droit des garanties",https://barreau-saint-denis.re/listing/moussa-carpentier-sanaze/,,0692878863,avocat.moussa-carpentier@wanadoo.fr,
Isabelle,SIMON LEBON,2022,"Droit du divorce; Responsabilité civile",https://barreau-saint-denis.re/listing/simon-lebon-isabelle/,,0262456230,isabellesimon.avocat@gmail.com,
```

## Statistiques typiques
- **80+ avocats** extraits
- **90%+ d'emails** récupérés
- **40%+ de domaines d'intervention** disponibles
- **100% de téléphones** (quand disponibles sur le site)

## Notes techniques
- Le site utilise le format "NOM Prénom" qui est automatiquement inversé
- Les emails sont extraits depuis les métadonnées JSON-LD intégrées
- Les domaines d'intervention sont parsés depuis des blocs HTML spécifiques
- Le scraper respecte les délais entre requêtes (2-3 secondes)

## Version
- **Version** : 1.0
- **Date** : 2026-02-19
- **Auteur** : Claude Code
- **Dernière mise à jour** : Extraction avec parsing des noms corrigé et domaines d'intervention

## Support
Pour toute question ou problème, vérifiez que :
1. Chrome est installé et à jour
2. Les dépendances Python sont installées
3. La connexion internet est stable

Le scraper est conçu pour être robuste et se relancer facilement en cas de mise à jour de l'annuaire.