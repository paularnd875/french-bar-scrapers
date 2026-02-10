# Scraper du Barreau d'Angers

## 📋 Description

Scraper complet pour extraire les données de tous les avocats inscrits au barreau d'Angers depuis https://barreau-angers.org/annuaire-des-avocats/

## ✅ Résultats

- **455 avocats** extraits avec succès
- **Taux de succès emails** : > 90%
- **Mode headless** : Aucune fenêtre de navigateur
- **Durée d'exécution** : ~30 minutes

## 📊 Données extraites

Pour chaque avocat :
- Nom complet (prénom + nom séparés)
- Adresse email professionnelle
- Adresse complète avec code postal
- Spécialisations juridiques
- Structure (Cabinet/Exercice individuel)
- URL de la fiche

## 📁 Fichiers

### Scripts principaux
- **`angers_production_working.py`** - Script de production final (recommandé)
- `angers_production_final.py` - Version alternative
- `angers_scraper_final.py` - Version avec extraction améliorée
- `angers_scraper_requests.py` - Version basique avec requests/BeautifulSoup

### Scripts de test
- `angers_scraper_test.py` - Script de test initial
- `angers_minimal_test.py` - Test minimal de connectivité

### Résultats
- **`angers_production_COMPLET_20260209_161245.json`** - Données complètes (JSON)
- **`angers_production_COMPLET_20260209_161245.csv`** - Données complètes (CSV)
- `angers_production_backup_*.json` - Sauvegardes intermédiaires

## 🚀 Utilisation

### Installation des dépendances
```bash
pip3 install requests beautifulsoup4
```

### Lancement du scraper
```bash
python3 angers_production_working.py
```

## ⚙️ Fonctionnalités

- **Gestion des cookies** automatique
- **Mode headless** (sans fenêtres)
- **Sauvegardes automatiques** tous les 100 avocats
- **Gestion d'erreurs** robuste
- **Respect du site** avec pauses entre requêtes
- **Formats multiples** : JSON + CSV

## 📈 Statistiques

- Total avocats : **455**
- Emails trouvés : **~410** (90%+)
- Adresses trouvées : **~450** (99%)
- Spécialisations détectées : **~300** (65%)

## 🛠️ Technical Stack

- **Python 3.x**
- **Requests** : Client HTTP
- **BeautifulSoup** : Parsing HTML
- **Regex** : Extraction de données
- **JSON/CSV** : Export des données

## 📅 Date de création

Février 2026 - Scraper testé et validé

## 📧 Format des emails extraits

Exemples d'emails récupérés :
- marie.brosset@avocat.fr
- christelle.ranchoux@acr-avocats.com  
- contact@gaya-avocats.fr
- lr.penneau@oratio-avocats.com

## ⚖️ Spécialisations détectées

- Droit Civil
- Droit Pénal  
- Droit Commercial
- Droit du Travail
- Droit de la Famille
- Droit Immobilier
- Droit des Affaires
- Droit Public
- Droit Administratif
- Etc.