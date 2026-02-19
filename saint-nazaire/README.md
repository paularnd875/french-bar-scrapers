# Scraper Barreau de Saint-Nazaire

Ce scraper extrait automatiquement tous les avocats du Barreau de Saint-Nazaire depuis leur annuaire en ligne.

## 🎯 Données extraites

- **Prénom et nom** (correctement séparés)
- **Année d'inscription au barreau** (date de serment)
- **Email** (extrait depuis les liens mailto)
- **Téléphone**
- **Adresse**
- **Spécialisations juridiques** (quand disponibles)
- **Structure/cabinet**
- **Lien source** pour vérification

## 📊 Résultats

- **~87 avocats** extraits (100% du barreau)
- **~85 emails uniques** récupérés (98% de succès)
- **Format CSV propre** : une ligne par avocat
- **Données nettoyées** : pas d'informations parasites

## 🚀 Installation et utilisation

### Prérequis

```bash
pip install -r requirements.txt
```

Vous devez également avoir Chrome installé sur votre système.

### Exécution

```bash
python scraper.py
```

Le script fonctionne en mode **headless** (sans interface visuelle) par défaut.

## 📁 Fichiers générés

Le script génère automatiquement :

- `SAINTNAZAIRE_FINAL_XX_avocats_YYYYMMDD_HHMMSS.csv` - Données principales
- `SAINTNAZAIRE_FINAL_XX_avocats_YYYYMMDD_HHMMSS.json` - Format JSON
- `SAINTNAZAIRE_FINAL_EMAILS_YYYYMMDD_HHMMSS.txt` - Liste des emails uniquement
- `SAINTNAZAIRE_FINAL_RAPPORT_YYYYMMDD_HHMMSS.txt` - Rapport détaillé

## ⚙️ Fonctionnalités

- ✅ **Mode headless** - Pas d'interface visuelle
- ✅ **Acceptation automatique des cookies**
- ✅ **Navigation sur toutes les pages** (~11 pages)
- ✅ **Extraction emails via mailto**
- ✅ **Gestion des noms composés**
- ✅ **Sauvegardes automatiques** (tous les 20 avocats)
- ✅ **Gestion des erreurs et continuation**
- ✅ **Données nettoyées** (pas de retours à la ligne parasites)

## 🔧 Configuration

Pour modifier le comportement :

```python
# Mode visible (pour déboguer)
scraper = SaintNazaireScraper(headless=False)

# Modifier la fréquence de sauvegarde
backup_frequency = 10  # Sauvegarde tous les 10 avocats
```

## 📝 Structure des données CSV

```
prenom,nom,annee_inscription,specialisations,competences,activites_dominantes,structure,email,telephone,adresse,source
```

Exemple :
```
Julia,GARCIA-DUBRAY,2005,,,,,contact@jgd-avocat.fr,02.52.41.08.62,90 Avenue Albert de Mun - 44600 Saint-Nazaire,https://www.barreau-saintnazaire.fr/avocat/garcia-dubray-julia/
```

## 🎯 Site source

- **URL** : https://www.barreau-saintnazaire.fr/les-avocats/lannuaire-des-avocats/
- **Pages** : ~11 pages d'annuaire
- **Structure** : WordPress avec pagination

## ⏱️ Temps d'exécution

- **Durée totale** : ~15-20 minutes
- **Rythme** : ~1 seconde par avocat
- **Sauvegardes** : Automatiques tous les 20 avocats

## 🐛 Dépannage

### Problèmes courants

1. **ChromeDriver non trouvé**
   ```bash
   # Sur macOS avec Homebrew
   brew install chromedriver
   ```

2. **Timeout lors du scraping**
   - Vérifier la connexion internet
   - Le site peut être temporairement lent

3. **Moins d'avocats récupérés**
   - Le site peut avoir changé de structure
   - Vérifier les logs pour les erreurs de pages

### Logs

Le script affiche en temps réel :
- Progression par page et par avocat
- Emails trouvés
- Sauvegardes automatiques
- Erreurs éventuelles

## 📅 Dernière mise à jour

**Février 2026** - Script testé et fonctionnel

## ✅ Tests effectués

- ✅ Extraction complète des 87 avocats
- ✅ Récupération de 85 emails uniques (98%)
- ✅ Parsing correct des noms composés
- ✅ CSV sans erreurs de format
- ✅ Spécialisations proprement extraites
- ✅ Mode headless stable

---

*Développé avec Claude Code pour l'extraction automatisée des données des barreaux français.*