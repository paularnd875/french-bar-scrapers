# Scraper Barreau de Thionville

Scraper pour extraire la liste complète des avocats du Barreau de Thionville avec leurs informations détaillées.

## 🎯 Fonctionnalités

- **Extraction complète** : Récupère tous les 54 avocats inscrits au barreau
- **Parsing intelligent des noms** : Traite correctement le format "NOMPrénom" du site (ex: "MULLERChristian" → "Christian MULLER")
- **Informations détaillées** : Prénom, nom, date de serment, adresse, téléphone, email, spécialisations
- **Enrichissement des profils** : Visite les pages individuelles pour extraire plus de détails
- **Exports multiples** : CSV, JSON, liste d'emails, rapport détaillé

## 📋 Données extraites

Pour chaque avocat :
- **Nom et prénom** séparés correctement
- **Date de serment** et année d'inscription au barreau
- **Adresse complète** (rue, ville)
- **Coordonnées** (téléphone, fax)
- **Email** (si disponible sur le profil)
- **Spécialisations** et compétences
- **Structure/Cabinet** d'appartenance
- **Lien vers le profil** pour vérification

## 🚀 Utilisation

### Installation des dépendances
```bash
pip3 install selenium beautifulsoup4 requests
```

### Commandes de base

**Mode production** (tous les avocats) :
```bash
python3 thionville_scraper.py
```

**Mode test** (première page seulement) :
```bash
python3 thionville_scraper.py --test
```

**Mode avec interface graphique** (pour debug) :
```bash
python3 thionville_scraper.py --no-headless
```

**Sans enrichissement des profils** (plus rapide) :
```bash
python3 thionville_scraper.py --no-enrich
```

### Options disponibles
- `--test` : Mode test (10-15 premiers avocats seulement)
- `--no-headless` : Affiche le navigateur Chrome (pour debug)
- `--no-enrich` : Évite de visiter chaque profil individuel (plus rapide)

## 📊 Résultats attendus

### Mode production complet
- **54 avocats** extraits
- **100% de réussite** pour les noms/prénoms
- **100% de réussite** pour les dates de serment
- **100% de réussite** pour les adresses
- **100% de réussite** pour les téléphones
- **0-30%** d'emails (selon disponibilité sur les profils)

### Fichiers générés
```
THIONVILLE_PRODUCTION_54_avocats_20260220_123456.csv    # Données principales
THIONVILLE_PRODUCTION_54_avocats_20260220_123456.json   # Format JSON
THIONVILLE_PRODUCTION_EMAILS_20260220_123456.txt        # Liste des emails
THIONVILLE_PRODUCTION_RAPPORT_20260220_123456.txt       # Rapport détaillé
```

## 🔧 Particularités techniques

### Parsing des noms
Le site Thionville utilise un format particulier où le nom et prénom sont collés : "MULLERChristian"

Le scraper utilise des regex sophistiquées pour séparer correctement :
```python
def parse_combined_name(self, combined_text):
    patterns = [
        r'^([A-Z]{2,}[A-Z\-]*)\s*([A-Z][a-z\-]+(?:\s*[A-Z][a-z\-]+)*)$',
        r'^([A-Z][A-Z\-]+)\s*([A-Z][a-z\-]+(?:\-[A-Z][a-z\-]+)*)$',
    ]
```

### Pagination
Le site utilise le paramètre `limitstart` :
- Page 1 : `limitstart=0` (15 avocats)
- Page 2 : `limitstart=15` (15 avocats)  
- Page 3 : `limitstart=30` (15 avocats)
- Page 4 : `limitstart=45` (9 avocats)

### Structure du tableau HTML
```
| Date serment | NOMPrénom | Adresse+Ville | Tél+Fax |
|--------------|-----------|---------------|---------|
| 12/04/1972   | MULLERChristian | 14 avenue de GaulleTHIONVILLE | 03.82.53.38.24 |
```

## 🐛 Problèmes connus et solutions

### 1. Erreur "WebDriver not found"
```bash
# Installer ChromeDriver via Homebrew (macOS)
brew install chromedriver

# Ou télécharger depuis https://chromedriver.chromium.org/
```

### 2. Timeout de page
Le scraper inclut des délais et retry automatiques, mais si problème :
```bash
python3 thionville_scraper.py --no-headless  # Pour voir ce qui se passe
```

### 3. Captcha ou protection
Le site Thionville ne semble pas avoir de protection particulière, mais le scraper inclut :
- User-Agent aléatoire
- Délais entre requêtes
- Gestion des cookies

## 📈 Historique des améliorations

### Version finale (février 2026)
- ✅ **Parsing parfait des noms** : Résolution du problème majeur d'extraction des noms
- ✅ **Structure complète** : Tous les champs requis extraits
- ✅ **Mode headless** : Fonctionne sans interface graphique
- ✅ **Enrichissement optionnel** : Visite des profils pour plus de détails
- ✅ **Arguments en ligne de commande** : Flexibilité d'utilisation

### Problèmes résolus
- ❌ **Noms mal extraits** ("I RIPOLL" au lieu de "Christian MULLER")
- ❌ **Erreurs de syntaxe** dans le parsing
- ❌ **URLs incorrectes** pour la pagination

## 🔍 Vérification des résultats

### Contrôle qualité automatique
Le rapport généré inclut :
```
=== QUALITÉ DES DONNÉES ===
Avec Prenom: 54/54 (100.0%)
Avec Nom: 54/54 (100.0%)  
Avec Date Serment: 54/54 (100.0%)
Avec Telephone: 54/54 (100.0%)
Avec Adresse: 54/54 (100.0%)
Avec Email: 0/54 (0.0%)
```

### Vérification manuelle
Comparer quelques résultats avec le site officiel :
https://www.avocats-thionville.fr/annuaire/userslist/Avocats?limit=15&limitstart=0

### Exemple de résultat correct
```csv
id,prenom,nom,nom_complet,date_serment,annee_inscription,adresse,ville,telephone
1,Christian,MULLER,Christian MULLER,12/04/1972,1972,14 avenue de Gaulle,THIONVILLE,03.82.53.38.24
2,Nadine,CHRISTMANN,Nadine CHRISTMANN,17/12/1980,1980,1 allée Poincaré,THIONVILLE,03.82.53.47.22
```

## 📱 Contact & Support

Pour toute question ou amélioration :
- Vérifier d'abord le rapport d'erreur généré
- Tester en mode `--no-headless` pour voir les erreurs
- Consulter les logs détaillés du scraper

Site source : https://www.avocats-thionville.fr/