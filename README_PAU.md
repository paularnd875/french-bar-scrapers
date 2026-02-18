# Barreau de Pau - Scraper

Ce script permet d'extraire toutes les informations des avocats du Barreau de Pau depuis leur site officiel.

## Site source
- **URL**: https://avocats-pau.fr/avocat/
- **Nombre d'avocats**: ~290

## Fonctionnalités

### Données extraites
- Prénom (séparé)
- Nom (séparé) 
- Email
- Téléphone
- Adresse
- Année d'inscription au barreau
- Spécialisations
- Structure/Cabinet
- URL source pour vérification

### Particularités techniques
- **Extraction robuste des noms**: Gestion des noms composés avec "DIT" (ex: "MASSOU DIT LABAQUERE Maripierre")
- **Nettoyage avancé**: Suppression des caractères parasites dans les CSV
- **Séparation prénom/nom**: Logique spécialement développée pour les formats français du barreau
- **Gestion des erreurs**: Retry et fallback sur chaque extraction

## Utilisation

```bash
python3 pau_scraper.py
```

### Options de test
Pour tester sur un échantillon limité, modifier la ligne 416:
```python
scraper = PauBarScraper(max_lawyers=30)  # Limite à 30 avocats
```

## Résultats obtenus
- **289 avocats** extraits
- **271 emails** trouvés (93.8% de succès)
- **Format de sortie**: CSV, JSON, TXT (emails seuls), rapport détaillé

## Fichiers générés
- `pau_CORRIGE_FINAL_289_avocats_YYYYMMDD_HHMMSS.csv`
- `pau_CORRIGE_FINAL_289_avocats_YYYYMMDD_HHMMSS.json`
- `pau_CORRIGE_EMAILS_YYYYMMDD_HHMMSS.txt`
- `pau_CORRIGE_RAPPORT_YYYYMMDD_HHMMSS.txt`

## Notes techniques
- Utilise `requests` et `BeautifulSoup` pour de meilleures performances
- Session HTTP avec User-Agent réaliste
- Gestion des pauses aléatoires entre requêtes
- Validation des données (emails, téléphones, années)
- Extraction d'adresses avec patterns multiples

## Particularités du site
- Structure standard avec articles `class="avocat"`
- Pas de pagination dynamique
- Pages individuelles avec informations détaillées
- Formats de noms français complexes nécessitant une logique spécifique