# Scraper Barreau des Alpes de Haute-Provence

## Description
Scraper complet pour l'annuaire du Barreau des Alpes de Haute-Provence (04).

**URL Source:** https://www.avocats04.fr/le-barreau/annuaire-des-avocats.htm

## Scripts Disponibles

### 1. ALPESDEHAUTEPROVENCE_COMPLET_AVEC_DATES.py (RECOMMANDÉ)
**Version finale complète** - Approche hybride optimisée

**Fonctionnalités:**
- ✅ **Phase 1:** Extraction rapide des informations de base depuis l'annuaire principal
- ✅ **Phase 2:** Visite individuelle des pages d'avocats pour récupérer les années d'inscription
- ✅ Gestion automatique des cookies
- ✅ Mode headless (pas d'interference avec votre travail)
- ✅ Extraction complète : nom, prénom, adresse, téléphone, spécialités, année d'inscription
- ✅ Gestion des noms composés
- ✅ Sauvegarde en CSV, JSON et rapport détaillé
- ✅ Mode test (15 avocats) et production (tous)

**Résultats typiques:**
- 57 avocats traités (100%)
- 47 téléphones (82.5%)  
- 56 adresses (98.2%)
- 12 années inscription (21.1%)
- 0 emails (non publiques sur ce site)

### 2. ALPESDEHAUTEPROVENCE_DIRECT_EXTRACTION.py (RAPIDE)
**Version directe** - Extraction uniquement depuis la page d'annuaire

**Fonctionnalités:**
- ✅ Extraction rapide depuis la page principale uniquement
- ✅ Pas de navigation vers les pages individuelles
- ✅ Bon pour les mises à jour rapides
- ❌ Pas d'années d'inscription (nécessite pages individuelles)

## Installation

### Prérequis
```bash
pip install selenium beautifulsoup4 pandas requests
```

### Chrome Driver
Assurez-vous d'avoir ChromeDriver installé et dans le PATH.

## Utilisation

### Lancement Rapide (Production)
```bash
cd alpes-de-haute-provence
python3 ALPESDEHAUTEPROVENCE_COMPLET_AVEC_DATES.py
```

### Mode Test (15 avocats)
Modifiez la ligne 366 dans le script :
```python
choice = "test"  # au lieu de "production"
```

## Fichiers Générés

### CSV Principal
`ALPES_COMPLET_DATES_PRODUCTION_XXavocats_YYYYMMDD_HHMMSS.csv`

**Colonnes:**
- `prenom` - Prénom
- `nom` - Nom de famille  
- `nom_complet` - Nom complet avec civilité
- `annee_inscription` - Année de prestation de serment
- `specialisations` - Spécialités/fonctions
- `adresse` - Adresse complète
- `telephone` - Numéro de téléphone
- `email` - Email (généralement vide sur ce site)
- `source_url` - URL de la page individuelle

### Autres Fichiers
- **JSON:** Même données au format JSON
- **Rapport:** Statistiques détaillées et exemples d'avocats extraits
- **Emails:** Fichier texte avec uniquement les emails (si disponibles)

## Caractéristiques Techniques

### Structure du Site
- Site dynamique nécessitant JavaScript/Selenium
- Fiches avocats dans des divs `.annuaireFicheMini`
- Structure CSS spécifique :
  - `.anfiche_civ` - Civilité (Madame/Monsieur)
  - `.anfiche_prenom` - Prénom
  - `.anfiche_nom` - Nom
  - `.coordonnees` - Informations de contact
  - `.annuaireFicheDateSerment` - Année d'inscription (pages individuelles)

### Gestion des Erreurs
- Retry automatique en cas d'échec de chargement
- Backup des données pendant l'extraction
- Debug HTML sauvegardé pour analyse
- Pauses aléatoires entre les requêtes

### Performance
- **Direct (sans dates):** ~30 secondes pour tous les avocats
- **Complet (avec dates):** ~2-3 minutes pour tous les avocats
- Optimisé pour minimiser la charge serveur

## Notes Importantes

1. **Emails:** Ce site ne publie généralement pas d'emails dans l'annuaire public
2. **Années d'inscription:** Seulement ~20% des avocats ont cette information visible
3. **Rate Limiting:** Pauses automatiques pour éviter la surcharge du serveur
4. **Cookies:** Acceptation automatique des cookies de consentement

## Maintenance

### Mise à Jour
Pour mettre à jour vos données :
```bash
cd /chemin/vers/french-bar-scrapers/alpes-de-haute-provence
python3 ALPESDEHAUTEPROVENCE_COMPLET_AVEC_DATES.py
```

### Dépannage
- Si le script plante, vérifiez que ChromeDriver est bien installé
- En cas d'erreur 0 avocats trouvés, le site a peut-être changé de structure
- Consultez les fichiers debug_*.html générés pour analyser la structure

## Dernière Mise à Jour
24 février 2026 - Version finale validée et testée