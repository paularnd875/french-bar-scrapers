# 🏛️ BARREAU DE SAUMUR - SCRAPER EXHAUSTIF

## 📋 Description
Script d'extraction exhaustive des données de tous les avocats du barreau de Saumur depuis le PDF officiel.

**Source :** https://www.barreau-saumur.fr/wp-content/uploads/2025/02/avocats-saumur-2025.pdf

## 📊 Résultats
- **28 avocats** extraits au total
  - 26 avocats au tableau principal (1992-2022)
  - 2 avocats en cabinets secondaires
- **Taux d'emails :** 75% global (100% pour le tableau principal)
- **Mode headless :** Aucune interface graphique

## 🚀 Utilisation Rapide

### Prérequis
```bash
pip install PyPDF2 pandas requests
```

### Lancement du script
```bash
python3 SAUMUR_SCRAPER_COMPLET_FINAL.py
```

OU utilisez le script de lancement simplifié :
```bash
python3 run_saumur_scraper.py
```

## 📁 Fichiers générés

Le script génère automatiquement :

1. **`SAUMUR_FINAL_EXHAUSTIF_XX_avocats_YYYYMMDD_HHMMSS.csv`** - Fichier principal (tous les avocats)
2. **`SAUMUR_FINAL_EXHAUSTIF_XX_avocats_YYYYMMDD_HHMMSS.json`** - Format JSON
3. **`SAUMUR_FINAL_EXHAUSTIF_AVEC_EMAILS_XX_YYYYMMDD_HHMMSS.csv`** - Seulement les avocats avec email
4. **`SAUMUR_FINAL_EXHAUSTIF_EMAILS_UNIQUES_XX_YYYYMMDD_HHMMSS.txt`** - Liste des emails uniques
5. **`SAUMUR_FINAL_EXHAUSTIF_RAPPORT_FINAL_YYYYMMDD_HHMMSS.txt`** - Rapport détaillé

## 📋 Données extraites par avocat

| Colonne | Description | Exemple |
|---------|-------------|---------|
| `annee_inscription` | Année d'inscription au barreau | 1992 |
| `nom` | Nom de famille (majuscules) | COUVREUX |
| `prenom` | Prénom (gestion des prénoms composés) | Christine |
| `nom_complet` | Nom complet | COUVREUX Christine |
| `email` | Adresse email | aca.saumur@aca-avocats.fr |
| `telephone` | Numéro de téléphone | 0241502100 |
| `adresse` | Adresse complète | 16 avenue David d'Angers - 49400 SAUMUR |
| `specialisations` | Domaines de spécialisation | Droit de la famille, des personnes... |
| `structure` | Cabinet/Structure d'appartenance | SCP A.C.A. COUVREUX-EON-GRATON |
| `titre` | Titre spécial | Ancien Bâtonnier |
| `source_pdf` | URL source pour vérification | https://www.barreau-saumur.fr/... |

## 🔧 Fonctionnalités

- ✅ **Extraction PDF directe** (plus fiable que le web scraping)
- ✅ **Gestion prénoms composés** (ex: "Marie, Ornella" → "Marie Ornella")
- ✅ **Distinction nom/prénom** en colonnes séparées
- ✅ **Mode headless** (aucune fenêtre)
- ✅ **Validation automatique** des données
- ✅ **Rapports détaillés** avec statistiques
- ✅ **Formats multiples** (CSV, JSON, TXT)

## 📈 Exemple de sortie

```csv
annee_inscription,nom,prenom,nom_complet,email,telephone,adresse,specialisations,structure,titre,source_pdf
1992,COUVREUX,Christine,COUVREUX Christine,aca.saumur@aca-avocats.fr,0241502100,16 avenue David d'Angers - 49400 SAUMUR,"Droit de la famille, des personnes et de leur patrimoine",SCP A.C.A. COUVREUX-EON-GRATON,Ancien Bâtonnier,https://www.barreau-saumur.fr/wp-content/uploads/2025/02/avocats-saumur-2025.pdf
1993,MALIVERT,Jean-Pierre,MALIVERT Jean-Pierre,malivertjeanpierre@bbox.fr,0241598862,36 bis rue Dacier - 49400 SAUMUR,,,,https://www.barreau-saumur.fr/wp-content/uploads/2025/02/avocats-saumur-2025.pdf
```

## ⚙️ Configuration

Le script fonctionne directement sans configuration. Il :
1. Télécharge automatiquement le PDF depuis le site officiel
2. Extrait toutes les données
3. Valide la qualité des informations
4. Génère les fichiers de sortie avec timestamp

## 🔄 Mise à jour

Pour mettre à jour les données :
1. Relancez simplement le script
2. Les nouveaux fichiers seront générés avec un timestamp actualisé
3. Consultez le rapport pour voir les changements

## ✅ Validation

Le script inclut une validation automatique :
- Vérification de la complétude des données
- Validation des formats email
- Contrôle de cohérence des téléphones
- Rapport d'erreurs/avertissements

## 🆘 Support

En cas de problème :
1. Vérifiez que les dépendances sont installées
2. Consultez le rapport généré pour les détails
3. Vérifiez la connectivité internet (téléchargement PDF)

---
*Dernière mise à jour : Mars 2026*