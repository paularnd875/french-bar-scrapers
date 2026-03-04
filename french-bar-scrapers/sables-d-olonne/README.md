# Scraper Barreau des Sables d'Olonne

Ce scraper permet d'extraire automatiquement toutes les informations des avocats inscrits au Barreau des Sables d'Olonne.

## 🎯 Fonctionnalités

- **Extraction complète** : 60 avocats du barreau
- **Informations collectées** :
  - Prénom et nom (séparés)
  - Email (décodage automatique des emails encodés)
  - Année d'inscription au barreau
  - Spécialisations (quand disponibles)
  - Cabinet/Structure d'exercice
  - URL de la fiche individuelle
- **Formats de sortie** : CSV, JSON, TXT (emails uniquement), rapport détaillé

## 📊 Résultats

- **100% de réussite** sur l'extraction des emails et années d'inscription
- **Spécialisations extraites** : Droit du travail, Droit public, Droit de la famille, Droit des sociétés, etc.
- **Cabinets identifiés** : Noms complets des structures d'exercice

## 🚀 Utilisation

### Installation

```bash
pip install selenium
```

### Utilisation de base

```python
from sables_olonne_scraper import SablesOlonneLawyerScraperFinalCorrected

# Mode production (headless)
scraper = SablesOlonneLawyerScraperFinalCorrected(headless=True)
lawyers_data = scraper.scrape_all_lawyers()
scraper.save_results(lawyers_data)
scraper.close()
```

### Ligne de commande

```bash
# Mode production complet
python sables_olonne_scraper.py

# Mode test (10 premiers avocats, interface visible)
python sables_olonne_scraper.py test
```

## 📁 Fichiers générés

- `SABLES_OLONNE_CORRIGE_60_avocats_[timestamp].csv` - Données complètes
- `SABLES_OLONNE_CORRIGE_60_avocats_[timestamp].json` - Format JSON
- `SABLES_OLONNE_CORRIGE_EMAILS_SEULEMENT_[timestamp].txt` - Liste des emails
- `SABLES_OLONNE_CORRIGE_RAPPORT_COMPLET_[timestamp].txt` - Rapport détaillé

## 🔧 Caractéristiques techniques

- **Anti-détection** : Configuration Chrome pour éviter la détection
- **Gestion des cookies** : Acceptation automatique
- **Décodage d'emails** : Correction automatique des emails encodés URL
- **Extraction robuste** : Gestion des erreurs et fallbacks multiples
- **Filtrage intelligent** : Spécialisations extraites sans éléments parasites

## 📋 Exemple de données extraites

```csv
prenom,nom,email,annee_inscription,specialisations,structure,cabinet,url
Thierry,ANGIBAUD,cabinet.angibaud@gmail.com,1994,,CABINET ANGIBAUD-MARCHAIS AVOCATS,CABINET ANGIBAUD-MARCHAIS AVOCATS,https://www.barreaudessablesdolonne.fr/page/annuaire/maitre-thierry-angibaud-97.htm
Liliane,BARRE,lbarre@pbsv.fr,1995,Droit du travail,SOCIETE D'AVOCATS PBSV,SOCIETE D'AVOCATS PBSV,https://www.barreaudessablesdolonne.fr/page/annuaire/maitre-liliane-barre-89.htm
```

## 🎯 Spécialisations identifiées

- Droit du travail
- Droit public
- Droit de la famille, des personnes et de leur patrimoine
- Droit du dommage corporel
- Droit des sociétés

## ⚙️ Configuration

Le scraper est configuré pour fonctionner avec :
- Chrome WebDriver (Selenium)
- Gestion automatique des cookies
- Délais adaptatifs entre les requêtes
- Mode headless pour la production

## 🐛 Résolution des problèmes

### Emails encodés
Le scraper corrige automatiquement les emails encodés URL comme :
- `gd%65%62a%79n%61%73t.%61%76ocat@orange.fr` → `gdebaynast.avocat@orange.fr`

### Erreurs courantes
- **ChromeDriver** : Assurez-vous d'avoir Chrome installé
- **Timeouts** : Vérifiez votre connexion internet
- **Éléments non trouvés** : Le site peut avoir changé de structure

## 📈 Statistiques

- **Avocats extraits** : 60/60 (100%)
- **Emails récupérés** : 60/60 (100%) 
- **Années d'inscription** : 60/60 (100%)
- **Cabinets identifiés** : 60/60 (100%)
- **Spécialisations** : 6/60 (10% - selon disponibilité sur le site)

## 🔄 Historique des versions

### Version finale corrigée
- ✅ Correction du décodage des emails encodés URL
- ✅ Extraction propre des spécialisations (sans parasites)
- ✅ Noms complets des cabinets (pas seulement "CABINET")
- ✅ 100% de réussite sur tous les champs disponibles

## 📞 Support

Ce scraper fait partie du projet french-bar-scrapers pour l'extraction automatisée des annuaires d'avocats français.