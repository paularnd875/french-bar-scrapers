# Scraper Barreau de Brest

Ce scraper extrait les informations de tous les avocats du Barreau de Brest depuis le site officiel.

## 📋 Informations extraites

- **Nom complet** (prénom et nom séparés correctement)
- **Email** (100% de réussite)
- **Téléphone** (si disponible)
- **Adresse** (si disponible)  
- **Année de serment** (si disponible)
- **URL de la fiche** (lien direct)

## 🚀 Installation

```bash
# Cloner le repo
git clone https://github.com/paularnd875/french-bar-scrapers.git
cd french-bar-scrapers/brest

# Installer les dépendances
pip3 install selenium webdriver-manager
```

## 💻 Utilisation

### Extraction complète (recommandé)
```bash
python3 brest_scraper.py
```
- Extrait **tous les 258 avocats** (15 pages)
- Mode headless (pas d'interface visible)
- Génère 4 fichiers de sortie

### Mode test
```bash
python3 brest_scraper.py --test
```
- Extrait seulement **3 pages** (~54 avocats)
- Parfait pour tester le script

### Mode visuel (debug)
```bash
python3 brest_scraper.py --visual
```
- Interface Chrome visible
- Utile pour déboguer

## 📁 Fichiers générés

Le script génère automatiquement 4 fichiers avec timestamp :

1. **`brest_complet_YYYYMMDD_HHMMSS.csv`** - Format Excel
2. **`brest_complet_YYYYMMDD_HHMMSS.json`** - Données structurées
3. **`brest_complet_emails_YYYYMMDD_HHMMSS.txt`** - Liste emails uniquement
4. **`brest_complet_rapport_YYYYMMDD_HHMMSS.txt`** - Rapport détaillé

## 🎯 Résultats attendus

- **258 avocats** au total
- **100% d'emails** extraits
- **Noms parfaitement formatés** (correction automatique des noms composés)
- **Années de serment** quand disponibles

## 🔧 Fonctionnalités techniques

### Extraction intelligente des noms
- Parsing depuis les balises `<h6>` au format "NOM Prénom"
- Gestion automatique des noms composés
- Correction des particules (de, du, des, Mc, Mac, etc.)
- Fallback sur extraction depuis email si nécessaire

### Anti-détection
- Headers User-Agent réalistes
- Gestion automatique des cookies
- Pauses entre pages pour respecter le serveur
- Mode headless par défaut

### Robustesse
- Gestion d'erreurs complète
- Logs détaillés pour debugging
- Retry automatique sur erreurs temporaires

## 🌐 Site source

https://www.avocats-brest.fr/avocats/

## 📊 Exemple de résultats

```csv
prenom,nom,nom_complet,email,telephone,adresse,annee_serment,url_fiche,barreau
Elina,Nonnotte,Elina Nonnotte,elina.nonnotte@aoden-avocats.com,,,,https://www.avocats-brest.fr/avocats/nonnotteelina/?email=elina.nonnotte@aoden-avocats.com,Brest
Leslie,Baurreau-juhel,Leslie Baurreau-juhel,leslie.baurreau@lbj-avocat.fr,,,,https://www.avocats-brest.fr/avocats/baurreau-juhelleslie/?email=leslie.baurreau@lbj-avocat.fr,Brest
```

## ⚡ Performance

- **Temps d'exécution** : ~5-8 minutes en mode complet
- **Taux de réussite** : 100% pour les emails
- **Stabilité** : Script robuste avec gestion d'erreurs

## 🔄 Mise à jour des données

Pour mettre à jour votre base de données :

```bash
cd french-bar-scrapers/brest
python3 brest_scraper.py
```

Les nouveaux fichiers seront générés avec un timestamp actuel.
