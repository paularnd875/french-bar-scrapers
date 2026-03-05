# Scraper Barreau de Nouméa

Script d'extraction complète des informations des avocats du Barreau de Nouméa (Nouvelle-Calédonie).

## 🎯 Fonctionnalités

### Extraction Complète
- **Noms complets** : Extraction des prénom/nom avec séparation automatique
- **Dates de serment** : Année d'inscription au barreau
- **Activités dominantes** : Spécialisations juridiques
- **Coordonnées** : Emails, téléphones, adresses
- **130 avocats** : Base complète du barreau

### Données Extraites
- ✅ **Noms complets** (100%)
- ✅ **Dates de serment** (100%)  
- ✅ **Activités dominantes** (82.3%)
- ✅ **Emails** (~67%)
- ✅ **Téléphones** (~40%)
- ✅ **Adresses** (100%)

## 🚀 Installation

```bash
# Cloner le repository
git clone https://github.com/paularnd875/french-bar-scrapers.git
cd french-bar-scrapers/noumea

# Installer les dépendances
pip install -r requirements.txt
```

## 📋 Utilisation

### Mode Test (5 avocats)
```bash
python noumea_scraper.py --test
```

### Mode Production (130 avocats)
```bash
python noumea_scraper.py
```

## 📁 Fichiers Générés

### Données Principales
- `NOUMEA_PRODUCTION_FINAL_130avocats_YYYYMMDD_HHMMSS.csv` - Données complètes au format CSV
- `NOUMEA_PRODUCTION_FINAL_130avocats_YYYYMMDD_HHMMSS.json` - Données complètes au format JSON

### Extractions Spécialisées
- `NOUMEA_PRODUCTION_FINAL_EMAILS_XXemails_YYYYMMDD_HHMMSS.txt` - Liste unique d'emails
- `NOUMEA_PRODUCTION_FINAL_ACTIVITES_XXactivites_YYYYMMDD_HHMMSS.txt` - Liste unique d'activités dominantes
- `NOUMEA_PRODUCTION_FINAL_RAPPORT_FINAL_YYYYMMDD_HHMMSS.txt` - Rapport détaillé avec statistiques

### Sauvegardes Intermédiaires
- `NOUMEA_FINAL_BACKUP_XXfiches_YYYYMMDD_HHMMSS.json` - Sauvegardes automatiques toutes les 20 extractions

## 🏛️ Structure des Données

### Champs Principaux
```json
{
  "id": "125",
  "url": "https://www.barreau-noumea.nc/annuaire/125", 
  "nom_complet": "ZAOUCHE Vanessa",
  "prenom": "Vanessa",
  "nom": "ZAOUCHE",
  "email": "zaouche@zr-avocats.nc",
  "telephone": "",
  "annee_serment": "2006",
  "activites_dominantes": "Droit des assurances | Droit de la construction | Droit de l'immobilier",
  "adresse_complete": "3 rue RP Goujon - Vallée des Colons 98800 Nouméa",
  "ville": "Nouméa",
  "code_postal": "98800",
  "pays": "Nouvelle-Calédonie"
}
```

## 📊 Résultats Attendus

### Statistiques de Performance
- **130 avocats** traités
- **87 emails** extraits (66.9%)
- **52 téléphones** extraits (40%)
- **130 noms** extraits (100%)
- **130 dates de serment** extraites (100%)
- **107 activités dominantes** extraites (82.3%)

### Activités Dominantes Courantes
- Droit civil
- Droit pénal
- Droit des affaires
- Droit de la famille
- Droit du travail
- Droit commercial
- Droit immobilier
- Droit des assurances
- Préjudices corporels
- Droit public

## ⚙️ Configuration Technique

### Spécificités Nouméa
- **Site web** : https://www.barreau-noumea.nc
- **Parsing HTML** : Extraction ciblée via sélecteurs CSS
- **Rate limiting** : 0.5 seconde entre chaque requête
- **Timeout** : 15 secondes par requête
- **User-Agent** : Simulation navigateur standard

### Robustesse
- Gestion d'erreurs automatique
- Sauvegardes intermédiaires
- Extraction multi-méthodes pour les activités dominantes
- Patterns regex optimisés pour les coordonnées

## 🔄 Mise à Jour

Le script peut être relancé facilement pour mettre à jour la base de données :

```bash
# Dernière extraction
python noumea_scraper.py

# Comparer avec les anciennes données
ls -la NOUMEA_PRODUCTION_FINAL_*.csv
```

## 📞 Support Nouvelle-Calédonie

Format téléphones supportés :
- `+687 XX XX XX` (international)
- `687 XX XX XX` (local)
- Extraction automatique avec nettoyage

## ⚡ Performance

- **Durée moyenne** : ~2-3 minutes pour 130 avocats
- **Stabilité** : Très robuste avec gestion d'erreurs
- **Qualité** : Extraction haute fidélité des données

---

📧 **Contact** : paul.arnould@gmail.com
🏛️ **Barreau de Nouméa** : https://www.barreau-noumea.nc