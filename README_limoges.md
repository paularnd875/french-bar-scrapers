# Scraper Barreau de Limoges

## Description
Script complet pour extraire tous les avocats du Barreau de Limoges avec leurs informations détaillées.

## Fonctionnalités
- ✅ **Extraction complète** : 194 avocats (100% du barreau)
- ✅ **Données complètes** : prénom, nom, email, année d'inscription, spécialisations, structure, téléphone, adresse, URL source
- ✅ **Consolidation automatique** avec déduplication
- ✅ **Mode headless** optimisé
- ✅ **Gestion d'erreurs** robuste

## Usage

### Installation des dépendances
```bash
pip install selenium beautifulsoup4 requests
```

### Lancement
```bash
python3 limoges_scraper_complet.py
```

## Résultats
- **Fichier de sortie** : `LIMOGES_COMPLET_194_avocats_YYYYMMDD_HHMMSS.csv`
- **Format** : CSV avec en-têtes
- **Encodage** : UTF-8

## Structure des données
| Champ | Description | Taux de remplissage |
|-------|-------------|-------------------|
| prenom | Prénom de l'avocat | 100% |
| nom | Nom de l'avocat | 100% |
| email | Adresse email | 100% |
| annee_inscription | Année d'inscription au barreau | 100% |
| specialisations | Domaines de spécialisation | 12% (24/194) |
| structure | Nom du cabinet/structure | Variable |
| telephone | Numéro de téléphone | 97% (189/194) |
| adresse | Adresse complète | 92% (179/194) |
| source_url | URL du profil pour vérification | 100% |

## Exemple de sortie
```csv
prenom,nom,email,annee_inscription,specialisations,structure,telephone,adresse,source_url
Jean-Philippe,BOURRA,jphbourra@wanadoo.fr,2002,Droit du dommage corporel,,09 62 69 14 04,28 Avenue Du Midi  87000 LIMOGES,https://www.avocats-limoges.org/cb-profile/570-jbourra.html
Josyane,ANDRIEU-FILLIOL,cabinetandrieu-filliol@wanadoo.fr,1975,"Droit de la famille, des personnes, et de leur patrimoine, Droit pénal",,05 55 32 08 30,9 Place D'Aine  87000 LIMOGES,https://www.avocats-limoges.org/cb-profile/553-jandrieu-filliol.html
```

## Performance
- **Temps d'exécution** : ~5 minutes
- **Pages traitées** : 7 pages (30+30+30+30+30+30+14 avocats)
- **Taux de succès** : 100%

## Site source
- **URL** : https://www.avocats-limoges.org/
- **Structure** : Pagination avec 30 avocats par page
- **Dernière extraction** : 194 avocats (février 2026)

## Notes techniques
- Utilise Selenium WebDriver avec Chrome headless
- Extraction page par page pour une meilleure robustesse
- Déduplication automatique par URL source
- Gestion des timeouts et erreurs réseau
- Extraction des données par regex et sélecteurs CSS

## Maintenance
Pour une utilisation future, le script s'adapte automatiquement au nombre d'avocats et à la structure des pages. Aucune modification n'est nécessaire sauf changement majeur du site web.