# Barreau de Lyon - Scraper Complet

## 🎯 Résultats Finaux

**Scraper du Barreau de Lyon avec 96.3% d'emails récupérés**

### Statistiques Finales
- **4141 avocats** extraits (100% du barreau)
- **3987 emails récupérés** (96.3% de couverture)
- **4141 dates de serment** (100% de couverture)
- **Téléphones et spécialisations** inclus

### Fichier Principal
📁 `data/LYON_COMPLET_FINAL_4141avocats_3987emails_4141dates_20260518_180705.csv`

## 🚀 Installation et Usage

### Prérequis
```bash
pip install -r requirements.txt
```

### Lancement Rapide
```bash
cd lyon/
python3 scripts/scraper_barreau_lyon_complet_final.py
```

### Mode Production
Le scraper utilise l'API WordPress du barreau pour une extraction complète et fiable.

## 📋 Structure des Données

### Champs Extraits
- `nom` : Nom de famille
- `prenom` : Prénom(s)
- `email` : Adresse email (96.3% de couverture)
- `telephone` : Numéro de téléphone
- `specialisations` : Domaines de spécialisation
- `structure` : Cabinet/Structure
- `adresse` : Adresse complète
- `date_serment` : Date de prestation de serment
- `url` : URL source du profil

### Formats de Sortie
- **CSV** : Données complètes avec toutes les colonnes
- **JSON** : Format structuré pour intégrations API
- **TXT** : Liste d'emails uniquement

## 🔧 Architecture Technique

### Méthode d'Extraction
1. **API WordPress** : Récupération de la liste complète via `/wp-json/wp/v2/annuaire`
2. **Enrichissement individuel** : Visite de chaque profil pour extraction détaillée
3. **Fusion intelligente** : Combinaison des données emails + dates de serment

### Techniques d'Extraction Email (96.3% de succès)
```python
# Méthode 1: Liens mailto (prioritaire)
mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))

# Méthode 2: Regex dans HTML
emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_content)
```

### Gestion des Erreurs
- Retry automatique avec backoff exponentiel
- Sauvegarde intermédiaire tous les 50 avocats
- Validation stricte des emails
- Timeout configurable par requête

## 📊 Historique des Versions

### Version Finale (Mai 2026)
- ✅ 4141 avocats (100% du barreau)
- ✅ 3987 emails (96.3% de couverture)
- ✅ Dates de serment complètes
- ✅ Architecture modulaire pour plateforme

### Améliorations Techniques
- **API WordPress native** (plus fiable que scraping HTML)
- **Enrichissement par lots** avec pause respectueuse
- **Fusion de données** par URL unique
- **Validation avancée** des emails français

## 🏗️ Intégration Plateforme

### Structure Recommandée
```
lyon/
├── scripts/           # Scripts d'extraction
├── data/             # Fichiers de résultats
├── docs/             # Documentation
└── requirements.txt   # Dépendances
```

### Configuration Plateforme
```python
BARREAU_LYON = {
    'nom': 'Barreau de Lyon',
    'url_base': 'https://www.barreaulyon.com',
    'api_endpoint': '/wp-json/wp/v2/annuaire',
    'script': 'scraper_barreau_lyon_complet_final.py',
    'couverture_email': 96.3,
    'total_avocats': 4141
}
```

## 📈 Performance

### Temps d'Exécution
- **Extraction complète** : ~3-4 heures
- **Enrichissement** : ~2 avocats/minute
- **Respect des limites** : Pause 1-2s entre requêtes

### Optimisations
- Mode headless pour production
- Session persistante avec cookies
- Cache des URLs déjà visitées
- Gestion mémoire optimisée

## 🚨 Notes Importantes

### Respect du Site
- Pause minimale de 1 seconde entre requêtes
- User-Agent respectueux
- Pas de surcharge du serveur
- Extraction éthique et légale

### Maintenance
- Vérifier la structure API périodiquement
- Mettre à jour les sélecteurs si nécessaire
- Surveiller les changements du site web

---

**Développé par Paul Arnould & Claude - Mai 2026**  
**Prêt pour intégration dans la plateforme de scraping française**