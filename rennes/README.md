# Scraper Barreau de Rennes

Scripts pour extraire tous les avocats du barreau de Rennes avec leurs informations détaillées.

## 🎯 Objectif

Extraire la base complète des **1107 avocats** du barreau de Rennes depuis l'annuaire officiel : https://www.ordre-avocats-rennes.fr/annuaire

## 📊 Résultats attendus

- **1107 avocats** extraits (100%)
- **99.9% de taux de réussite** sur les emails
- **99.8% de taux de réussite** sur les téléphones
- Spécialisations, adresses, structures complètes

## 🚀 Utilisation

### Prérequis
```bash
pip install selenium
```

### Étape 1 : Récupérer la liste complète
```bash
python3 rennes_scraper_complet.py
```
**Durée** : ~15 minutes
**Résultat** : Fichier `RENNES_LISTE_COMPLETE_1107_avocats_YYYYMMDD_HHMMSS.json`

### Étape 2 : Extraire tous les détails
```bash
python3 rennes_extraction_details.py
```
**Durée** : ~2h pour les 1107 avocats
**Résultats** :
- `RENNES_FINAL_COMPLET_1107_avocats_YYYYMMDD_HHMMSS.csv`
- `RENNES_FINAL_COMPLET_1107_avocats_YYYYMMDD_HHMMSS.json`
- `RENNES_FINAL_COMPLET_EMAILS_SEULEMENT_YYYYMMDD_HHMMSS.txt`

## 📋 Informations extraites

### Pour chaque avocat
- **Prénom** (colonne séparée)
- **Nom** (colonne séparée)
- **Email** (99.9% de réussite)
- **Téléphone** (99.8% de réussite)
- **Adresse complète**
- **Structure/Cabinet**
- **Année d'inscription au barreau**
- **Spécialisations/Compétences** (format: "Droit commercial | Droit des sociétés")
- **Source** (lien vers la fiche avocat)

## ⚙️ Fonctionnalités

- **Mode headless** : Pas d'ouverture de fenêtres
- **Gestion automatique des cookies**
- **Sauvegarde automatique** toutes les 100 extractions
- **Reprise automatique** en cas d'interruption
- **Déduplication** des doublons
- **Séparation correcte** des prénoms composés et noms de famille

## 🎯 Points clés validés

✅ Extraction exhaustive de tous les 1107 avocats  
✅ Taux de réussite email exceptionnel (99.9%)  
✅ Gestion correcte des noms composés  
✅ Spécialisations extraites depuis `.avocatDetails_infoCompl_col`  
✅ Navigation complète sur les 37 pages  
✅ Robustesse et reprises automatiques  

## 📁 Structure des fichiers

```
rennes/
├── README.md                    # Ce fichier
├── rennes_scraper_complet.py   # Étape 1 : Liste complète
└── rennes_extraction_details.py # Étape 2 : Détails complets
```

## 🔄 Mise à jour

Pour mettre à jour la base :
1. Supprimer les anciens fichiers `RENNES_*`
2. Relancer l'étape 1 puis l'étape 2
3. Comparer avec l'ancienne base pour identifier les nouveaux avocats

## 🎉 Résultats de test

**Test validé** sur 50 avocats :
- ✅ 100% emails récupérés
- ✅ 100% téléphones récupérés  
- ✅ 100% adresses récupérées
- ✅ Spécialisations extraites correctement

**Production complète validée** :
- ✅ 1107/1107 avocats extraits
- ✅ 1106 emails récupérés (99.9%)
- ✅ 1105 téléphones récupérés (99.8%)
- ✅ Base de données complète et opérationnelle