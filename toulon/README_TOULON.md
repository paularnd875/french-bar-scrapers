# Scraper Barreau de Toulon

Script Python pour extraire automatiquement tous les avocats de l'annuaire du Barreau de Toulon.

## 🎯 Fonctionnalités

- **Extraction complète** de l'annuaire https://barreautoulon.fr/avocats/annuaire/
- **Données extraites** :
  - Nom et prénom (parsing automatique)
  - Email professionnel
  - Téléphone
  - Année d'inscription au barreau
  - Spécialisations/compétences
  - Structure (cabinet, SELAS, etc.)
  - URL source de la fiche avocat
- **Formats de sortie** : CSV, JSON, TXT (emails uniquement)
- **Performance** : ~500 avocats en moins de 2 minutes
- **Robustesse** : Gestion d'erreurs et retry automatique

## 📋 Prérequis

```bash
pip install requests beautifulsoup4 pandas
```

## 🚀 Utilisation

### Extraction complète (recommandé)
```bash
python3 toulon_scraper_final.py
```

### Extraction limitée (pour test)
```bash
python3 toulon_scraper_final.py 50  # Limite à 50 avocats
```

## 📁 Fichiers générés

Le script génère automatiquement :

- `TOULON_AVOCATS_XXX_avocats_YYYYMMDD_HHMMSS.csv` - Données complètes en CSV
- `TOULON_AVOCATS_XXX_avocats_YYYYMMDD_HHMMSS.json` - Données complètes en JSON  
- `TOULON_AVOCATS_EMAILS_XXX_emails_YYYYMMDD_HHMMSS.txt` - Emails uniquement

## 📊 Exemple de données extraites

```csv
nom,prenom,nom_complet,annee_inscription,specialisations,structure,adresse,telephone,email,source_url
DUPONT,Marie,Marie DUPONT,2010,"Droit Penal, Droit Civil",SELAS DUPONT ASSOCIES,,0494123456,marie.dupont@avocat-conseil.fr,https://barreautoulon.fr/avocat/marie-dupont
```

## ⚡ Performances typiques

- **Avocats extraits** : ~520 (annuaire complet)
- **Durée** : 60-90 secondes
- **Taux de réussite** :
  - 📧 Emails : 99%+
  - 📞 Téléphones : 95%+
  - 🔗 Sources : 100%
  - 🎯 Spécialisations : 7-10%

## 🔧 Configuration avancée

Le script peut être modifié pour ajuster :

- **Timeout** : Délai d'attente par page (défaut: 30s)
- **Pause** : Délai entre pages (défaut: 1s)  
- **User-Agent** : Headers HTTP personnalisés

## 🐛 Dépannage

### Erreur "No module named"
```bash
pip install requests beautifulsoup4 pandas
```

### Timeout ou erreur réseau
- Vérifier la connexion internet
- Le site peut être temporairement indisponible
- Relancer le script (il reprendra automatiquement)

### Aucun avocat trouvé
- Vérifier que le site https://barreautoulon.fr/avocats/annuaire/ est accessible
- La structure du site peut avoir changé

## 📝 Historique des versions

- **v3.0** (Final) - Version HTTP optimisée, extraction complète
- **v2.0** - Ajout spécialisations et URLs sources 
- **v1.0** - Version Selenium de base

## ⚖️ Usage responsable

Ce script est conçu pour un usage légitime d'information publique. Respectez :
- Les conditions d'utilisation du site
- La réglementation RGPD
- Un usage raisonnable (pas de spam)

## 🔄 Mise à jour

Pour mettre à jour votre base de données :

1. Supprimer les anciens fichiers de résultats
2. Relancer le script complet
3. Comparer les nouveaux résultats avec l'ancienne base

## 📞 Support

En cas de problème :
1. Vérifier les prérequis
2. Tester avec une limite (ex: 10 avocats)
3. Consulter les logs d'erreur affichés