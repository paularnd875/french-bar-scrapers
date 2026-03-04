# 🏛️ Scraper Barreau d'Arras - Version Enhanced

## 🚀 Lancement rapide

### Installation et exécution automatique
```bash
# 1. Cloner le repository
git clone https://github.com/paularnd875/french-bar-scrapers.git
cd french-bar-scrapers/arras-enhanced

# 2. Lancer le scraping (installation automatique des dépendances)
./launch_scraping.sh
```

### Lancement manuel
```bash
# Installation des dépendances
pip3 install -r requirements.txt

# Lancement automatique
python3 run_arras_scraping.py

# Ou lancement interactif
python3 arras_scraper_enhanced.py
```

## 📊 Résultats attendus

Le scraper extrait **98 avocats** du Barreau d'Arras avec :
- ✅ **100% de taux de réussite**
- 📧 **82.7%** d'emails trouvés
- 📞 **99.0%** de téléphones trouvés  
- 🏠 **100%** d'adresses trouvées
- ⚖️ **100%** de spécialisations trouvées
- ⏱️ **~5 minutes** d'exécution

## 📁 Fichiers générés

Après exécution, vous obtiendrez :
- `arras_enhanced_FINAL_YYYYMMDD_HHMMSS.csv` - Export CSV (84KB)
- `arras_enhanced_FINAL_YYYYMMDD_HHMMSS.json` - Données JSON avec métadonnées (139KB)
- `arras_report_FINAL_YYYYMMDD_HHMMSS.txt` - Rapport détaillé (2KB)
- Logs d'exécution automatiques

## ✨ Fonctionnalités avancées

- 🔄 **Reprise automatique** en cas d'interruption
- ✅ **Validation** des emails, téléphones et adresses
- 📊 **Score de qualité** pour chaque avocat (0-10)
- 📈 **Rapports détaillés** avec statistiques
- 🛡️ **Gestion d'erreurs robuste** avec retry
- 💾 **Sauvegarde progressive** tous les 10 avocats

## 🔧 Structure des fichiers

```
arras-enhanced/
├── arras_scraper_enhanced.py    # Scraper principal avec toutes les fonctionnalités
├── run_arras_scraping.py        # Lanceur automatique sans interaction
├── launch_scraping.sh           # Script bash pour lancement facile
├── requirements.txt             # Dépendances Python
├── README.md                   # Ce fichier
└── ARRAS_SCRAPER_README.md     # Documentation complète
```

## 🎯 Utilisation pour mise à jour future

Pour relancer le scraping et mettre à jour vos données :

```bash
# Récupérer la dernière version
git pull origin main

# Relancer le scraping
./launch_scraping.sh
```

Le scraper détectera automatiquement s'il y a de nouveaux avocats et ne traitera que les données nécessaires.

## 📋 Configuration

Par défaut, le scraper utilise :
- **Délai** : 2 secondes entre les requêtes
- **Reprise automatique** : Activée
- **Validation stricte** : Emails et téléphones français
- **Logs détaillés** : Activés

Pour personnaliser, modifiez `run_arras_scraping.py` ou utilisez `arras_scraper_enhanced.py` en mode interactif.

## 🐛 Dépannage

Si le scraping échoue :
1. Vérifiez votre connexion internet
2. Consultez les logs générés automatiquement  
3. Le scraper reprendra automatiquement où il s'était arrêté

## 📞 Support

Pour toute question ou problème, consultez la documentation complète dans `ARRAS_SCRAPER_README.md`.

---

**Dernière mise à jour** : Février 2026  
**Version** : Enhanced v1.0  
**Taux de réussite testé** : 100%