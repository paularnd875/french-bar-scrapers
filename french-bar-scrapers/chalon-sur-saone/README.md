# 🏛️ Scraper Barreau de Chalon-sur-Saône

Scraper complet pour extraire toutes les informations des avocats du Barreau de Chalon-sur-Saône.

## 🎯 Fonctionnalités

- **Extraction complète** : Tous les 100 avocats sur les 7 pages
- **Données récupérées** : Nom, prénom, email, téléphone, adresse, ville, spécialisations, structure
- **Navigation automatique** : Parcourt toutes les pages automatiquement
- **Mode headless** : Fonctionne sans interface (pas de fenêtres qui s'ouvrent)
- **Sauvegarde multiple** : CSV, JSON, TXT (emails uniquement)
- **Gestion d'erreurs** : Continue même en cas de problème sur un avocat
- **Sauvegardes intermédiaires** : Évite de perdre les données

## 📋 Prérequis

- Python 3.x
- Chrome ou Chromium installé
- Selenium (installé automatiquement)

## 🚀 Utilisation

### Méthode 1 : Script automatique (recommandé)
```bash
./run_chalon_scraper.sh
```

### Méthode 2 : Lancement direct

#### Mode headless (production)
```bash
python3 chalon_scraper_production.py
```

#### Mode visuel (debug)
```bash
python3 chalon_scraper_production.py --visual
```

## 📁 Fichiers générés

Après l'exécution, vous trouverez :

- `chalon_COMPLET_YYYYMMDD_HHMMSS.csv` - Données complètes au format CSV
- `chalon_COMPLET_YYYYMMDD_HHMMSS.json` - Données complètes au format JSON
- `chalon_EMAILS_SEULEMENT_YYYYMMDD_HHMMSS.txt` - Liste des emails uniquement
- `chalon_RAPPORT_COMPLET_YYYYMMDD_HHMMSS.txt` - Rapport avec statistiques
- `chalon_partial_pX_YYYYMMDD_HHMMSS.json` - Sauvegardes intermédiaires

## 🧪 Tests disponibles

### Test simple (3 avocats)
```bash
python3 chalon_scraper_test.py
```

### Test pagination (2 pages)
```bash
python3 chalon_scraper_test_pagination.py
```

## 📊 Taux de réussite

Basé sur les tests effectués :

| Donnée | Taux de réussite |
|--------|------------------|
| Nom/Prénom | 100% |
| Email | 100% |
| Téléphone | 100% |
| Adresse | 100% |
| Ville | 100% |
| Spécialisations | 100% (avec nettoyage nécessaire) |
| Année inscription | Variable |
| Structure | Variable |

## ⚙️ Configuration

Le scraper est optimisé pour :
- Éviter la détection anti-bot
- Fonctionner en mode headless
- Gérer les timeouts
- Respecter les délais entre requêtes (1-3 secondes)

## 🔧 Dépannage

### Chrome/Chromium non trouvé
Assurez-vous que Chrome est installé dans un répertoire standard.

### Timeout de chargement
Le script attend jusqu'à 15 secondes pour le chargement des pages. Vous pouvez modifier cette valeur dans `WebDriverWait(self.driver, 15)`.

### Mode headless ne fonctionne pas
Utilisez le mode visuel pour le debug :
```bash
python3 chalon_scraper_production.py --visual
```

## 📈 Durée d'exécution

- **Test (3 avocats)** : ~30 secondes
- **Test pagination (4 avocats)** : ~1 minute
- **Complet (100 avocats)** : ~15-20 minutes

## 🛡️ Bonnes pratiques

1. **Testez d'abord** : Utilisez les scripts de test avant le scraping complet
2. **Vérifiez les résultats** : Consultez le rapport généré
3. **Sauvegardez** : Les sauvegardes intermédiaires évitent les pertes de données
4. **Respectez le site** : Des délais sont intégrés pour ne pas surcharger le serveur

## 📞 Support

En cas de problème :
1. Vérifiez les logs affichés à l'écran
2. Consultez le fichier de rapport généré
3. Testez d'abord avec les scripts de test
4. Utilisez le mode visuel pour voir ce qui se passe

---

✅ **Scraper testé et validé sur le site officiel du Barreau de Chalon-sur-Saône**