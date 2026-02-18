# Nancy Bar Association Scraper

Scripts pour l'extraction complète des avocats du Barreau de Nancy.

## 🎯 Résultats

- **274 avocats extraits** (100% complet)
- **272 dates de prestation** (99.3% de succès)  
- **274 emails récupérés** (100% de succès)
- **Noms et prénoms correctement séparés**
- **URLs sources valides pour chaque avocat**

## 📁 Scripts

### Scripts principaux

1. **`nancy_scraper_273_FINAL.py`** - Script principal pour extraire la liste complète des avocats
   - Extrait 274 avocats depuis https://avocats-nancy.com/annuaire-pro/
   - Navigation automatique avec "Charger la suite" 
   - Mode headless supporté
   - Gestion des cartes cachées

2. **`nancy_portfolio_scraper_COMPLET.py`** - Extraction détaillée des informations individuelles
   - Visite chaque fiche avocat pour extraire les détails complets
   - Emails, téléphones, adresses, spécialités
   - Séparation correcte des noms/prénoms composés
   - Export CSV et JSON

3. **`nancy_dates_prestation_extractor.py`** - Extraction spécialisée des dates de prestation de serment
   - 4 stratégies d'extraction pour maximum de succès
   - Mode non-headless pour garantir le chargement complet
   - Merge avec les données existantes

### Script de test

4. **`nancy_test_prestation_dates.py`** - Validation de l'extraction des dates
   - Test sur 5 échantillons
   - Validation des patterns d'extraction

## 🚀 Utilisation

### Extraction complète (recommandée)

```bash
# 1. Extraire la liste complète des avocats
python3 nancy_scraper_273_FINAL.py

# 2. Extraire les détails individuels 
python3 nancy_portfolio_scraper_COMPLET.py

# 3. Extraire les dates de prestation manquantes
python3 nancy_dates_prestation_extractor.py
```

### Test rapide

```bash
# Tester l'extraction des dates sur 5 échantillons
python3 nancy_test_prestation_dates.py
```

## 📊 Structure des données

### Champs extraits

- `nom` - Nom complet
- `prenom` - Prénom 
- `nom_famille` - Nom de famille
- `email` - Adresse email
- `telephone` - Numéro principal
- `telephone_2` - Numéro secondaire
- `adresse` - Adresse
- `ville` - Ville
- `code_postal` - Code postal
- `annee_inscription` - Année d'inscription au barreau
- `date_prestation_serment` - Date complète de prestation
- `specialites` - Liste des spécialités
- `cabinet` - Nom du cabinet
- `site_web` - Site web
- `url` - URL de la fiche source

### Formats de sortie

- **JSON** : Données structurées avec listes
- **CSV** : Export Excel avec séparateurs ";" pour les listes

## 🔧 Technique

### Défis résolus

1. **Anti-bot detection** - Contournement avec user agents et pauses
2. **Cartes cachées** - Activation des `.wpgb-card-hidden`
3. **Navigation pagination** - Clic automatique sur "Charger la suite"
4. **Noms composés** - Parsing intelligent (ex: "DAL MOLIN, Georges")
5. **Dates headless** - Script spécialisé en mode visible

### Sélecteurs CSS utilisés

```css
.wpgb-card                    /* Cartes avocats */
a[href*='/portfolio/']        /* Liens vers fiches */
p.has-text-align-right        /* Dates de prestation */
```

## 📈 Performance

- **Temps total** : ~15 minutes pour 274 avocats
- **Taux de succès emails** : 100%
- **Taux de succès dates** : 99.3%
- **Mode** : Headless supporté (sauf extraction dates)

## 🔄 Mise à jour

Pour relancer une extraction complète :

```bash
python3 nancy_portfolio_scraper_COMPLET.py
python3 nancy_dates_prestation_extractor.py
```

Les fichiers générés auront un timestamp unique pour éviter les écrasements.