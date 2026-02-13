# Scraper Barreau de Guyane

## Description

Scraper complet pour extraire toutes les informations des avocats du Barreau de Guyane depuis leur annuaire officiel : https://www.avocats-barreau-guyane.com/annuaire-des-avocats.htm

## Fonctionnalités

✅ **Extraction complète** : Tous les avocats de l'annuaire  
✅ **Navigation automatique** : Parcours toutes les pages  
✅ **Gestion des cookies** : Acceptation automatique  
✅ **Mode headless** : Fonctionne sans ouvrir de fenêtre  
✅ **Extraction détaillée** : Informations complètes par avocat  
✅ **Formats multiples** : JSON, CSV, TXT  
✅ **Rapports** : Statistiques et analyse des résultats  

## Informations extraites

Pour chaque avocat :
- **Nom complet** (Civilité, Prénom, Nom)
- **Email** ✉️
- **Téléphone** ☎️
- **Fax**
- **Adresse complète** 📍
- **Structure/Cabinet** 🏢
- **Spécialisations** ⚖️
- **Année d'inscription au barreau** 📅
- **Langues parlées** 🗣️
- **Page d'origine**
- **URL de la fiche détaillée**

## Fichiers disponibles

### 1. Version de test : `guyane_scraper_final.py`
Test sur les 3 premiers avocats avec fenêtre visible pour vérification.

```bash
python3 guyane_scraper_final.py
```

### 2. Version production : `guyane_scraper_production.py`
Extraction complète de tous les avocats en mode headless.

```bash
python3 guyane_scraper_production.py
```

## Installation des dépendances

```bash
# Installer les packages Python requis
pip3 install selenium

# S'assurer que ChromeDriver est installé
# MacOS avec Homebrew :
brew install chromedriver

# Ou télécharger depuis : https://chromedriver.chromium.org/
```

## Utilisation

### Mode Test (recommandé d'abord)
```bash
python3 guyane_scraper_final.py
```

### Mode Production
```bash
python3 guyane_scraper_production.py
```

Le script vous demandera :
- **Mode headless** : O/n (O = sans fenêtre, n = avec fenêtre)
- **Limite de pages** : nombre ou vide pour toutes les pages

### Exemple d'interaction
```
SCRAPER BARREAU DE GUYANE - VERSION PRODUCTION
==================================================
Mode sans fenêtre (headless) ? [O/n]: O
Limiter le nombre de pages ? (laissez vide pour toutes): 
```

## Fichiers générés

Après chaque exécution, plusieurs fichiers sont créés :

### Fichiers de données
- `GUYANE_COMPLET_XXX_avocats_YYYYMMDD_HHMMSS.json` - Données complètes
- `GUYANE_COMPLET_XXX_avocats_YYYYMMDD_HHMMSS.csv` - Format tableur
- `GUYANE_EMAILS_SEULEMENT_YYYYMMDD_HHMMSS.txt` - Liste des emails uniquement

### Fichiers de rapport
- `GUYANE_RAPPORT_COMPLET_YYYYMMDD_HHMMSS.txt` - Rapport détaillé avec statistiques

## Structure des données JSON

```json
{
  "nom_complet": "Maître Francesca ADJOUALE",
  "civilite": "Maître",
  "prenom": "Francesca", 
  "nom": "ADJOUALE",
  "structure": "SELASU Muriel PREVOT",
  "email": "adj_francesca@hotmail.com",
  "telephone": "0594.28.21.21",
  "fax": "0594.31.25.42",
  "adresse": "794 route de baduel, 97300 Cayenne",
  "specialisations": "Droit civil | Droit des affaires",
  "annee_inscription": "2015",
  "langues": "Français, Anglais",
  "page_origine": 1,
  "detail_url": "https://www.avocats-barreau-guyane.com/annuaire-des-avocats/annuaire/maitre-francesca-adjouale-7.htm"
}
```

## Performances

**Site analysé** : 83 avocats détectés (au 12/02/2026)  
**Temps d'exécution** : ~5-10 minutes en mode headless  
**Taux de succès emails** : ~60-80% selon la complétude des fiches  

## Gestion d'erreurs

Le scraper inclut :
- ⚠️ Gestion des timeouts
- 🔄 Retry automatique sur les échecs
- 📝 Log détaillé des erreurs
- 🛡️ Protection anti-détection
- ⏸️ Pauses intelligentes entre requêtes

## Conformité légale

⚖️ **Important** : Ce scraper extrait des informations **publiquement disponibles** sur l'annuaire officiel du Barreau de Guyane. L'utilisation doit respecter :

- Les conditions d'utilisation du site
- Le RGPD pour les données personnelles  
- L'usage professionnel et légitime des données

## Dépannage

### Erreur ChromeDriver
```bash
# Réinstaller ChromeDriver
brew reinstall chromedriver
# Ou mettre à jour Chrome
```

### Erreur de permissions
```bash
# Donner les permissions d'exécution
chmod +x chromedriver
```

### Site inaccessible
- Vérifier votre connexion internet
- Le site peut être temporairement indisponible

## Exemples de résultats

### Statistiques typiques
```
Total avocats: 83
Avocats avec email: 52 (62.7%)
Avocats avec téléphone: 78 (94.0%)
Avocats avec adresse: 71 (85.5%)
Avocats avec spécialisations: 23 (27.7%)
```

### Emails extraits
```
adj_francesca@hotmail.com
janycia.aubert@gmail.com
victor.audubert@avocat.fr
...
```

## Support

En cas de problème :
1. Vérifier les prérequis (Chrome, ChromeDriver, Python 3)
2. Tester d'abord en mode visible (headless=False)
3. Consulter les logs détaillés générés

## Évolutions possibles

- 🔄 Détection automatique des changements sur le site
- 📊 Dashboard de suivi des extractions
- 🔗 Integration avec CRM
- 📧 Validation automatique des emails
- 🌍 Support d'autres barreaux

---

**Développé pour l'extraction professionnelle de données publiques**  
*Dernière mise à jour : 12/02/2026*