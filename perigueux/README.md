# Scraper Barreau de Périgueux

## Vue d'ensemble

Script d'extraction automatisée pour l'annuaire du Barreau de Périgueux. Extrait les données complètes de **91 avocats** avec dates de serment, emails, téléphones et informations de contact.

## Résultats d'extraction

- **✅ 91/91 avocats** extraits (100% de réussite)
- **📧 87 emails uniques** collectés (95.6% de taux de succès)
- **⚖️ 81 dates de serment** récupérées (89.0% de réussite)  
- **📞 27 téléphones** collectés (29.7% de taux de succès)

## Spécificités techniques

### Architecture du site
- **CMS**: Joomla avec Community Builder
- **Navigation**: URLs directes vers profils individuels
- **JavaScript**: Contenu chargé dynamiquement avec cbUserURLs

### Défis techniques résolus

1. **Extraction des dates de serment**
   - Cible spécifique: éléments `<h3>Prestation de serment : YEAR</h3>`
   - Parsing avec regex pour extraire l'année
   - Validation des années entre 1950-2025

2. **Parsing des noms français**
   - Gestion des particules: "de", "du", "des", "de la"
   - Support des noms composés et noms tout en majuscules
   - Logique de fallback avec multiple sources (titre, URL, contenu)

3. **Extraction multi-sources**
   - Titre de page, sélecteurs CSS, contenu textuel
   - URLs décodées comme source de nom de secours
   - Patterns regex pour différents formats de noms

## Structure des données extraites

```json
{
  "prenom": "Delphine",
  "nom": "ALONSO", 
  "email": "cabinet@avocats-lga.fr",
  "telephone": "",
  "annee_serment": "2009",
  "annee_inscription": "",
  "specialisations": "",
  "structure": "",
  "adresse": "",
  "source_url": "https://www.avocats-perigueux.com/component/comprofiler/userprofile/77/dalonso.html"
}
```

## Installation et utilisation

### Prérequis
```bash
pip install selenium webdriver-manager beautifulsoup4 requests pandas
```

### Lancement rapide
```bash
./run_perigueux_scraper.sh
```

### Lancement manuel
```bash
python3 perigueux_scraper_final.py
```

## Fonctionnalités avancées

### Sauvegardes automatiques
- Backup intermédiaire tous les 20 profils
- Protection contre les pertes de données en cas d'interruption

### Gestion des erreurs
- Retry automatique sur les échecs de connexion
- Validation des données extraites
- Logs détaillés pour le debugging

### Formats de sortie multiples
- **CSV**: pour analyse tableur 
- **JSON**: format structuré avec métadonnées
- **TXT**: liste des emails pour mailing

## Structure du site source

**Base URL**: https://www.avocats-perigueux.com

**Pattern des profils**:
```
/component/comprofiler/userprofile/[ID]/[NOM].html
```

**Exemple**:
```
https://www.avocats-perigueux.com/component/comprofiler/userprofile/77/dalonso.html
```

## URLs complètes des 91 avocats

Le script contient la liste exhaustive des 91 URLs de profils, découverte après analyse de la pagination du site avec les paramètres:
- Page 1: `limitstart=0`  
- Page 2: `limitstart=30`
- Page 3: `limitstart=60` 
- Page 4: `limitstart=90`

## Notes importantes

⚠️ **Rate limiting**: Délais de 2 secondes entre chaque profil pour respecter le serveur

⚠️ **Mode headless**: Exécution en arrière-plan pour optimiser les performances

⚠️ **Robustesse**: Gestion des profils indisponibles ou mal formatés

## Maintenance

Le site utilise une structure Joomla stable. Les URLs de profils sont persistantes mais de nouveaux avocats peuvent être ajoutés. 

Pour mettre à jour la liste:
1. Vérifier la pagination sur le site principal
2. Extraire les nouvelles URLs de profils 
3. Ajouter à la liste `PERIGUEUX_LAWYER_URLS`

## Développement

**Développé**: Février 2026  
**Testé sur**: 91 profils d'avocats  
**Validé**: Extraction complète avec données de qualité

## Conformité

Script développé dans le respect des bonnes pratiques de web scraping, avec délais appropriés et sans surcharge du serveur cible.