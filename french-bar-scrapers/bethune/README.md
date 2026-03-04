# Scraper Barreau de Béthune

## Description
Scraper complet pour extraire la liste de tous les avocats du Barreau de Béthune.
Site web: https://www.barreaudebethune.com/

## Résultats obtenus
- **125 avocats** extraits avec succès
- **100% de réussite** pour l'extraction des noms complets et villes
- **Spécialisations volontairement omises** (données non fiables)
- Couverture de **30 villes** dans la région

## Utilisation rapide

### Prérequis
```bash
pip3 install selenium beautifulsoup4 lxml
```

### Exécution
```bash
python3 bethune_scraper_final_propre.py
```

### Fichiers générés
- `BETHUNE_FINAL_PROPRE_[nombre]_avocats_[date].csv`
- `BETHUNE_FINAL_PROPRE_[nombre]_avocats_[date].json`
- `BETHUNE_FINAL_PROPRE_[nombre]_avocats_[date]_EMAILS.txt`
- `BETHUNE_FINAL_PROPRE_[nombre]_avocats_[date]_RAPPORT.txt`

## Caractéristiques techniques

### Données extraites
- ✅ **Nom complet** (avec accents préservés)
- ✅ **Prénom et nom séparés**
- ✅ **Année d'inscription** (tous 2019)
- ✅ **Ville d'exercice** (30 villes différentes)
- ✅ **Numéro de téléphone** (identique pour tous - standard du barreau)
- ❌ **Email** (non disponible publiquement)
- ❌ **Spécialisations** (volontairement omises - données non fiables)

### Fonctionnalités
- Mode headless (invisible)
- Gestion automatique des cookies
- Système de backup (toutes les 25 extractions)
- Gestion des noms composés et particules
- Préservation des accents français
- Rapport détaillé avec statistiques

### Architecture technique
- **Selenium WebDriver** pour la navigation
- **BeautifulSoup** pour le parsing HTML
- **Extraction meta-tags** pour données fiables
- **Regex patterns** pour nettoyage des données
- **CSV/JSON export** avec encodage UTF-8

## Répartition géographique (Top 5)
1. **BETHUNE** : 53 avocats (42%)
2. **LENS** : 15 avocats (12%)
3. **LIEVIN** : 9 avocats (7%)
4. **BETHUNE CEDEX** : 7 avocats (6%)
5. **HENIN BEAUMONT** : 5 avocats (4%)

## Décisions techniques importantes

### Spécialisations omises
Les spécialisations détectées étaient génériques ("Avocat à [VILLE]") et ne reflétaient pas les vraies expertises juridiques. Pour maintenir la qualité des données, ce champ est volontairement laissé vide.

### Téléphones identiques
Tous les avocats affichent le même numéro (standard du barreau). Ces données sont conservées pour référence mais ne représentent pas les contacts directs.

## Dernière extraction
- **Date** : 20/02/2026 17:30:16
- **Avocats** : 125
- **Taux de réussite** : 100% (noms et villes)