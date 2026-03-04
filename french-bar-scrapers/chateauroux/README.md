# Scraper du Barreau de Châteauroux

## Description

Script Python utilisant Selenium pour extraire automatiquement les informations des avocats du Barreau de Châteauroux depuis https://www.avocats-chateauroux.fr/annuaire-des-avocats/

## Fonctionnalités

- ✅ **Extraction complète** : Parcourt toutes les lettres de l'alphabet (A-Z)
- ✅ **Données détaillées** : Nom, prénom, structure, adresse, téléphone, email, spécialités, date de serment
- ✅ **Gestion automatique des cookies** : Accepte automatiquement les cookies
- ✅ **Décodage ROT13** : Déchiffre les emails encodés
- ✅ **Déduplication des emails** : Assure l'unicité des adresses email
- ✅ **Navigation par fiches détaillées** : Consulte chaque fiche avocat individuellement
- ✅ **Formats de sortie multiples** : CSV, JSON, liste d'emails, rapport détaillé
- ✅ **Mode test et production** : Permet de tester sur un échantillon avant extraction complète

## Prérequis

```bash
pip install selenium beautifulsoup4 requests
```

Installer Chrome WebDriver :
- Télécharger depuis https://chromedriver.chromium.org/
- Ou utiliser `brew install chromedriver` sur macOS

## Utilisation

### Mode Test (5 avocats)
```bash
python3 chateauroux_scraper.py test
```

### Mode Production (tous les avocats)
```bash
python3 chateauroux_scraper.py
```

## Fichiers générés

Le script génère automatiquement plusieurs fichiers :

1. **`CHATEAUROUX_PRODUCTION_[nb]_avocats_[timestamp].json`** - Données complètes au format JSON
2. **`CHATEAUROUX_PRODUCTION_[nb]_avocats_[timestamp].csv`** - Données tabulaires
3. **`CHATEAUROUX_PRODUCTION_EMAILS_[nb]emails_[timestamp].txt`** - Liste des emails uniques
4. **`CHATEAUROUX_PRODUCTION_RAPPORT_COMPLET_[timestamp].txt`** - Rapport détaillé avec statistiques

## Exemple de sortie

**Statistiques typiques :**
- 59 avocats extraits
- 35 emails uniques (59.3%)
- 96.6% de taux de complétude téléphones
- 100% de taux de complétude adresses
- 64.4% de taux de complétude spécialités

**Données extraites par avocat :**
- Nom et prénom (séparés automatiquement)
- Structure/cabinet
- Adresse complète
- Téléphone et fax
- Email (décodé si nécessaire)
- Date de serment (année extraite)
- Spécialités juridiques
- Site web

## Caractéristiques techniques

- **Navigation intelligente** : Utilise les URLs pour extraire les noms et éviter les parasites DOM
- **Gestion d'erreurs** : Continue l'extraction même en cas d'erreurs ponctuelles
- **Sauvegarde incrémentale** : Sauvegarde partielle en cas d'interruption
- **Nettoyage automatique** : Nettoie et valide les données extraites

## Dernière extraction réussie

**Date** : 2026-03-03  
**Total** : 59 avocats  
**Emails uniques** : 35  
**Statut** : ✅ Extraction complète réussie