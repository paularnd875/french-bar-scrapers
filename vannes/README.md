# Scraper Barreau de Vannes

## Description

Scraper officiel pour l'extraction complète des avocats du Barreau de Vannes avec spécialisations juridiques et langues parlées correctement séparées.

## Caractéristiques

- **152 avocats** extraits sur 19 pages
- **Spécialisations juridiques** individuelles correctement détectées (15 avocats avec spécialisations)  
- **Langues parlées** séparées des spécialisations (13 avocats avec langues)
- **Sauvegarde automatique** tous les 25 avocats pour sécurité
- **Gestion robuste** des erreurs et timeouts
- **Pagination inversée** optimisée (pages 19→1)

## Données extraites

### Informations de base
- Nom complet, prénom, nom de famille
- Année d'inscription au barreau
- Structure juridique (Cabinet, SELARL, SCP, etc.)
- Adresse complète
- Téléphone et email
- Site web (si disponible)

### Spécialisations juridiques détectées
- Droit immobilier
- Droit du travail  
- Droit de la famille
- Droit des sociétés
- Droit pénal
- Droit de l'environnement
- Droit public
- Et autres domaines

### Langues parlées
- Anglais, Italien, Espagnol, Allemand
- Séparées des spécialisations juridiques

## Installation

```bash
# Installer les dépendances
pip install selenium

# Installer ChromeDriver (macOS avec Homebrew)
brew install chromedriver

# Ou télécharger depuis https://chromedriver.chromium.org/
```

## Utilisation

```bash
# Lancer l'extraction complète
python3 vannes_scraper_final.py
```

## Fichiers générés

### Fichiers de données
- `VANNES_FINAL_SPECIALISATIONS_CORRECTES_152_avocats_[timestamp].csv`
- `VANNES_FINAL_SPECIALISATIONS_CORRECTES_152_avocats_[timestamp].json`

### Rapports
- `VANNES_RAPPORT_SPECIALISATIONS_FINAL_[timestamp].txt`

### Sauvegardes automatiques
- `VANNES_BACKUP_25_avocats_[timestamp].csv`  
- `VANNES_BACKUP_50_avocats_[timestamp].csv`
- etc. (tous les 25 avocats)

## Structure des données CSV

```csv
nom_complet,prenom,nom,annee_inscription,specialisations,langues_parlees,structure,adresse,telephone,email,site_web,source
MAUGENDRE Clara,Clara,MAUGENDRE,2025,,,SELARL MAIRE - TANGUY...,56000 VANNES,02.97.68.21.21,contact@claramaugendre-avocat.fr,,https://...
MAIRE Christian,Christian,MAIRE,1989,Droit immobilier,,SELARL MAIRE - TANGUY...,56006 VANNES,02.97.68.21.21,c.maire@alter-a.com,www.alter-a.com,https://...
```

## Statistiques de la dernière extraction

```
Total avocats: 152
- Avec spécialisations: 15 (9.9%)
- Sans spécialisations: 137 (90.1%)  
- Avec langues: 13 (8.6%)
- Sans langues: 139 (91.4%)
```

## Spécialisations trouvées (exemples)

- **PEIGNARD Antoine**: Droit immobilier
- **VEILLARD Anne-Cécile**: Droit du Travail
- **DUBREUIL Thomas**: Droit de l'environnement
- **STEPHAN Gwenaëlle**: Droit des sociétés
- **MAIRE Christian**: Droit immobilier
- **MATEL Pierre-Yves**: Droit immobilier | Droit public
- **LE RESTE David**: Droit pénal
- **LARCHE Stéphanie**: Droit du Travail
- **LAROZE-LE PORTZ Isabelle**: Droit de la famille, des personnes et de leur patrimoine
- **GOURDIN Loïc**: Droit du Travail | Droit public

## Correction technique importante

### Problème initial
Le scraper récupérait les spécialisations génériques du formulaire de recherche (lignes 16-34) au lieu des spécialisations individuelles.

### Solution appliquée
1. **Ignore les lignes 16-34** (formulaire de recherche générique)
2. **Cherche APRÈS ligne 60** pour les informations individuelles de l'avocat
3. **Détecte "Specialisation de l'avocat"** pour les vraies spécialisations
4. **Sépare complètement** les spécialisations des langues parlées

## Durée d'exécution

- **Phase 1** (collecte des liens): ~2-3 minutes
- **Phase 2** (extraction détaillée): ~25-30 minutes  
- **Total**: ~30 minutes pour les 152 avocats

## Maintenance

Pour mettre à jour les données:

```bash
# Supprimer les anciens fichiers
rm VANNES_FINAL_* VANNES_BACKUP_* VANNES_RAPPORT_*

# Relancer l'extraction
python3 vannes_scraper_final.py
```

## Logs d'exemple

```
2026-02-23 13:00:00,000 - INFO - 🚀 VANNES SCRAPER - VERSION FINALE
2026-02-23 13:00:00,000 - INFO - 🔍 PHASE 1: COLLECTE DE TOUS LES LIENS D'AVOCATS
2026-02-23 13:00:30,000 - INFO - 📊 TOTAL LIENS COLLECTÉS: 152
2026-02-23 13:00:30,000 - INFO - 🔍 PHASE 2: EXTRACTION DÉTAILLÉE DE TOUS LES AVOCATS
2026-02-23 13:15:00,000 - INFO - 🎯 Section spé trouvée: Specialisation de l'avocat
2026-02-23 13:15:01,000 - INFO - ✅ Spé trouvée: Droit immobilier
2026-02-23 13:30:00,000 - INFO - ✅ Extraction terminée: 152 avocats traités
2026-02-23 13:30:00,000 - INFO - 📈 Spécialisations trouvées: 15 avocats (9.9%)
```

## Auteur

Claude Code - Version finale optimisée
Date: 2026-02-23