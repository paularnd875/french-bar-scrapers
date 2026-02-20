# Scraper Barreau de Valenciennes

Ce scraper extrait l'annuaire complet des avocats du barreau de Valenciennes.

## Site source
- **URL** : https://www.avocats-valenciennes.fr/annuaire-avocats-du-barreau.htm
- **Nombre d'avocats** : 115
- **Dernière extraction** : 2026-02-20

## Fonctionnalités

✅ **Extraction complète** : 115 avocats  
✅ **Mode headless** : Pas de fenêtres qui s'ouvrent  
✅ **Gestion automatique des cookies** : Pas de bannière bloquante  
✅ **Décodage d'emails** : Emails encodés décodés automatiquement  
✅ **Séparation nom/prénom** : Extraction correcte des noms composés  

## Informations extraites

- **Prénom** et **Nom** (correctement séparés)
- **Email** (décodé automatiquement)
- **Téléphone** (format normalisé)
- **Fax** (si disponible)
- **Adresse complète** avec code postal et ville
- **Année de serment** 
- **Spécialisations/Domaines d'activité**
- **Cabinet/Structure** (si disponible)
- **Site web** (si disponible)
- **URL source** pour vérification

## Installation des dépendances

```bash
pip install selenium beautifulsoup4 requests
```

## Utilisation

### Test avec 20 avocats
```bash
python3 scraper.py test
```

### Extraction complète (115 avocats)
```bash
python3 scraper.py
```

## Fichiers générés

Le scraper génère 4 fichiers :

1. **JSON** : `VALENCIENNES_COMPLET_115_avocats_YYYYMMDD_HHMMSS.json`
2. **CSV** : `VALENCIENNES_COMPLET_115_avocats_YYYYMMDD_HHMMSS.csv` (format Excel, UTF-8 BOM, séparateur `;`)
3. **Emails** : `VALENCIENNES_EMAILS_UNIQUES_YYYYMMDD_HHMMSS.txt` (liste des emails uniques)
4. **Rapport** : `VALENCIENNES_RAPPORT_COMPLET_YYYYMMDD_HHMMSS.txt` (statistiques et détails)

## Résultats attendus

- **115 avocats** extraits
- **100% de réussite** pour emails, téléphones, adresses, années de serment
- **~113 emails uniques** (certains avocats partagent des emails)
- **Temps d'exécution** : ~5-7 minutes pour l'extraction complète

## Structure CSV

```
nom;prenom;nom_complet;email;telephone;fax;adresse;code_postal;ville;annee_serment;specialites;cabinet;site_web;langues;url_fiche;slug
GUILLEMINOT;Jerome;Jerome Guilleminot;jguilleminot.avocat@orange.fr;03 27 42 71 44;03 27 28 07 99;...
```

## Spécificités techniques

- **Chrome WebDriver** requis
- **Mode headless** par défaut
- **Retry automatique** sur les erreurs
- **Pause entre requêtes** (0.5s) pour respecter le serveur
- **Extraction depuis URLs** pour fiabilité des noms
- **Validation des données** (années, emails, téléphones)

## Notes importantes

- Le site n'a pas de pagination - tous les avocats sont sur une page
- Pas de gestion de cookies bloquante
- Les noms sont extraits depuis les URLs pour plus de fiabilité
- Les emails sont souvent encodés en HTML entities et sont automatiquement décodés