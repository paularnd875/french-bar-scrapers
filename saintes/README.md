# Scraper Barreau de Saintes

Scraper complet pour extraire tous les avocats de l'annuaire du Barreau de Saintes.

## Site cible

- **URL**: https://www.avocats-saintes.com/annuaire-des-avocats.html
- **Type**: Annuaire avec pagination (22 avocats par page)
- **Nombre total d'avocats**: ~93

## Fonctionnalités

✅ **Extraction complète**: Tous les avocats de l'annuaire  
✅ **Pagination automatique**: Navigation sur toutes les pages  
✅ **Détails complets**: Nom, prénom, spécialisations, structure, emails  
✅ **Gestion des cookies**: Acceptation automatique  
✅ **Mode headless**: Exécution en arrière-plan  
✅ **Nettoyage des données**: Suppression des emails génériques  
✅ **Formats multiples**: CSV, JSON, TXT  
✅ **Sauvegarde automatique**: Backups intermédiaires  

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

### 1. Scraping complet

```bash
python saintes_scraper.py
```

Ce script va :
- Extraire tous les ~93 avocats
- Naviguer automatiquement sur les 5 pages
- Extraire les détails de chaque avocat
- Sauvegarder les résultats en CSV/JSON

### 2. Nettoyage des emails génériques

Après le scraping initial, nettoyer les emails dupliqués :

```bash
python clean_generic_emails.py SAINTES_COMPLET_93_avocats_YYYYMMDD_HHMMSS.csv
```

Ou avec un seuil personnalisé :

```bash
python clean_generic_emails.py fichier.csv --threshold 30
```

## Données extraites

Pour chaque avocat :

| Champ | Description | Exemple |
|-------|-------------|---------|
| `nom_complet` | Nom complet | "ROSIER Jean-Paul" |
| `prenom` | Prénom séparé | "Jean-Paul" |
| `nom` | Nom de famille | "ROSIER" |
| `url` | URL de la fiche | "https://www.avocats-saintes.com/avocat/..." |
| `specialisations` | Domaines d'expertise | "Droit commercial; Droit social" |
| `structure` | Cabinet/Structure | "Cabinet ROSIER & ASSOCIES" |
| `date_inscription` | Date inscription au barreau | "01/01/2000" |
| `emails` | Adresses email | "contact@cabinet.fr" |

## Fichiers générés

### Scraping principal
- `SAINTES_COMPLET_XX_avocats_YYYYMMDD_HHMMSS.csv` - Données complètes CSV
- `SAINTES_COMPLET_XX_avocats_YYYYMMDD_HHMMSS.json` - Données complètes JSON
- `SAINTES_COMPLET_EMAILS_XXuniques_YYYYMMDD_HHMMSS.txt` - Liste emails
- `SAINTES_COMPLET_RAPPORT_YYYYMMDD_HHMMSS.txt` - Rapport détaillé

### Nettoyage emails
- `*_CLEAN_YYYYMMDD_HHMMSS.csv` - Fichier principal nettoyé
- `*_AVEC_EMAILS_SPECIFIQUES_XXavocats_YYYYMMDD_HHMMSS.csv` - Avocats avec emails uniquement
- `*_EMAILS_SPECIFIQUES_XXemails_YYYYMMDD_HHMMSS.txt` - Emails spécifiques seulement
- `*_RAPPORT_NETTOYAGE_YYYYMMDD_HHMMSS.txt` - Rapport de nettoyage

## Résultats attendus

D'après les derniers tests :
- **93 avocats** extraits au total
- **4 emails spécifiques** après nettoyage :
  - `larochelle@actejuris.fr`
  - `rgermain@galilee-avocats.fr`
  - `royan@actejuris.fr`
  - `royan@e-litis.com`

## Configuration

### Mode headless
Par défaut, le scraper s'exécute en mode headless (arrière-plan).  
Pour voir le navigateur, modifier dans `saintes_scraper.py` :

```python
scraper = SaintesLawyerScraper(headless=False)
```

### Délais et politesse
Les délais sont configurés pour respecter le site :
- 2 secondes entre les pages
- 1 seconde entre les avocats
- 2 secondes pour charger une fiche

## Gestion des erreurs

Le scraper inclut :
- ✅ Gestion des timeouts
- ✅ Sauvegarde automatique en cas d'interruption
- ✅ Logs détaillés des opérations
- ✅ Continuation automatique après erreurs ponctuelles

## Emails génériques détectés

Le script de nettoyage supprime automatiquement :
- `biblibarreau@orange.fr` (présent sur toutes les fiches)

## Mise à jour des données

Pour remettre à jour votre base :

1. Exécuter le scraper principal :
```bash
python saintes_scraper.py
```

2. Nettoyer les emails génériques :
```bash
python clean_generic_emails.py SAINTES_COMPLET_*_avocats_*.csv
```

3. Utiliser le fichier `*_CLEAN_*.csv` comme version finale

## Support

En cas de problème :
1. Vérifier que Chrome/Chromium est installé
2. Vérifier la connexion internet
3. Vérifier que le site est accessible
4. Consulter les logs pour identifier l'erreur

## Structure technique

```
saintes/
├── saintes_scraper.py          # Scraper principal
├── clean_generic_emails.py     # Nettoyage emails
├── requirements.txt            # Dépendances
└── README.md                   # Cette documentation
```