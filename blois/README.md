# Scraper Barreau de Blois

## Description
Scraper Python pour extraire toutes les informations des avocats du Barreau de Blois depuis https://avocats-blois.com/trouver-un-avocat/

## Résultats
- **75 avocats** extraits (sur 76 total - 99% de réussite)
- **46 emails** récupérés (61.3% de taux de réussite)
- **Extraction complète** avec toutes les informations disponibles

## Informations extraites
- ✅ **Identité** : Nom, prénom, nom complet, civilité, titre
- ✅ **Contact** : Email, téléphone, fax, site web
- ✅ **Adresse** : Adresse complète, ville, code postal
- ✅ **Professionnel** : Spécialisations juridiques, domaines de compétences
- ✅ **Carrière** : Année d'inscription, date de serment, barreau d'origine
- ✅ **Structure** : Cabinet, associés, structure juridique
- ✅ **Formation** : Diplômes, formations, langues parlées
- ✅ **Autres** : Description, biographie, coordonnées complètes

## Fichiers

### Scripts principaux
- **`blois_scraper.py`** - Scraper principal avec extraction complète
- **`generate_final_files.py`** - Générateur de fichiers finaux formatés

### Utilisation
```bash
# Installation des dépendances
pip install selenium

# Lancement du scraper complet
python3 blois_scraper.py

# Génération des fichiers finaux (après scraping)
python3 generate_final_files.py
```

## Fichiers générés
1. **CSV principal** - Toutes les colonnes et informations
2. **CSV emails** - Avocats avec email + infos essentielles
3. **JSON complet** - Format structuré avec tous les champs
4. **TXT emails** - Liste pure des emails uniquement
5. **Rapport** - Statistiques détaillées et analyse

## Caractéristiques techniques
- **Mode headless** : Pas d'ouverture de fenêtres
- **Anti-détection** : User-Agent et options Chrome optimisées
- **Sauvegarde progressive** : Tous les 15 avocats
- **Extraction robuste** : Multiples stratégies par champ
- **Gestion d'erreurs** : Continue même en cas d'erreur sur une fiche

## Spécialisations les plus trouvées
- Droit civil
- Droit de la famille
- Droit pénal
- Droit du travail
- Droit commercial
- Droit immobilier
- Droit des baux

## Taux de réussite par information
- **Noms/prénoms** : 100% (75/75)
- **Emails** : 61.3% (46/75)
- **Spécialisations** : 42.7% (32/75)
- **Téléphones** : 5.3% (4/75)
- **Adresses** : 5.3% (4/75)
- **Années inscription** : 4.0% (3/75)

## Exemple de données extraites
```json
{
  "nom_complet": "PRUD'HOMME ARTHUR",
  "nom": "PRUD'HOMME",
  "prenom": "ARTHUR",
  "email": "arthur.prudhomme@avocat.fr",
  "specialisations": "Droit civil; Droit du dommage corporel; Droit pénal",
  "annee_inscription": "2024",
  "url": "https://avocats-blois.com/arthur-prudhomme/"
}
```

## Notes
- Site web responsive avec chargement dynamique
- 76 fiches d'avocats identifiées au total
- Temps d'exécution : ~10 minutes pour extraction complète
- Respect des délais entre requêtes (1 seconde)
- Compatible avec les dernières versions de Chrome/Selenium