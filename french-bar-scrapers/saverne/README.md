# Scraper Barreau de Saverne

## Description
Ce scraper permet d'extraire toutes les informations des avocats du Barreau de Saverne depuis leur site officiel.

## Site cible
- **URL**: https://avocats-saverne.com/annuaire-des-avocats/
- **Total d'avocats**: ~33 avocats

## Informations extraites
- Prénom
- Nom
- Nom complet
- Année d'inscription au barreau
- Spécialisations
- Compétences
- Activités dominantes
- Structure/Cabinet
- Adresse
- Téléphone
- Email
- Site web
- Source (URL de la fiche)

## Prérequis
```bash
pip install selenium beautifulsoup4 pandas requests
```

## Utilisation

### Mode production (tous les avocats)
```bash
python saverne_scraper.py
```

### Mode test (10 premiers avocats)
```bash
python saverne_scraper.py --test
```

### Mode visible (avec fenêtres navigateur)
```bash
python saverne_scraper.py --visible
```

### Combinaisons possibles
```bash
python saverne_scraper.py --test --visible
```

## Fonctionnalités

### ✅ Gestion automatique des cookies
Le script accepte automatiquement les cookies du site.

### ✅ Mode headless par défaut
Scraping sans fenêtres pour ne pas interférer avec le travail.

### ✅ Gestion intelligente des noms composés
- Anne-Segolène BOCQUET → Prénom: "Anne-Segolène", Nom: "BOCQUET"
- Catherine ROTH-MULLER → Prénom: "Catherine", Nom: "ROTH-MULLER"

### ✅ Extraction exhaustive
Récupération de tous les avocats sans exception avec vérification anti-doublons.

### ✅ Système de backup automatique
Sauvegarde intermédiaire tous les 5 avocats traités.

### ✅ Multiples formats de sortie
- **CSV**: Format tableur
- **JSON**: Format structuré
- **TXT**: Liste des emails uniquement
- **Rapport détaillé**: Statistiques complètes

## Fichiers générés

### Production
- `SAVERNE_PRODUCTION_FINAL_XX_avocats_YYYYMMDD_HHMMSS.csv`
- `SAVERNE_PRODUCTION_FINAL_XX_avocats_YYYYMMDD_HHMMSS.json`
- `SAVERNE_PRODUCTION_EMAILS_XX_uniques_YYYYMMDD_HHMMSS.txt`
- `SAVERNE_PRODUCTION_RAPPORT_YYYYMMDD_HHMMSS.txt`

### Test
- `SAVERNE_TEST_FINAL_XX_avocats_YYYYMMDD_HHMMSS.csv`
- `SAVERNE_TEST_FINAL_XX_avocats_YYYYMMDD_HHMMSS.json`
- `SAVERNE_TEST_EMAILS_XX_uniques_YYYYMMDD_HHMMSS.txt`
- `SAVERNE_TEST_RAPPORT_YYYYMMDD_HHMMSS.txt`

### Backups automatiques
- `SAVERNE_BACKUP_5_YYYYMMDD_HHMMSS.json`
- `SAVERNE_BACKUP_10_YYYYMMDD_HHMMSS.json`
- etc.

## Statistiques d'extraction

Résultats du dernier scraping complet (2026-02-19) :
- **33 avocats** extraits (100% de couverture)
- **32 emails** récupérés (97% de réussite)
- **33 téléphones** récupérés (100%)
- **33 années d'inscription** récupérées (100%)
- **Zéro doublon** détecté

## Structure du code

### Classes principales
- `SaverneScraperFinal`: Classe principale du scraper

### Méthodes importantes
- `setup_driver()`: Configuration du navigateur Chrome
- `accept_cookies()`: Gestion automatique des cookies
- `get_all_lawyer_links()`: Récupération des liens d'avocats
- `extract_lawyer_details()`: Extraction des détails individuels
- `split_name_intelligently()`: Séparation intelligente prénom/nom
- `save_backup()`: Sauvegardes intermédiaires
- `save_final_results()`: Export des résultats finaux

## Robustesse

### Anti-détection
- User-agent réaliste
- Délais entre les requêtes
- Désactivation des indicateurs d'automation

### Gestion d'erreurs
- Retry automatique sur les échecs
- Logs détaillés
- Backup en cas d'interruption

### Patterns d'extraction flexibles
- Multiples sélecteurs CSS
- Regex adaptatifs pour emails/téléphones
- Fallback BeautifulSoup si Selenium échoue

## Dernière mise à jour
2026-02-20 - Version finale validée et intégrée au repository.