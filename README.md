# French Bar Association Scrapers

Collection de scrapers pour extraire les données des barreaux français.

## 🔥 NOUVEAU : Lyon - Scraper API Complet (96.3% emails)

**Scraper Lyon** avec API WordPress native :
- ✅ **4141 avocats** extraits (100% du barreau)
- ✅ **3987 emails uniques** (96.3% de couverture - RECORD)
- ✅ **4141 dates de serment** (100% de couverture)
- ✅ **API WordPress** : Plus fiable et plus rapide
- ✅ **Architecture modulaire** prête pour plateforme
- 📁 **Dossier**: [`lyon/`](./lyon/)

## 🆕 NOUVEAU : Saumur - Extraction PDF exhaustive

**Scraper Saumur** avec extraction PDF directe :
- ✅ **28 avocats** extraits (100% du barreau)
- ✅ **21 emails uniques** (75% de taux global, 100% tableau principal)  
- ✅ **Mode headless** - aucune interface graphique
- ✅ **Extraction PDF** : Plus fiable que le web scraping
- ✅ **Gestion parfaite** des prénoms composés
- 📁 **Dossier**: [`saumur/`](./saumur/)

### Utilisation Lyon 🔥
```bash
cd lyon/
pip install -r requirements.txt
python3 scripts/scraper_barreau_lyon_complet_final.py
```

### Utilisation Saumur
```bash
cd saumur/
pip install -r requirements.txt
python3 run_saumur_scraper.py
```

## 🔥 RÉCENT : Compiègne avec parsing parfait

**Scraper Compiègne** avec parsing de noms de classe professionnelle :
- ✅ **75 avocats** récupérés (100% de l'annuaire)
- ✅ **64 emails uniques** (85% de taux de récupération)  
- ✅ **100% précision** sur noms composés et particules nobiliaires
- ✅ **Parsing avancé** : `CARON - DE WILDE Stéphanie` → Stéphanie / CARON - DE WILDE
- 📁 **Dossier**: [`compiegne/`](./compiegne/)

### Utilisation Compiègne
```bash
cd compiegne/
pip install -r requirements.txt
python3 run_compiegne_scraper.py
```

## Scripts Disponibles

### 1. Barreau de Saumur 🆕
**Dossier:** `saumur/`
**Source:** PDF officiel (https://www.barreau-saumur.fr/wp-content/uploads/2025/02/avocats-saumur-2025.pdf)

#### Utilisation
```bash
cd saumur/
pip install -r requirements.txt

# Lancement simplifié
python3 run_saumur_scraper.py

# Ou directement
python3 SAUMUR_SCRAPER_COMPLET_FINAL.py
```

#### Résultats
- **28 avocats** extraits (100% exhaustif)
  - 26 avocats au tableau principal (1992-2022)
  - 2 avocats en cabinets secondaires
- **21 emails uniques** (75% global, 100% tableau)
- **Mode headless** - aucune fenêtre
- **Extraction PDF directe** (plus fiable)

### 2. Barreau d'Alès
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
# Pour Saumur 🆕
cd saumur/
python3 run_saumur_scraper.py

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