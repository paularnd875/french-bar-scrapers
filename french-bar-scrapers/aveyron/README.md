# Scraper Barreau d'Aveyron

Scraper automatisé pour l'extraction des données des avocats du Barreau d'Aveyron.

## 🎯 Fonctionnalités

- ✅ **Extraction complète** : Tous les avocats du barreau (~72)
- ✅ **Données détaillées** : Nom, téléphone, adresse, année de serment
- ✅ **Correction des accents** : Gestion automatique des URLs avec %
- ✅ **Formats multiples** : CSV et JSON
- ✅ **Mode test** : Validation sur échantillon

## 🚀 Utilisation

### Installation
```bash
pip install -r requirements.txt
```

### Mode production (tous les avocats)
```bash
python aveyron_scraper.py production
```

### Mode test (échantillon)
```bash
python aveyron_scraper.py test
```

## 📊 Données extraites

| Champ | Description |
|-------|-------------|
| `nom_famille` | Nom de famille |
| `prenom` | Prénom |
| `telephone` | Numéro de téléphone |
| `fax` | Numéro de fax |
| `adresse` | Adresse complète |
| `ville` | Ville d'exercice |
| `annee_inscription` | Année de serment |
| `statut` | Titre professionnel |

## 🔧 Configuration

Le scraper utilise des sélecteurs CSS spécifiques au site Wix :

```python
SELECTEURS_WIX = {
    'statut': '#comp-kezp4zjj',        # Titre professionnel
    'annee': '#comp-kezp5i4q',         # Année de serment
    'telephone': '#comp-kezpcw70',     # Téléphone
    'fax': '#comp-kezph14q',          # Fax
    'adresse': '#comp-kezq0cbl'       # Adresse
}
```

## 📄 Fichiers générés

- `AVEYRON_PRODUCTION_XXavocats_YYYYMMDD_HHMMSS.csv`
- `AVEYRON_PRODUCTION_XXavocats_YYYYMMDD_HHMMSS.json`

**Dernière mise à jour** : Février 2026  
**Statut** : ✅ Fonctionnel