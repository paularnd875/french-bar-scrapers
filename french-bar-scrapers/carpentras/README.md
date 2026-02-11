# Scraper Barreau de Carpentras

## 🎯 Objectif
Extraire toutes les informations des avocats du Barreau de Carpentras depuis leur annuaire officiel : https://www.barreaudecarpentras.fr/annuaire-des-avocats-de-carpentras

## ✅ Fonctionnalités
- ✅ Acceptation automatique des cookies
- ✅ Extraction des noms et prénoms
- ✅ Récupération des emails
- ✅ Extraction des téléphones et fax
- ✅ Récupération des adresses complètes
- ✅ Extraction des années d'inscription au barreau
- ✅ Identification des spécialisations et fonctions (Bâtonnier, etc.)
- ✅ Récupération des sites web
- ✅ Mode headless (sans interface visuelle)
- ✅ Génération de multiples formats de sortie

## 📁 Fichiers disponibles

### 1. Script de test
- **`carpentras_scraper_fixed.py`** - Script de test avec 3 avocats (mode visuel)

### 2. Script de production  
- **`carpentras_scraper_production.py`** - Version optimisée headless pour tous les avocats

### 3. Scripts de debug
- **`carpentras_debug_structure.py`** - Analyse de la structure HTML

## 🚀 Utilisation

### Test rapide (3 avocats)
```bash
python3 carpentras_scraper_fixed.py
```

### Production complète (tous les avocats, headless)
```bash
python3 carpentras_scraper_production.py
```

## 📊 Résultats du test
Le test a extrait **3 avocats** avec succès :

| Nom | Prénom | Email | Année | Spécialisations |
|-----|---------|-------|--------|-----------------|
| BONHOMMO | YVES | cabinet@bonhommo.fr | 1984 | ANCIEN BÂTONNIER, BÂTONNIER |
| PENTZ | MARTINE | contact@pentz-avocat.com | 1984 | BÂTONNIER |
| GEIGER | MARC | - | 1988 | ANCIEN BÂTONNIER, BÂTONNIER |

## 📁 Fichiers générés

Le scraper génère automatiquement :

1. **`carpentras_COMPLET_YYYYMMDD_HHMMSS.json`** - Données complètes au format JSON
2. **`carpentras_COMPLET_YYYYMMDD_HHMMSS.csv`** - Données au format CSV (Excel)
3. **`carpentras_EMAILS_SEULEMENT_YYYYMMDD_HHMMSS.txt`** - Liste unique des emails
4. **`carpentras_RAPPORT_COMPLET_YYYYMMDD_HHMMSS.txt`** - Rapport détaillé

## 🛠️ Informations techniques

### Structure des données extraites
```json
{
  "nom": "BONHOMMO",
  "prenom": "YVES", 
  "email": "cabinet@bonhommo.fr",
  "telephone": "04 90 60 67 67",
  "fax": "04 90 60 62 85",
  "adresse": "48 Avenue Pierre Sémard à CARPENTRAS",
  "ville": "CARPENTRAS",
  "annee_inscription": "1984",
  "specialisations": ["ANCIEN BATONNIER", "BATONNIER"],
  "structure": "",
  "site_web": "http://example.com"
}
```

### Sélecteurs HTML utilisés
- **Conteneurs avocats** : `.eb-post-content`
- **Noms** : `h2.eb-post-title a`
- **Emails** : `a[href^='mailto:']`
- **Informations** : `table.table-bordered tbody tr`

### Gestion des cookies
Le script détecte et accepte automatiquement les cookies avec ces sélecteurs :
- `button[id*='cookie']`, `button[class*='cookie']`
- `.cookie-accept`, `#cookie-accept`
- `.accept-cookies`, `#accept-cookies`

## 📈 Statistiques attendues
Basé sur l'analyse du site :
- **~90 avocats** dans l'annuaire
- **~77 emails** disponibles (d'après l'analyse initiale)
- Villes : Carpentras, Orange, Vaison-la-Romaine et autres

## ⚙️ Configuration

### Prérequis
```bash
pip install selenium
```

### Chrome driver
Le script utilise ChromeDriver. Assurez-vous qu'il est installé :
```bash
# MacOS avec Homebrew
brew install chromedriver

# Ou télécharger depuis : https://chromedriver.chromium.org/
```

### Options du driver
- **Mode headless** activé en production
- **Anti-détection** : User-Agent naturel, suppression des flags automation
- **Optimisations** : Désactivation images, plugins, extensions
- **Timeouts** appropriés pour la stabilité

## 🐛 Débogage

### Logs disponibles
- **`carpentras_production.log`** - Log du scraper production
- **`carpentras_fixed.log`** - Log du scraper test

### En cas de problème
1. Vérifier que ChromeDriver est installé
2. Tester d'abord le script en mode visuel (`carpentras_scraper_fixed.py`)
3. Vérifier les logs pour les erreurs spécifiques
4. S'assurer que le site est accessible

### Screenshots de debug
Le script de debug génère :
- `carpentras_page_screenshot.png` - Screenshot de la page
- `carpentras_page_source.html` - Source HTML complet

## 🔧 Personnalisation

### Modifier le nombre d'avocats de test
```python
success = scraper.run_test(max_lawyers=5)  # Tester avec 5 avocats
```

### Ajouter des pauses entre extractions
```python
time.sleep(1)  # Pause de 1 seconde entre chaque avocat
```

### Modifier les timeouts
```python
self.driver.implicitly_wait(15)  # Timeout implicite de 15 secondes
```

## 📞 Support
En cas de problème, vérifiez :
1. La connectivité au site web
2. La version de ChromeDriver
3. Les logs d'erreurs
4. La structure HTML du site (peut évoluer)

## ⚠️ Notes importantes
- Le script respecte le site et inclut des pauses appropriées
- Mode headless pour ne pas interférer avec votre travail
- Sauvegarde automatique en plusieurs formats
- Gestion d'erreurs robuste pour éviter les interruptions