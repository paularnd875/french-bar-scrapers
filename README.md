# French Bar Association Scrapers

Collection de scrapers pour extraire les données des barreaux français.

## Scripts Disponibles

### 1. Barreau d'Alès
**Fichier:** `ales_scraper_final.py`
**Site cible:** https://www.barreau-ales.fr/fr/annuaire/avocats-barreau-ales/

#### Utilisation
```bash
# Mode test (20 premiers avocats)
python3 ales_scraper_final.py

# Mode production (tous les avocats)
python3 ales_scraper_final.py production
```

#### Résultats
- **50 avocats** extraits avec succès
- **100% d'emails** récupérés
- Parsing correct des noms composés
- Navigation automatique sur 3 pages

### 2. Barreau des Alpes de Haute-Provence
**Fichier:** `alpes_hp_scraper_final.py`
**Site cible:** https://www.avocats04.fr/le-barreau/annuaire-des-avocats.htm

#### Utilisation
```bash
# Mode test (20 premiers avocats)
python3 alpes_hp_scraper_final.py

# Mode production (tous les avocats)
python3 alpes_hp_scraper_final.py production
```

#### Résultats
- **121 pages** découvertes
- Navigation automatique et extraction détaillée
- Extraction des détails individuels pour chaque avocat

### 3. Barreau de Villefranche-sur-Saône  
**Dossier:** `villefranche-sur-saone/`
**Site cible:** https://www.avocatsvillefranche.fr/annuaire/

#### Utilisation
```bash
# Mode test (20 avocats)
python3 VILLEFRANCHE_SCRAPER_AMELIORE.py

# Mode production complet (60 avocats)
python3 LANCER_PRODUCTION_VILLEFRANCHE.py

# Ou directement
python3 VILLEFRANCHE_SCRAPER_PRODUCTION.py
```

#### Résultats
- **60 avocats** extraits (100% de l'annuaire)
- **44 emails uniques** (100% de couverture)
- **57 téléphones** (95% de couverture)
- Sauvegardes automatiques tous les 25 avocats
- Mode headless optimisé

### 4. Barreau de Nevers
**Fichier:** `nevers_scraper_complete.py`
**Site cible:** https://www.avocats-nevers.org/fr/annuaire/annuaire-avocats.html

#### Utilisation
```bash
python3 nevers_scraper_complete.py
```

#### Résultats
- **49 avocats** extraits (100% de l'annuaire)
- **49 emails** décodés (100% de réussite)
- Décodage JavaScript des emails obfusqués

## Prérequis

```bash
pip install selenium beautifulsoup4 requests lxml pandas
```

## Fonctionnalités Communes

- ✅ Acceptation automatique des cookies
- ✅ Navigation multi-pages automatique
- ✅ Extraction des détails individuels
- ✅ Parsing intelligent des noms composés
- ✅ Mode headless pour production
- ✅ Export CSV, JSON et TXT
- ✅ Rapports détaillés d'extraction
- ✅ Gestion d'erreurs robuste

## Champs Extraits

- **Prénom/Nom** (parsing intelligent)
- **Email** (extraction prioritaire)
- **Téléphone** (si disponible)
- **Année d'inscription** (si disponible)
- **Spécialisations/Compétences** (si disponible)
- **Structure/Cabinet** (si disponible)
- **URL source**

## Mise à Jour

Pour mettre à jour vos données, il suffit de relancer le script correspondant :

```bash
# Pour Alès
python3 ales_scraper_final.py production

# Pour Alpes de Haute-Provence
python3 alpes_hp_scraper_final.py production

# Pour Villefranche-sur-Saône
cd villefranche-sur-saone/
python3 VILLEFRANCHE_SCRAPER_PRODUCTION.py

# Pour Nevers
python3 nevers_scraper_complete.py
```

Les fichiers de résultats sont horodatés automatiquement.

## 👨‍💻 Auteur

Développé par Claude (Anthropic) - Février-Mars 2026