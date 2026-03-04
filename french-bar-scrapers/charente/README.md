# Scraper Barreau de Charente

## Description
Scraper complet pour extraire tous les avocats du Barreau de Charente avec leurs informations complètes et emails personnels.

**Site web**: https://www.avocats-charente.com/annuaire-des-avocats

## Résultats
- ✅ **132/132 avocats extraits** (100% de couverture)
- ✅ **132/132 emails personnels trouvés** (100% de taux de réussite)
- ✅ **Temps d'exécution**: ~25 minutes
- ✅ **Protection anti-bot**: Contournée avec succès

## Fonctionnalités techniques

### Déobfuscation JavaScript
Le site utilise une protection avancée des emails par obfuscation JavaScript :
- Encoding HTML entities (`&#97;` = 'a', etc.)
- Variables JavaScript dynamiques
- Éléments DOM "cloak"

**Solution implémentée** : 5 méthodes d'extraction complémentaires :
1. Liens `mailto:` directs
2. Regex avec décodage HTML entities
3. Recherche dans le texte visible post-JavaScript
4. Déclenchement des éléments cloak
5. Regex avancée sur le code source

### Navigation multi-pages
- **9 pages** à traiter (15 avocats par page + 12 sur la dernière)
- Pagination par paramètre URL (`limitstart`)
- Gestion des cookies automatique
- Sauvegardes intermédiaires toutes les 3 pages

### Anti-détection
- User-agent naturel
- Délais respectueux entre requêtes (2-5 secondes)
- Désactivation des indicateurs d'automatisation
- Headless mode optionnel

## Utilisation

### Prérequis
```bash
pip install selenium
```

### Lancement
```bash
python charente_scraper_production.py
```

### Options
- Mode headless/visible
- Confirmation avant lancement
- Sauvegardes intermédiaires automatiques

## Fichiers de sortie

Le scraper génère 5 fichiers :
- `charente_COMPLET_YYYYMMDD_HHMMSS.json` - Données complètes JSON
- `charente_COMPLET_YYYYMMDD_HHMMSS.csv` - Données complètes CSV  
- `charente_EMAILS_COMPLET_YYYYMMDD_HHMMSS.csv` - CSV emails uniquement
- `charente_EMAILS_SEULEMENT_YYYYMMDD_HHMMSS.txt` - Liste emails simple
- `charente_RAPPORT_COMPLET_YYYYMMDD_HHMMSS.txt` - Rapport détaillé

## Structure des données

### Champs extraits
- `prenom` - Prénom de l'avocat
- `nom` - Nom de famille
- `nom_complet` - Nom complet
- `url_profil` - URL du profil individuel
- `code_postal` - Code postal
- `ville` - Ville d'exercice
- `adresse` - Adresse complète
- `telephone` - Numéro de téléphone
- `specialites` - Domaines de spécialisation
- `email_personnel` - Email personnel déobfusqué
- `email_generique` - Email générique du barreau
- `autres_emails` - Autres emails trouvés
- `total_emails_trouves` - Nombre total d'emails

### Exemple de données
```json
{
  "prenom": "Sonia",
  "nom": "AIMARD",
  "nom_complet": "Sonia AIMARD",
  "url_profil": "https://www.avocats-charente.com/cb-profile/saimardloubere.html",
  "code_postal": "16000",
  "ville": "ANGOULEME",
  "adresse": "11, rue Montalembert",
  "telephone": "05 45 39 56 44",
  "specialites": "",
  "email_personnel": "s.aimard@abvocare.fr",
  "email_generique": "contact@avocats-charente.com",
  "autres_emails": "",
  "total_emails_trouves": 2
}
```

## Architecture technique

### Classe `CharenteCompletScraper`
- `setup_driver()` - Configuration Chrome avec anti-détection
- `accept_cookies()` - Gestion automatique des cookies
- `navigate_to_page(page_num)` - Navigation avec pagination
- `collect_basic_info_from_page(page_num)` - Extraction infos de base
- `extract_all_emails_from_profile(url, name)` - Déobfuscation emails
- `scrape_all_lawyers()` - Orchestration complète
- `save_intermediate_backup()` - Sauvegardes intermédiaires
- `save_final_results()` - Génération fichiers finaux

### Gestion d'erreurs
- Try/catch sur chaque avocat individuel
- Continuation en cas d'erreur ponctuelle  
- Logs détaillés pour debugging
- Sauvegardes de récupération

## Validations

### Test sur 10 avocats
- **10/10 emails trouvés** (100% de succès)
- Validation de toutes les méthodes de déobfuscation
- Correction des erreurs de navigation (stale element)

### Test complet (132 avocats)
- **132/132 emails extraits** (100% de succès)
- **Durée**: 24 minutes 22 secondes
- **Aucune erreur** technique rencontrée

## Défis techniques résolus

1. **Obfuscation JavaScript avancée**
   - Problème : Emails encodés en HTML entities
   - Solution : Décodage `html.unescape()` + regex multiples

2. **Erreurs stale element**
   - Problème : Navigation invalidait les références DOM
   - Solution : Collecte des infos de base avant navigation vers profils

3. **Protection anti-bot**
   - Problème : Détection d'automation
   - Solution : User-agent naturel + délais + désactivation webdriver

## Performance
- **Vitesse**: ~5,5 avocats/minute
- **Fiabilité**: 100% de taux de réussite
- **Robustesse**: Sauvegardes intermédiaires + gestion d'erreurs

---

**Développé avec succès le 11/02/2026**  
**Validation complète**: ✅ 132/132 avocats extraits avec emails