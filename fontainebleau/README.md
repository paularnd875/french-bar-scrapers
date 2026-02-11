# Scraper du Barreau de Fontainebleau

## Description
Scraper complet pour extraire tous les avocats du Barreau de Fontainebleau (77).

**Site web :** https://avocats-fontainebleau.fr/trouver-un-avocat/

## Résultats
- ✅ **51 avocats** extraits (100% de couverture)
- ✅ **7 pages** scrapées automatiquement
- ✅ **50 emails** professionnels uniques
- ✅ Toutes les informations : noms, prénoms, emails, téléphones, spécialisations, années d'inscription, adresses, structures

## Fonctionnalités
- 🍪 **Gestion automatique des cookies**
- 📄 **Navigation automatique entre les 7 pages**
- 🔍 **Extraction complète des données**
- 💾 **Sauvegarde multi-formats** (JSON, CSV, TXT emails, Rapport détaillé)
- 👻 **Mode headless** (sans interface visuelle)
- 🛡️ **Anti-détection** intégré
- ⚡ **Gestion robuste des erreurs**

## Informations extraites par avocat
- Nom complet, prénom, nom de famille
- Email professionnel
- Numéro de téléphone
- Adresse complète
- Date de serment
- Année d'inscription au barreau
- Spécialisations et compétences dominantes
- Structure/Cabinet d'exercice
- Site web (si disponible)
- URL de la fiche détaillée
- Numéro de page où l'avocat a été trouvé

## Installation

### Prérequis
```bash
pip install selenium webdriver-manager
```

### Utilisation
```bash
python fontainebleau_scraper.py
```

## Structure de pagination
Le site utilise une pagination en 7 pages :
- **Pages 1-6** : 8 avocats chacune
- **Page 7** : 3 avocats
- **Total** : 51 avocats

## Fichiers générés
Le script génère automatiquement :

1. **JSON complet** : `fontainebleau_COMPLET_7PAGES_YYYYMMDD_HHMMSS.json`
2. **CSV complet** : `fontainebleau_COMPLET_7PAGES_YYYYMMDD_HHMMSS.csv`
3. **Emails uniquement** : `fontainebleau_EMAILS_COMPLET_7PAGES_YYYYMMDD_HHMMSS.txt`
4. **Rapport détaillé** : `fontainebleau_RAPPORT_COMPLET_7PAGES_YYYYMMDD_HHMMSS.txt`

## Statistiques d'extraction
- ✅ **Couverture** : 100% (51/51 avocats)
- 📧 **Emails** : 98% (50/51 avocats avec email)
- 📱 **Téléphones** : 100% (51/51 avocats)
- 🏢 **Structures** : ~70% (avocats avec cabinet/structure)
- 🎓 **Années d'inscription** : 100% (toutes les dates de serment)

## Navigation
Le scraper utilise 3 méthodes de navigation entre pages :
1. **Lien "suivant"** avec `rel='next'`
2. **Liens par numéro** de page (1, 2, 3, etc.)
3. **Navigation directe** par URL en cas d'échec

## Gestion des cookies
Acceptation automatique avec plusieurs sélecteurs :
- `button[id*='accept']`
- `button[class*='accept']`
- `button[class*='cookie']`
- `[class*='cookie'] button`

## Mode d'exécution
- **Mode headless** par défaut (aucune fenêtre visible)
- Navigation fluide avec pauses entre pages
- Extraction silencieuse pour ne pas perturber le travail

## Sélecteurs CSS utilisés
```css
.wpbdp-listing                           /* Conteneur avocat */
.wpbdp-field-nom .value a                /* Nom complet */
.wpbdp-field-e-mail .value               /* Email */
.wpbdp-field-telephone .value            /* Téléphone */
.wpbdp-field-date_de_serment .value      /* Date de serment */
.wpbdp-field-competences_dominantes .value ul li  /* Compétences */
.address-info div                        /* Adresse */
.cabinet                                 /* Structure/Cabinet */
.wpbdp-field-site_internet .value a     /* Site web */
```

## Performance
- **Temps d'exécution** : ~2-3 minutes pour les 7 pages
- **Pause entre pages** : 2 secondes
- **Timeout par page** : 10 secondes
- **Gestion d'erreurs** : Continue même en cas d'échec partiel

## Structure des données JSON
```json
{
  "prenom": "Jean",
  "nom": "MARTIN",
  "nom_complet": "MARTIN Jean",
  "email": "jean.martin@avocat.fr",
  "telephone": "+33 1 23 45 67 89",
  "adresse": "123 rue Example - 77300 FONTAINEBLEAU",
  "annee_inscription": "2015",
  "date_serment": "15/01/2015",
  "specialisations": ["Droit Civil", "Droit Pénal"],
  "competences": ["Droit Civil", "Droit Pénal"],
  "structure": "Cabinet Example",
  "site_web": "https://example.fr",
  "url_fiche": "https://avocats-fontainebleau.fr/...",
  "page_trouvee": 1
}
```

## Développeur
Créé avec Claude Code - Extraction complète et fiable des données du Barreau de Fontainebleau.

---

**Dernière mise à jour :** 11 février 2026  
**Version :** 1.0  
**Status :** Production Ready ✅