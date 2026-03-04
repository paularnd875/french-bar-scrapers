# French Bar Scrapers

Collection de scrapers automatisés pour l'extraction des données des barreaux d'avocats français.

## 🎯 Objectif

Automatiser la collecte des informations publiques des avocats français depuis les sites officiels des barreaux.

## 📊 Barreaux supportés

| Barreau | Statut | Avocats | Lien |
|---------|---------|---------|------|
| **Aveyron** | ✅ Opérationnel | ~72 | [aveyron/](./aveyron/) |

## 🚀 Installation rapide

```bash
git clone https://github.com/paularnd875/french-bar-scrapers.git
cd french-bar-scrapers/aveyron
pip install -r requirements.txt
python aveyron_scraper.py production
```

## 🔧 Fonctionnalités communes

- ✅ **Mode test/production** : Validation avant extraction complète
- ✅ **Formats multiples** : CSV, JSON
- ✅ **Respect des sites** : Pauses entre requêtes
- ✅ **Mode headless** : Extraction invisible
- ✅ **Gestion d'erreurs** : Continuation en cas d'échec

## 📊 Données extraites

| Champ | Description |
|-------|-------------|
| `nom_famille` | Nom de famille |
| `prenom` | Prénom |
| `telephone` | Téléphone principal |
| `adresse` | Adresse complète |
| `ville` | Ville d'exercice |
| `annee_inscription` | Année de serment |
| `statut` | Titre/fonction |

## 🎯 Utilisation

### Extraction complète
```bash
cd aveyron/
python aveyron_scraper.py production
```

### Test sur échantillon
```bash
python aveyron_scraper.py test
```

## 📄 Licence

Utilisation respectueuse des données publiques conformément aux CGU des sites sources.

---

**Dernière mise à jour** : Février 2026  
**Version** : 1.0  
**Statut** : ✅ Production ready
