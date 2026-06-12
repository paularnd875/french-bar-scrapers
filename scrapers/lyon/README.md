# Scraper Barreau de Lyon

## Source
- URL : https://www.barreaulyon.com/annuaire/
- Type : Annuaire officiel du Barreau de Lyon

## Méthode d'énumération

**IMPORTANT** : L'annuaire affiche les avocats en ordre aléatoire à chaque visite. Une pagination simple ne récupère que ~60-65% des fiches. La méthode exhaustive utilise le sitemap WordPress.

### Stratégie recommandée (sitemap)
1. Récupération du sitemap principal : `wp-sitemap.xml`
2. Extraction des sitemaps d'annuaire : `annuaire-sitemap*.xml`
3. Parsing de toutes les URLs de fiches individuelles
4. Scraping séquentiel avec rate-limiting poli

### Fallback (pagination multi-passes)
Si le sitemap échoue, pagination avec plusieurs passes pour compenser l'ordre aléatoire.

## Résultat de référence
- **3989 avocats** (run du 12/06/2026)
- Couverture : exhaustive via sitemap

## Colonnes extraites (18 champs)

| Colonne | Type | Taux de remplissage | Description |
|---------|------|-------------------|-------------|
| nom_complet | string | 100% | Nom et prénom complets |
| nom | string | 99.97% | Nom de famille |
| prenom | string | 100% | Prénom |
| email | string | 99.7% | Email professionnel |
| telephone | string | ~85% | Téléphone direct |
| telephone_structure | string | ~70% | Téléphone du cabinet |
| site_web | string | ~25% | Site web personnel/cabinet |
| structure | string | 99% | Nom du cabinet/structure |
| adresse | string | ~95% | Adresse complète |
| code_postal | string | ~95% | Code postal |
| ville | string | ~95% | Ville |
| case | string | ~90% | Case postale si applicable |
| date_serment | string | 100% | Date de prestation de serment |
| annee_serment | integer | 100% | Année de serment (calculée) |
| specialisations | string | 8% | Certificats de spécialisation (rare) |
| domaines_activite | string | 31% | Domaines d'activité déclarés |
| langues | string | ~15% | Langues pratiquées |
| url_fiche | string | 100% | URL de la fiche individuelle |

## Usage

### Installation des dépendances
```bash
pip install -r ../../requirements.txt
```

### Exécution
```bash
# Run complet (~40 minutes)
python scrape_barreau_lyon.py

# Mode test (1000 fiches)
python scrape_barreau_lyon.py 1000
```

## Fonctionnalités techniques

- **Reprise automatique** : Sauvegarde incrémentale, reprend après interruption
- **Écriture incrémentale** : CSV et JSON mis à jour en temps réel
- **Rate-limiting poli** : 1-2 secondes entre requêtes
- **Rapport de couverture** : Statistiques détaillées en fin de run
- **Gestion d'erreurs** : Retry automatique, logging des échecs

## Conformité RGPD

⚠️ **Données personnelles** : Ce scraper traite des données nominatives publiques.

### Base légale
- **Intérêt légitime** pour la prospection B2B (avocat → avocat)
- Données publiquement accessibles sur site officiel du Barreau

### Obligations
- **Information des personnes** : Informer de l'utilisation de leurs données
- **Droit d'opposition** : Permettre l'opt-out facilement
- **Finalité limitée** : Usage strictement professionnel

### Recommandations
- Tenir registre des traitements (CNIL)
- Implémenter un mécanisme d'opt-out
- Limiter la conservation des données

## Limites connues

1. **Fiche sans nom** : 1 fiche avec nom non capitalisé côté site (parsing défaillant)
2. **Emails partagés** : Certains associés partagent la même adresse email
   → Dédupliquer avant envoi de masse
3. **Certificats rares** : Seulement 8% ont des spécialisations certifiées
4. **Rate-limiting** : Scraping lent pour préserver le serveur cible

## Structure des fichiers générés

```
LYON_SCRAPED_YYYY-MM-DD_HHMMSS.csv    # Format CSV standard
LYON_SCRAPED_YYYY-MM-DD_HHMMSS.json   # Format JSON avec métadonnées
```

## Maintenance

- **Vérifier sitemaps** : Le format des sitemaps WordPress peut évoluer
- **Surveiller structure** : Les champs de l'annuaire peuvent changer
- **Tester régulièrement** : Run test mensuel pour détecter les changements