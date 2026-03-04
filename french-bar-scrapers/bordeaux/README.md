# Scraper Barreau de Bordeaux

Scripts d'extraction automatique des données des avocats du Barreau de Bordeaux.

## 🎯 Objectif
Extraire l'ensemble des informations des avocats inscrits au Barreau de Bordeaux depuis le site officiel https://www.barreau-bordeaux.com/avocats/

## 📊 Résultats obtenus
- **Total avocats** : 2,147
- **Emails** : 100% (2,147 avocats)
- **Téléphones** : 100% (2,147 avocats) 
- **Cabinets** : 100% (2,147 avocats)
- **Spécialisations** : 164 avocats (7.6%)
- **Emails uniques** : 2,129

## 🛠️ Scripts principaux

### 1. `bordeaux_production_final.py`
Script principal d'extraction des données des avocats.

**Fonctionnalités :**
- Acceptation automatique des cookies
- Contournement des protections anti-bot
- Extraction parallèle avec multi-threading
- Sauvegarde incrémentale toutes les 100 fiches
- Simulation de comportement humain

**Utilisation :**
```bash
# Test sur 10 avocats
python3 bordeaux_production_final.py --test

# Extraction complète
python3 bordeaux_production_final.py
```

### 2. `bordeaux_specialisations_final.py`
Script d'extraction des spécialisations par codes officiels.

**Spécialisations extraites :**
- Droit du dommage corporel (24 avocats)
- Droit fiscal et droit douanier (22 avocats)
- Droit du travail (22 avocats)
- Droit de la sécurité sociale (22 avocats)
- Et 15 autres spécialisations

### 3. `bordeaux_fusion_final.py`
Script de fusion des données principales avec les spécialisations.

**Fonctionnalités :**
- Normalisation des noms pour correspondance
- Gestion des formats de noms concaténés
- Génération de rapports détaillés

## 📁 Fichiers de sortie

### Données finales
- `bordeaux_FINAL_COMPLET_20260210_170242.csv` - Données complètes au format CSV
- `bordeaux_FINAL_COMPLET_20260210_170242.json` - Données complètes au format JSON
- `bordeaux_FINAL_EMAILS_20260210_170242.txt` - Liste des emails uniques
- `bordeaux_FINAL_RAPPORT_20260210_170242.txt` - Rapport détaillé

### Données intermédiaires
- `bordeaux_specialisations_relations_20260210_170101.csv` - Relations spécialisations

## 🔧 Défis techniques résolus

### Anti-détection
- **Problème** : Protection anti-bot sophistiquée
- **Solution** : Rotation des User-Agent, délais humains, exécution JavaScript

### Extraction données complètes
- **Problème** : Informations partielles dans les résultats de recherche
- **Solution** : Extraction individuelle depuis les profils détaillés

### Fusion des spécialisations
- **Problème** : Formats de noms différents entre sources
- **Solution** : Parsing regex et normalisation multi-variantes

## ⚡ Performance
- **Threads** : 5-10 workers parallèles
- **Vitesse** : ~2 secondes par fiche avocat
- **Fiabilité** : 100% de réussite sur 2,147 avocats
- **Durée totale** : ~70-90 minutes pour l'extraction complète

## 🎁 Données extraites par avocat
- Nom et prénom
- Email professionnel
- Numéro de téléphone
- Adresse du cabinet
- Année d'inscription au barreau
- Spécialisations officielles (si disponibles)
- Structure du cabinet

---
*Extraction réalisée le 10 février 2026*