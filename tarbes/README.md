# Scraper Barreau de Tarbes

Ce scraper extrait les informations complètes de tous les avocats du Barreau de Tarbes depuis leur annuaire en ligne.

## 🎯 Fonctionnalités

- **Extraction complète** : 79 avocats avec toutes leurs informations
- **Données structurées** : Nom, prénom, inscription, spécialisations, structures d'exercice
- **Structures d'exercice** : SCP, SELARL, cabinets secondaires (38% de couverture)
- **Spécialisations juridiques** : Extraction des spécialisations réelles (Droit du travail, Droit du dommage corporel)
- **Navigation multi-pages** : Parcourt automatiquement les 10 pages de l'annuaire
- **Mode headless** : Exécution invisible en arrière-plan
- **Gestion robuste** : Sauvegardes intermédiaires, logs détaillés, gestion d'erreurs

## 📊 Qualité des données

- ✅ **100%** des noms complets et coordonnées
- ✅ **98.7%** des années d'inscription
- ✅ **38%** des structures d'exercice (excellent taux)
- ✅ **5.1%** des spécialisations juridiques
- ✅ **22** structures d'exercice distinctes identifiées

## 🚀 Installation

```bash
pip install -r requirements.txt
```

## 💻 Utilisation

### Extraction complète (recommandée)
```bash
python tarbes_scraper.py
```

### Mode avec fenêtre visible (debug)
Modifiez dans le script : `TarbesScraper(headless=False)`

## 📁 Fichiers générés

Le script génère automatiquement :

- `TARBES_COMPLET_79_avocats_YYYYMMDD_HHMMSS.csv` - Données CSV
- `TARBES_COMPLET_79_avocats_YYYYMMDD_HHMMSS.json` - Données JSON  
- `TARBES_COMPLET_79_avocats_YYYYMMDD_HHMMSS_RAPPORT.txt` - Rapport détaillé
- `tarbes_scraper.log` - Logs d'exécution
- `TARBES_BACKUP_*` - Sauvegardes intermédiaires

## 📋 Structure des données

| Champ | Description | Exemple |
|-------|-------------|---------|
| `nom_complet` | Nom complet de l'avocat | "Jean-Jacques Fellonneau" |
| `prenom` | Prénom séparé | "Jean-Jacques" |
| `nom` | Nom de famille | "Fellonneau" |
| `annee_inscription` | Année d'inscription au barreau | "1977" |
| `date_serment` | Date de prestation de serment | "1977" |
| `specialisations` | Spécialisations juridiques | "Droit du travail" |
| `structure_exercice` | Structure d'exercice | "SCP CHEVALLIER-FILLASTRE" |
| `adresse` | Adresse complète | "19 bis rue Georges Clémenceau 65000 TARBES" |
| `telephone` | Numéro de téléphone | "05 62 93 64 66" |
| `email` | Adresse email | "avocat@example.fr" |
| `url_source` | URL de vérification | "https://www.avocats-tarbes.fr/..." |

## 🏢 Types de structures identifiés

- **SELARL** (13 avocats) - Société d'Exercice Libéral à Responsabilité Limitée
- **SCP** (11 avocats) - Société Civile Professionnelle  
- **Cabinet secondaire** (2 avocats)
- **Exercice individuel** (53 avocats)

## ⚖️ Spécialisations trouvées

- **Droit du travail** (3 avocats)
- **Droit du dommage corporel** (1 avocat)

## 🔧 Configuration avancée

### Modification du nombre de pages
```python
scraper.scrape_all(max_pages=15)  # Par défaut : 15 pages max
```

### Mode debug complet
```python
scraper = TarbesScraper(headless=False)  # Affiche le navigateur
```

### Personnalisation des timeouts
```python
self.driver.implicitly_wait(10)  # Attente implicite
WebDriverWait(self.driver, 10)   # Attente explicite
```

## 📝 Logs et monitoring

Le script génère des logs détaillés dans `tarbes_scraper.log` :
```
2024-XX-XX XX:XX:XX - INFO - Début du scraping complet Tarbes
2024-XX-XX XX:XX:XX - INFO - Trouvé 8 avocats sur la page 1
2024-XX-XX XX:XX:XX - INFO - Page 1 - Avocat 1: Claude Sane
```

## ⚠️ Notes importantes

1. **Gestion des cookies** : Acceptation automatique des cookies du site
2. **Respect du site** : Délais entre les requêtes (2-3 secondes)
3. **Encodage** : Support complet UTF-8 pour les caractères français
4. **Robustesse** : Sauvegardes automatiques toutes les 3 pages

## 🐛 Résolution de problèmes

### Erreur ChromeDriver
```bash
# MacOS avec Homebrew
brew install chromedriver

# Ou télécharger depuis https://chromedriver.chromium.org/
```

### Timeout sur les pages
- Augmenter les délais dans `accept_cookies()` et `scrape_page()`
- Vérifier la connexion internet
- Passer en mode non-headless pour debug

### Données manquantes
- Vérifier les logs pour les erreurs d'extraction
- Le site peut avoir changé sa structure HTML
- Certaines informations peuvent ne pas être disponibles pour tous les avocats

## 📊 Statistiques historiques

**Dernière extraction complète :**
- Date : 2026-02-20 12:31:16
- Total : 79 avocats
- Structures : 30 (38%)
- Spécialisations : 4 (5.1%)
- Pages parcourues : 10/10

## 🔄 Maintenance

Pour mettre à jour les données :
```bash
# Cloner le repo
git clone https://github.com/paularnd875/french-bar-scrapers.git
cd french-bar-scrapers/tarbes

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'extraction
python tarbes_scraper.py
```

## 🤝 Contribution

Ce scraper fait partie du projet `french-bar-scrapers` qui vise à centraliser l'extraction des données des barreaux français.

---

**Site source :** https://www.avocats-tarbes.fr/annuaire/
**Développé pour :** Extraction complète avec structures d'exercice
**Dernière mise à jour :** 2026-02-20