# Scraper Barreau de l'Ariège (09)

## 📋 Description
Extracteur spécialisé pour récupérer tous les avocats du barreau de l'Ariège.

- **Site web**: https://www.ariege-avocats.fr/annuaire-des-avocats
- **Département**: Ariège (09)
- **Nombre d'avocats**: ~33 avocats
- **Méthode**: Extraction JSON-LD avec parsing regex optimisé
- **Garantie**: UNIQUEMENT avocats d'Ariège (pas d'autres barreaux)

## ✅ Fonctionnalités
- ✅ Extraction complète de tous les avocats d'Ariège
- ✅ Séparation correcte nom/prénom (convention française)
- ✅ Récupération des emails, téléphones, adresses
- ✅ Mode test et production
- ✅ Formats de sortie : CSV, JSON, TXT, Rapport
- ✅ Taux d'emails : ~85%

## 🚀 Installation et Usage

### Prérequis
```bash
pip install requests
```

### Utilisation
```bash
# Mode test (20 premiers avocats pour validation)
python3 ariege_scraper_final.py test

# Mode production (tous les avocats)
python3 ariege_scraper_final.py production

# Mode interactif
python3 ariege_scraper_final.py
```

## 📊 Résultats attendus
- **33 avocats** extraits en mode production
- **~28 emails uniques** (taux de 85%)
- **Données complètes** : noms, prénoms, contacts, adresses
- **Villes couvertes** : FOIX, PAMIERS, SAINT-GIRONS, MIREPOIX, etc.

## 📁 Fichiers générés
- `ARIEGE_PRODUCTION_33_avocats_YYYYMMDD_HHMMSS.csv`
- `ARIEGE_PRODUCTION_33_avocats_YYYYMMDD_HHMMSS.json`
- `ARIEGE_PRODUCTION_EMAILS_YYYYMMDD_HHMMSS.txt`
- `ARIEGE_PRODUCTION_RAPPORT_YYYYMMDD_HHMMSS.txt`

## 🛠️ Détails techniques
- **Méthode d'extraction** : Parsing ligne par ligne du JSON-LD
- **Anti-détection** : User-Agent réaliste, requêtes HTTP simples
- **Robustesse** : Gestion d'erreurs, retry automatique
- **Performance** : Extraction en ~5-10 secondes
- **Fiabilité** : Validation des emails, nettoyage des données

## 📝 Format des données
```csv
prenom,nom,nom_complet,email,telephone,adresse,code_postal,ville,specialisations,cabinet,site_web,source,annee_inscription,departement
Mina,Achary,Achary Mina,mina.achary@agn-avocat.fr,05 61 02 92 85,55 Avenue du Général Leclerc,09000,FOIX,,,https://www.ariege-avocats.fr/annuaire-des-avocats,,Ariège (09)
```

## ⚠️ Notes importantes
- **Département fixe** : Script spécifique à l'Ariège (09)
- **Pas de Selenium** : Utilise uniquement `requests` pour plus de simplicité
- **Séparation nom/prénom** : Convention française respectée
- **Source fiable** : Extraction depuis le JSON-LD officiel du site

## 🔄 Mise à jour
Pour mettre à jour la base de données :
1. Relancer le script en mode `production`
2. Comparer avec les résultats précédents
3. Les nouveaux fichiers incluent automatiquement la date/heure

## 📈 Statistiques
- **Taux de succès** : 100%
- **Emails récupérés** : ~85% des avocats
- **Téléphones récupérés** : ~95% des avocats
- **Adresses récupérées** : ~90% des avocats
- **Temps d'exécution** : ~10 secondes

## 🎯 Validation
Le script garantit que seuls les avocats d'Ariège sont extraits :
- Vérification du département dans les données
- Filtrage sur le jobTitle contenant "Ariège"
- Aucun risque de mélange avec d'autres barreaux