# Scraper Barreau de Montluçon

## Description
Scraper pour extraire les informations des avocats du barreau de Montluçon depuis leur annuaire en ligne.

**Site web :** https://barreaudemontlucon.com/index.php/annuaire-professionnel/wpbdp_category/avocat/

## Informations extraites

### Données disponibles (100% de couverture)
- ✅ **Prénom** - Séparation correcte des noms composés
- ✅ **Nom** - Gestion des noms de famille composés  
- ✅ **Email** - Tous les avocats ont un email
- ✅ **Adresse complète** - Toutes les adresses récupérées
- ✅ **Lien vers fiche détaillée** - Pour vérification

### Données non disponibles sur ce site
- ❌ **Spécialisations** - Non publiées sur les fiches
- ❌ **Année d'inscription** - Non mentionnée
- ❌ **Structure/Cabinet** - Information non disponible
- ❌ **Téléphone** - Non affiché publiquement

## Statistiques
- **Nombre total d'avocats :** 30
- **Emails récupérés :** 30 (100%)
- **Adresses récupérées :** 30 (100%)
- **Durée d'extraction :** ~27 secondes

## Installation et utilisation

### Prérequis
```bash
pip install requests beautifulsoup4 pandas
```

### Utilisation
```bash
python scraper.py
```

Le script génère automatiquement :
- `MONTLUCON_FINAL_30_avocats_[timestamp].csv` - Base de données complète
- `MONTLUCON_FINAL_EMAILS_[timestamp].txt` - Liste des emails uniquement
- `MONTLUCON_FINAL_[timestamp].json` - Données complètes en JSON
- `MONTLUCON_FINAL_RAPPORT_[timestamp].txt` - Rapport d'extraction détaillé

## Structure des données

### Format CSV
```csv
prenom,nom,nom_complet,email,telephone,adresse,annee_inscription,specialites,structure,source
Nathalie,VENTAX,VENTAX Nathalie,nventax@orange.fr,,9 BOULEVARD DE COURTAIS03100,,,,https://...
```

### Exemples d'avocats
- **VENTAX Nathalie** - nventax@orange.fr
- **TRIBALAT LANGENIEUX Anne** - tribalat.avocat@gmail.com  
- **BONNEAU VIGIER Marie Laure** - mebonneau-vigier@orange.fr

## Particularités techniques

### Gestion des noms composés
Le scraper gère correctement la séparation des noms composés :
- `TRIBALAT LANGENIEUX Anne` → Prénom: "Anne", Nom: "TRIBALAT LANGENIEUX"
- `BONNEAU VIGIER Marie Laure` → Prénom: "Marie Laure", Nom: "BONNEAU VIGIER"

### Robustesse
- Gestion d'erreurs avec retry automatique
- Headers HTTP authentiques pour éviter les blocages
- Pauses entre les requêtes pour respecter le serveur
- Mode silencieux sans fenêtres pop-up

## Structure du site
Le site utilise WordPress Business Directory Plugin (WPBDP) avec une structure simple :
- Une seule page contenant tous les avocats
- Sélecteur CSS : `.wpbdp-listing`
- Pas de pagination nécessaire
- Fiches détaillées accessibles mais sans informations supplémentaires

## Dernière mise à jour
**Date :** 16 février 2026  
**Status :** ✅ Fonctionnel - Extraction complète réussie

## Notes
Ce barreau publie uniquement les informations de contact de base. Contrairement à d'autres barreaux, les spécialisations, années d'inscription et structures ne sont pas rendues publiques sur leur site web.