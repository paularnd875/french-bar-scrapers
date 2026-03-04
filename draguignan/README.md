# Scraper Barreau de Draguignan

## Description
Ce scraper extrait toutes les informations des avocats du Barreau de Draguignan depuis le site officiel https://www.avocazur.com/fr/annuaire/

## Fonctionnalités
- ✅ **Extraction complète** : 234 avocats avec toutes leurs informations
- ✅ **Parsing intelligent** : Séparation automatique noms/prénoms (92.7% de réussite)
- ✅ **Données complètes** : emails, téléphones, adresses, cabinets, spécialisations
- ✅ **Sources traçables** : URL de chaque fiche avocat
- ✅ **Spécialisations réelles** : Extraction des vraies spécialisations (pas que "généraliste")
- ✅ **Déduplication** : Emails uniques, pas de doublons

## Utilisation

### Installation des dépendances
```bash
pip install selenium beautifulsoup4 pandas
```

### Lancement

#### Mode test (lettres A et B seulement)
```bash
python3 draguignan_scraper.py test
```

#### Mode production complet (toutes les lettres A-Z)
```bash
python3 draguignan_scraper.py production
```

#### Mode headless (sans interface)
```bash
python3 draguignan_scraper.py production --headless
```

## Fichiers générés

Le scraper génère automatiquement 4 fichiers :

1. **CSV** : `DRAGUIGNAN_[MODE]_CORRECTED_[NOMBRE]avocats_[TIMESTAMP].csv`
2. **JSON** : `DRAGUIGNAN_[MODE]_CORRECTED_[NOMBRE]avocats_[TIMESTAMP].json` 
3. **Emails** : `DRAGUIGNAN_[MODE]_CORRECTED_EMAILS_[NOMBRE]emails_[TIMESTAMP].txt`
4. **Rapport** : `DRAGUIGNAN_[MODE]_CORRECTED_RAPPORT_[TIMESTAMP].txt`

## Colonnes du CSV

| Colonne | Description |
|---------|-------------|
| `nom` | Nom de famille |
| `prenom` | Prénom(s) |
| `nom_complet` | Nom complet |
| `cabinet` | Cabinet/structure juridique |
| `email` | Adresse email |
| `telephone` | Numéro de téléphone |
| `fax` | Numéro de fax |
| `adresse` | Adresse postale complète |
| `ville` | Ville |
| `code_postal` | Code postal |
| `annee_inscription` | Année d'inscription au barreau |
| `specialisation` | Spécialisation(s) juridique(s) |
| `competences` | Domaines de compétences |
| `source` | URL de la fiche source |

## Statistiques récentes (production)

- **234 avocats** extraits
- **228 emails uniques** (97.4% de couverture)
- **92.7% noms/prénoms séparés** correctement
- **100% sources URL** ajoutées
- **9 spécialisations réelles** identifiées

## Améliorations apportées

1. **Parsing noms/prénoms avancé** : Gestion des noms composés, particules, tirets
2. **Extraction spécialisations** : Récupération des vraies spécialisations depuis les fiches détaillées
3. **Sources traçables** : Ajout URL de chaque fiche avocat
4. **Déduplication complète** : Suppression des doublons d'emails
5. **Robustesse** : Gestion des erreurs et retry automatique

## Notes techniques

- **Site source** : https://www.avocazur.com/fr/annuaire/
- **Navigation alphabétique** : Le scraper parcourt automatiquement toutes les lettres A-Z
- **Extraction détaillée** : Clic sur chaque fiche pour récupérer les détails complets
- **Format de sortie** : CSV, JSON et TXT pour maximum de compatibilité

## Maintenance

Pour mettre à jour la base :
1. Relancer le scraper en mode production
2. Comparer avec les résultats précédents
3. Les fichiers sont horodatés automatiquement

---
*Dernière mise à jour : Mars 2026*
*Développé avec corrections avancées de parsing et extraction complète*