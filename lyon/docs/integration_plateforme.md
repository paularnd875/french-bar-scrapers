# Intégration du Scraper Lyon dans la Plateforme

## 🏗️ Configuration pour la Plateforme Globale

### Paramètres du Barreau
```python
BARREAU_LYON = {
    'id': 'lyon',
    'nom': 'Barreau de Lyon',
    'region': 'Auvergne-Rhône-Alpes',
    'departement': '69',
    'url_officiel': 'https://www.barreaulyon.com',
    'api_endpoint': '/wp-json/wp/v2/annuaire',
    'script_principal': 'scraper_barreau_lyon_complet_final.py',
    'methode': 'api_wordpress',
    'statut': 'operationnel',
    'derniere_maj': '2026-05-18',
    'statistiques': {
        'total_avocats': 4141,
        'emails_recuperes': 3987,
        'taux_email': 96.3,
        'dates_serment': 4141,
        'taux_serment': 100.0
    }
}
```

### Structure de Données Standardisée
```python
SCHEMA_AVOCAT_LYON = {
    'nom': str,           # Nom de famille
    'prenom': str,        # Prénom(s)
    'email': str,         # Email professionnel
    'telephone': str,     # Téléphone (format français)
    'specialisations': str, # Domaines séparés par ;
    'structure': str,     # Cabinet/Société
    'adresse': str,       # Adresse complète
    'date_serment': str,  # Date prestation serment
    'url': str,           # URL source du profil
    'barreau_id': 'lyon', # Identifiant barreau
    'extraction_date': datetime  # Date d'extraction
}
```

## 🚀 Méthodes d'Intégration

### 1. Import Direct
```python
from lyon.scripts.scraper_barreau_lyon_complet_final import ScraperBarreauLyonComplet

scraper = ScraperBarreauLyonComplet()
resultats = scraper.scraper_complet()
```

### 2. Interface CLI Standardisée
```bash
# Lancement via plateforme
python3 platform.py --barreau lyon --mode production

# Lancement direct
cd lyon/
python3 scripts/scraper_barreau_lyon_complet_final.py
```

### 3. API REST
```python
# Endpoint pour déclencher scraping Lyon
POST /api/scrapers/lyon/run
{
    "mode": "production",
    "enrichissement": true,
    "format_sortie": ["csv", "json"]
}
```

## 📊 Monitoring et Métriques

### KPIs Clés
- **Taux de succès** : 100% (4141/4141 avocats)
- **Couverture email** : 96.3% (3987/4141)
- **Temps d'exécution** : ~3-4 heures
- **Taux d'erreur** : <0.1%

### Alertes Recommandées
```python
ALERTES_LYON = {
    'email_coverage_min': 95.0,  # Alerte si < 95%
    'total_lawyers_min': 4000,   # Alerte si < 4000
    'execution_time_max': 300,   # Alerte si > 5h
    'error_rate_max': 1.0        # Alerte si > 1%
}
```

## 🔧 Configuration Avancée

### Variables d'Environnement
```bash
# Configuration Lyon
LYON_API_BASE=https://www.barreaulyon.com/wp-json/wp/v2/annuaire
LYON_TIMEOUT=30
LYON_RETRY_MAX=3
LYON_PAUSE_MIN=1.0
LYON_PAUSE_MAX=2.0
LYON_HEADLESS=true
```

### Paramètres de Performance
```python
LYON_CONFIG = {
    'batch_size': 50,          # Sauvegarde tous les 50
    'max_workers': 1,          # Pas de parallélisation
    'timeout_request': 30,     # Timeout par requête
    'retry_attempts': 3,       # Tentatives max
    'pause_between': (1, 2),   # Pause aléatoire
    'user_agent': 'Mozilla/5.0...'
}
```

## 📈 Évolutions Futures

### Améliorations Prévues
1. **Cache intelligent** des profils déjà visités
2. **Détection automatique** des changements du site
3. **Enrichissement incrémental** (nouveaux avocats uniquement)
4. **Notifications** en temps réel du statut

### Intégrations Possibles
- **Base de données** centrale PostgreSQL
- **Queue system** Redis pour jobs asynchrones
- **Monitoring** Grafana + InfluxDB
- **Notifications** Slack/Teams

## 🚨 Notes Critiques

### Dépendances Externes
- Site web `barreaulyon.com` opérationnel
- API WordPress `/wp-json/wp/v2/annuaire` stable
- Pas de changement majeur de structure HTML

### Maintenance Recommandée
- **Test mensuel** de la structure API
- **Vérification trimestrielle** des sélecteurs CSS
- **Backup** des données avant chaque mise à jour
- **Log monitoring** pour détecter les anomalies

### Limitations Connues
- **Rate limiting** : Respecter 1-2s entre requêtes
- **Session timeout** : Renouveler la session si nécessaire
- **Captcha** : Aucun détecté, mais surveiller
- **Géo-blocking** : Extraction depuis la France recommandée

---

**Document préparé pour l'intégration dans la plateforme de scraping française**  
**Dernière mise à jour : Mai 2026**