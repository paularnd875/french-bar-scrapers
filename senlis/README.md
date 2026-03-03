# Scraper du Barreau de Senlis

## 📋 Description

Ce scraper extrait automatiquement tous les avocats inscrits au Barreau de Senlis depuis leur annuaire en ligne.

**Site source :** https://senlis-avocats.fr/besoin-dun-avocat/annuaire-des-avocats

## 🎯 Données extraites

Pour chaque avocat, le scraper récupère :

- **Prénom** (colonne A)
- **Nom** (colonne B) 
- **Nom complet** (colonne C)
- **Email** ✉️
- **Téléphone** ☎️
- **Adresse complète** (rue, numéro)
- **Code postal**
- **Ville**
- **Date de serment au barreau**
- **Site web** (si disponible)
- **URL source** (lien vers la page d'origine)
- **Numéro de page**

## 📊 Résultats attendus

- **~95 avocats** répartis sur 12 pages
- **Taux de réussite** : 100% 
- **Format de sortie** : CSV, JSON, TXT (emails uniquement)

## 🚀 Installation & Utilisation

### Prérequis
```bash
pip install playwright beautifulsoup4 pandas
playwright install chromium
```

### Utilisation

#### Mode test (2 pages seulement)
```bash
python3 senlis_scraper_final_improved.py test
```

#### Mode production complet (toutes les pages)
```bash
python3 senlis_scraper_final_improved.py
```

## 📁 Fichiers générés

Le scraper génère automatiquement :

1. **CSV principal** : `SENLIS_IMPROVED_COMPLETE_YYYYMMDD_HHMMSS.csv`
   - Avec séparation prénoms/noms en colonnes distinctes
   - URL source pour chaque entrée

2. **JSON complet** : `SENLIS_IMPROVED_COMPLETE_YYYYMMDD_HHMMSS.json`
   - Toutes les données en format structuré

3. **Liste emails** : `SENLIS_IMPROVED_COMPLETE_emails_YYYYMMDD_HHMMSS.txt`
   - Un email par ligne pour import facile

## ⚡ Fonctionnalités avancées

### Séparation intelligente des noms
Le scraper identifie automatiquement :
- **Prénoms** : Première lettre majuscule, reste minuscule (ex: "Marie-Claire")
- **Noms** : TOUT EN MAJUSCULES (ex: "DUPONT-MARTIN")
- **Gestion des noms composés** avec tirets

### Mode headless
- Extraction discrète et rapide
- Pas d'ouverture de navigateur visible
- Optimisé pour les serveurs

### Anti-détection
- Délais aléatoires entre les requêtes
- User-agent réaliste
- Gestion des modales et popups

## 🛠 Structure technique

### Architecture
- **Playwright** : Navigation web automatisée
- **BeautifulSoup** : Parsing HTML intelligent
- **Regex avancées** : Extraction emails, téléphones, dates
- **Logging complet** : Suivi détaillé de l'extraction

### Gestion des erreurs
- Retry automatique en cas d'échec
- Sauvegarde intermédiaire toutes les 3 pages
- Logs détaillés des problèmes rencontrés

## 📈 Historique

- **v1.0** : Version basique avec extraction simple
- **v2.0** : Ajout séparation prénoms/noms + mode headless
- **v2.1** : Optimisation anti-détection + URL sources

## 📝 Notes importantes

⚠️ **Respecter les conditions d'utilisation** du site source
⚠️ **Utilisation responsable** : pas de surcharge du serveur
⚠️ **Données personnelles** : respecter le RGPD

## 🔄 Mise à jour des données

Pour mettre à jour la base de données :

1. Relancer le scraper en mode production
2. Comparer avec les données précédentes
3. Identifier les nouveaux avocats et les modifications

---

*Dernière mise à jour : Mars 2026*
*Scraper développé et optimisé pour le Barreau de Senlis*