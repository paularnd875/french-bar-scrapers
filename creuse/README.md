# Scraper Barreau de Creuse

## Description

Scraper pour l'annuaire des avocats du Conseil Départemental de l'Accès au Droit (CDAD) de la Creuse.

**URL cible:** https://cdad-creuse.justice.fr/annuaire-des-professionnels#avocats

## Caractéristiques

- ✅ **20 avocats** extraits (totalité du barreau)
- ✅ **Mode headless** (pas d'interface graphique)
- ✅ **Méthode rapide** : Requests + BeautifulSoup
- ✅ **Données complètes** : emails, téléphones, adresses
- ✅ **Identification** du Bâtonnier
- ✅ **Filtrage automatique** (avocats uniquement, pas notaires/commissaires)

## Structure des données extraites

Chaque avocat contient :
- `nom_complet` : Nom complet avec titre
- `prenom` : Prénom
- `nom` : Nom de famille
- `email` : Adresse email
- `telephone` : Numéro de téléphone (formaté français)
- `adresse` : Adresse complète du cabinet
- `titre` : Titre spécial (Bâtonnier)
- `structure` : Information sur le cabinet

## Installation

```bash
pip install requests beautifulsoup4
```

## Utilisation

```bash
python scraper_creuse.py
```

## Résultats

Le script génère automatiquement 4 fichiers :

1. **`creuse_avocats_YYYYMMDD_HHMMSS.csv`** - Données tabulaires
2. **`creuse_avocats_YYYYMMDD_HHMMSS.json`** - Données JSON
3. **`creuse_emails_YYYYMMDD_HHMMSS.txt`** - Liste des emails uniquement
4. **`creuse_rapport_YYYYMMDD_HHMMSS.txt`** - Rapport détaillé avec statistiques

## Statistiques d'extraction

- **Total avocats :** 20
- **Taux de réussite :** 100%
- **Emails récupérés :** 18 uniques (2 doublons détectés)
- **Téléphones :** 20 (100%)
- **Adresses :** 20 (100%)

### Répartition des domaines email

- gmail.com : 2 avocats
- hadesavocats.com : 2 avocats  
- avocat-laurent.fr : 2 avocats
- orange.fr : 2 avocats
- Autres domaines professionnels : 12 avocats

## Structure technique

**Méthode d'extraction :**
- HTML statique parsé avec BeautifulSoup
- Données dans les attributs `data-bs-content` des boutons Bootstrap
- Regex pour extraire emails, téléphones et adresses

**Particularités du site :**
- Popovers Bootstrap pour les informations de contact
- Différenciation visuelle : avocats (btn-primary) vs notaires (btn-info)
- Pas de pagination (tous sur une seule page)
- Pas de cookies à accepter

## Robustesse

✅ Gestion des erreurs  
✅ Timeout de connexion  
✅ Validation des données  
✅ Dédoublonnage des emails  
✅ Formatage des numéros français  
✅ Détection automatique du Bâtonnier

## Auteur

French Bar Scrapers - 2026