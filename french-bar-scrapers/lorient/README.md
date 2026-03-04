# 🏛️ Scraper Barreau de Lorient

## 📊 Résultats

- **Total d'avocats** : 150
- **Emails trouvés** : 149/150 (99.3%)
- **Emails uniques** : 135
- **Téléphones** : 149/150 (99.3%)
- **Spécialisations** : 87/150 (58.0%)
- **Structures/Cabinets** : 59/150 (39.3%)

## 📁 Fichiers

- `lorient_scraper_final_consolidated.py` - Script principal
- `LORIENT_AVOCATS_FINAL_150.csv` - Base de données complète (150 avocats)
- `LORIENT_EMAILS_UNIQUES_FINAL.txt` - 135 emails uniques
- `sample_results.json` - Échantillon des résultats

## 🚀 Utilisation

### Installation des dépendances
```bash
pip install selenium webdriver-manager
```

### Extraction complète (tous les avocats)
```bash
python3 lorient_scraper_final_consolidated.py
```

### Consolidation de fichiers existants
```bash
python3 lorient_scraper_final_consolidated.py --consolidate
```

## ✅ Fonctionnalités

- ✅ **Parsing intelligent des noms** - Gestion des noms composés avec tirets
- ✅ **Extraction précise des spécialisations** - Depuis les balises H3 spécifiques
- ✅ **Détection des structures juridiques** - SELARL, SCP, SARL, etc.
- ✅ **Déduplication automatique** - Par URL et email
- ✅ **Mode batch intelligent** - Traitement par groupes pour éviter les blocages
- ✅ **Réutilisabilité totale** - Script prêt pour actualisation future

## 🎯 Exemples de parsing des noms

| Nom complet | Prénom | Nom |
|-------------|--------|-----|
| SIMPORE-GAULTIER Vanessa | Vanessa | SIMPORE-GAULTIER |
| SOBEAUX-LE GOFF Françoise | Françoise | SOBEAUX-LE GOFF |
| YHUEL - LE GARREC Gaëlle | Gaëlle | YHUEL - LE GARREC |
| ALVAREZ Iannis | Iannis | ALVAREZ |

## 📈 Spécialisations extraites

Exemples de spécialisations correctement formatées :
- "Droit de la santé | Droit des Assurances | Droit du dommage corporel | Droit pénal"
- "Droit immobilier | Droit des contrats | Droit des sociétés"
- "Droit des enfants | Droit des successions | Droit du Crédit"

## 🔄 Réutilisabilité

Ce script est conçu pour être réutilisé dans un an pour actualiser les données :
- Détection automatique des nouveaux avocats
- Mise à jour incrémentale de la base
- Génération d'un nouveau fichier consolidé unique

## 🏛️ Source

Barreau de Lorient : https://www.barreaulorient.fr/avocats-lorient/tous-les-avocats.php

## 📊 Qualité des données

- **Taux de succès exceptionnel** : 99.3% pour emails et téléphones
- **Données vérifiables** : URL source fournie pour chaque avocat
- **Format professionnel** : CSV optimisé pour exploitation directe
- **Nettoyage automatique** : Déduplication et validation des données