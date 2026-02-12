# Scraper - Barreau de Laval

## Description
Scraper pour extraire les informations de tous les avocats du Barreau de Laval depuis leur annuaire professionnel en ligne.

**Site source :** https://barreau-de-laval.com/annuaire-professionnel/

## Fonctionnalités

✅ **Extraction complète** - 69 avocats  
✅ **Mode headless** - Pas d'ouverture de fenêtres  
✅ **Gestion automatique des cookies**  
✅ **Séparation correcte prénom/nom**  
✅ **Taux de réussite : 100%**  

## Données extraites

Pour chaque avocat :
- **Prénom** (colonne séparée)
- **Nom** (colonne séparée) 
- **Nom complet**
- **Email** (100% de couverture)
- **Téléphone** (100% de couverture)
- **Adresse complète**
- **Spécialisations** (71% de couverture)
- **Site web du profil**
- **Année d'inscription** (si disponible)

## Installation

```bash
pip install selenium webdriver-manager
```

## Utilisation

```bash
python3 laval_scraper.py
```

## Structure des fichiers générés

Le script génère automatiquement 4 fichiers :

1. **CSV complet** : `LAVAL_COMPLET_[nb]_avocats_[timestamp].csv`
2. **JSON complet** : `LAVAL_COMPLET_[nb]_avocats_[timestamp].json`  
3. **Rapport détaillé** : `LAVAL_RAPPORT_COMPLET_[timestamp].txt`
4. **Emails uniquement** : `LAVAL_EMAILS_SEULEMENT_[timestamp].txt`

## Exemple de résultats

```csv
index,prenom,nom,nom_complet,email,telephone,adresse,specialisations
1,Valérie,Breger,Valérie Breger,v.breger@acmavocats.fr,02.43.67.95.30,ZI Sud – Rue des martinières 53960 BONCHAMP LES LAVAL,
2,Emmanuel-François,Doreau,Emmanuel-François Doreau,emmanuel.doreau@elcyavocats.fr,02.43.53.06.41,25 rue du Douanier Rousseau 53000 LAVAL,"Droit du dommage corporel, Droit du travail et droit social, Droit pénal"
```

## Statistiques d'extraction

- **69 avocats** détectés et extraits
- **69 emails** récupérés (100%)
- **69 téléphones** récupérés (100%)
- **49 spécialisations** renseignées (71%)
- **Aucun système de pagination** nécessaire (page unique)

## Particularités techniques

- **Prénoms composés** gérés correctement (ex: Emmanuel-François)
- **Extraction robuste** avec sélecteurs CSS optimisés
- **Gestion d'erreurs** complète
- **Mode headless** pour utilisation en production
- **Cookies Axeptio** gérés automatiquement

## Notes

- Le site du Barreau de Laval affiche tous les avocats sur une seule page
- Aucune pagination à gérer
- Structure HTML stable basée sur WordPress Business Directory Plugin
- Temps d'exécution : ~1-2 minutes