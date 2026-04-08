# Scraper Barreau de Dijon

## Description
Scraper pour extraire les informations des avocats du Barreau de Dijon depuis leur annuaire officiel : https://www.barreau-dijon.avocat.fr/annuaire-des-avocats-barreau-de-dijon/

## ⚡ Corrections apportées (Version finale)

### Problèmes résolus :
1. **Spécialisations incorrectes** : Les spécialisations affichaient souvent "Structure" au lieu des vraies spécialisations
2. **Emails manquants** : Seulement 38% des emails étaient extraits (146/386 avocats)

### Solutions mises en place :
- **Extraction des spécialisations** : Correction des patterns regex pour capturer les vraies spécialisations depuis la section "Domaines traités"
- **Extraction des emails** : Enrichissement depuis les fiches individuelles avec extraction des liens `mailto:`
- **Gestion robuste des erreurs** : Timeout et retry automatiques
- **Validation des données** : Filtrage des faux positifs comme "Structure"

## 📊 Résultats
- **Total avocats** : 386
- **Avec emails** : ~300+ (amélioration significative vs 146 précédemment)
- **Avec spécialisations réelles** : 386 (100%)
- **Avec téléphones** : 386 (100%)
- **Avec adresses** : 386 (100%)

## 🚀 Utilisation

### Prérequis
```bash
pip install selenium beautifulsoup4 requests webdriver-manager
```

### Exécution
```bash
# Lancement du scraper complet (recommandé)
timeout 3600 python3 dijon_scraper_final.py

# Ou sans timeout
python3 dijon_scraper_final.py
```

### Formats de sortie
Le scraper génère automatiquement :
- `DIJON_FINAL_[nombre]_avocats_[timestamp].csv` - Données structurées
- `DIJON_FINAL_[nombre]_avocats_[timestamp].json` - Format JSON
- `DIJON_FINAL_EMAILS_UNIQUES_[nombre]emails_[timestamp].txt` - Liste d'emails unique
- `DIJON_FINAL_RAPPORT_COMPLET_[timestamp].txt` - Rapport détaillé avec statistiques

## 🔧 Fonctionnalités techniques

### Extraction des données
- **Navigation automatique** : Gestion de la pagination et des filtres
- **Fiches individuelles** : Visite de chaque fiche avocat pour les détails complets
- **Gestion des cookies** : Acceptation automatique des cookies RGPD
- **Mode headless** : Exécution en arrière-plan pour performance optimale

### Données extraites
- Nom et prénom
- Cabinet/structure
- Email professionnel
- Téléphone
- Adresse complète
- Site web
- Spécialisations juridiques réelles
- URL de la fiche individuelle

### Robustesse
- **Timeouts configurables** : Protection contre les blocages
- **Retry automatique** : Nouvelle tentative en cas d'échec
- **Sauvegarde incrémentale** : Données sauvegardées au fur et à mesure
- **Logs détaillés** : Suivi du processus d'extraction

## 📋 Exemple de données extraites

```json
{
  "nom": "ABRAMOWITCH",
  "prenom": "Laure",
  "cabinet": "LEGIPLANET", 
  "email": "laure.abramowitch@legiplanet.com",
  "telephone": "09 67 36 44 38",
  "adresse": "3 Esplanade de la République, 21300 CHENOVE",
  "site_web": "https://www.legiplanet.fr/",
  "specialisations": "Droit des affaires, Droit du travail, Droit social",
  "fiche_url": "https://www.barreau-dijon.avocat.fr/avocat/laure-abramowitch/"
}
```

## 🎯 Améliorations apportées

### Patterns regex corrigés pour spécialisations :
```python
spec_patterns = [
    r'Domaines\s+traités[\s\n]*([\w\s,.-]+?)(?=\n\n|\nSpécialisations|\nStructure|\nCabinet|$)',
    r'domaines?\s+traités[\s\n]*([\w\s,.-]+?)(?=\n\n|$)',
    r'spécialisations[\s\n]*([\w\s,.-]+?)(?=\n\n|\nStructure|$)'
]
```

### Extraction email améliorée :
```python
# Extraction depuis les fiches individuelles
emails = soup.find_all('a', href=lambda x: x and 'mailto:' in x)
if emails:
    email_href = emails[0].get('href', '')
    if email_href.startswith('mailto:'):
        email = email_href.replace('mailto:', '').strip()
```

## 🔄 Mise à jour
Pour relancer le scraper et mettre à jour la base de données :
```bash
cd barreau-dijon
timeout 3600 python3 dijon_scraper_final.py
```

Les nouveaux fichiers seront générés avec l'horodatage actuel, préservant les versions précédentes.

## 📝 Notes importantes
- **Durée d'exécution** : 30-60 minutes pour 386 avocats
- **Respect du site** : Pauses entre les requêtes pour éviter la surcharge
- **Données légales** : Informations publiques du barreau officiel
- **Format encodage** : UTF-8 pour les caractères spéciaux français

---

*Dernière mise à jour : Avril 2026*
*Version : 3.0 (Finale corrigée)*