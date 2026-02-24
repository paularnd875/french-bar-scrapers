# Guide d'Utilisation - Scraper Barreau d'Aix-en-Provence

## 🎯 Vue d'ensemble

Ce guide vous accompagne pour utiliser le scraper du Barreau d'Aix-en-Provence, testé et validé en février 2026 avec un taux de succès exceptionnel.

## ⚡ Démarrage rapide

### 1. Pré-requis

- **Python 3.8+** installé
- **Chrome** ou **Chromium** installé
- **Connexion internet** stable

### 2. Installation

```bash
# Cloner le repository
git clone https://github.com/paularnd875/french-bar-scrapers.git

# Aller dans le dossier Aix-en-Provence
cd french-bar-scrapers/aix-en-provence

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Premier test (recommandé)

```bash
# Test avec 5 avocats pour valider l'installation
python3 test_scraper.py
```

**Résultat attendu :**
- Durée : ~30 secondes
- 5 avocats extraits avec emails, téléphones, adresses
- Fichiers créés : `AIX_TEST_AMELIORE_5_avocats_[timestamp].csv`

### 4. Extraction complète

```bash
# Production complète - 940 avocats
python3 aix_scraper_production.py
```

**Résultat attendu :**
- Durée : ~50 minutes
- 940 avocats avec toutes les données
- Fichiers créés : `AIX_FINAL_COMPLET_940_avocats_[timestamp].csv`

## 📊 Données extraites

### Informations de base (100% des avocats)
- **Prénom et nom** (séparés intelligemment)
- **Nom complet** original
- **URL de la fiche** individuelle
- **Coordonnées GPS** (latitude, longitude)

### Informations détaillées (~99% des avocats)
- **Email professionnel** (99.9% de succès)
- **Téléphone** (100% de succès)
- **Adresse complète** (100% de succès)
- **Date de serment** complète (100% de succès)
- **Année d'inscription** au barreau (100% de succès)

### Informations complémentaires (~25% des avocats)
- **Spécialisations juridiques** (visibles sur l'annuaire)
- **Domaines d'activité**

## 📁 Fichiers générés

### Format des noms de fichiers
```
AIX_[TYPE]_[NOMBRE]_avocats_[TIMESTAMP].[EXTENSION]
```

### Types de fichiers

1. **CSV principal** : Base de données complète
   - `AIX_FINAL_COMPLET_940_avocats_20260224_135753.csv`

2. **Emails séparés** : Liste pure d'emails
   - `AIX_FINAL_COMPLET_EMAILS_SEULEMENT_20260224_135753.txt`

3. **JSON** : Format structuré
   - `AIX_FINAL_COMPLET_940_avocats_20260224_135753.json`

4. **Rapport** : Statistiques et résumé
   - `AIX_FINAL_COMPLET_RAPPORT_COMPLET_20260224_135753.txt`

### Sauvegardes intermédiaires

Le script sauvegarde automatiquement tous les 100 avocats :
- `AIX_PARTIEL_100_avocats_[timestamp].csv`
- `AIX_PARTIEL_200_avocats_[timestamp].csv`
- etc.

## 🔧 Options avancées

### Mode debug

Pour voir plus de détails pendant l'extraction, modifier dans le script :

```python
# Ligne ~50 dans aix_scraper_production.py
driver = setup_driver(headless=False)  # Voir le navigateur
```

### Personnaliser les pauses

```python
# Ligne ~350 environ
time.sleep(2)  # Changer pour 1 ou 3 secondes
```

### Modifier le batch size

```python
# Ligne ~330 environ
batch_size = 20  # Changer pour 10 ou 30
```

## 🛠️ Résolution de problèmes

### Erreur "ChromeDriver not found"

```bash
# Sur macOS
brew install chromedriver

# Sur Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# Sur Windows
# Télécharger depuis https://chromedriver.chromium.org/
```

### Erreur "Module not found"

```bash
# Réinstaller les dépendances
pip install --upgrade -r requirements.txt
```

### Extraction qui s'arrête

Le script est robuste avec sauvegardes automatiques. En cas d'arrêt :

1. Vérifiez les fichiers `AIX_PARTIEL_*` créés
2. Le dernier fichier contient les données déjà extraites
3. Relancez le script, il recommencera au début

### Performance lente

- Vérifiez votre connexion internet
- Augmentez les délais : `time.sleep(3)`
- Réduisez le batch_size à 10

## 📈 Optimisation

### Pour une extraction plus rapide

```python
# Réduire les délais (attention au serveur)
time.sleep(1)  # Au lieu de 2

# Augmenter le batch size
batch_size = 30  # Au lieu de 20
```

### Pour plus de robustesse

```python
# Augmenter les délais
time.sleep(3)  # Au lieu de 2

# Réduire le batch size
batch_size = 10  # Au lieu de 20
```

## 📊 Statistiques de référence

### Extraction du 24/02/2026
- **Durée totale** : 49 minutes 45 secondes
- **Avocats extraits** : 940/940 (100%)
- **Emails récupérés** : 939/940 (99.9%)
- **Téléphones** : 940/940 (100%)
- **Adresses** : 940/940 (100%)
- **Dates de serment** : 940/940 (100%)

### Top spécialisations trouvées
1. Droit des affaires : 55 avocats
2. Droit du travail : 47 avocats
3. Droit pénal : 46 avocats
4. Droit de la famille : 39 avocats
5. Dommages corporels : 27 avocats

## 🔄 Mise à jour des données

Pour mettre à jour votre base :

1. **Relancer l'extraction** : `python3 aix_scraper_production.py`
2. **Comparer les totaux** dans les rapports
3. **Identifier les nouveaux avocats** en comparant les CSV
4. **Merger si nécessaire** avec vos données existantes

## 💡 Conseils d'utilisation

### Planification automatique

```bash
# Crontab pour extraction mensuelle
0 2 1 * * cd /path/to/french-bar-scrapers/aix-en-provence && python3 aix_scraper_production.py
```

### Surveillance

```bash
# Suivre les logs en temps réel
tail -f AIX_*.txt
```

### Validation des données

```bash
# Compter les emails uniques
sort AIX_FINAL_COMPLET_EMAILS_*.txt | uniq | wc -l

# Vérifier la structure CSV
head -5 AIX_FINAL_COMPLET_*_avocats_*.csv
```

---

**🎯 Support** : Ce scraper a été développé et testé avec succès. Pour toute question, référez-vous aux fichiers de logs et rapports générés.