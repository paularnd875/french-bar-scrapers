# Scraper Barreau de l'Essonne (91)

Scraper complet pour extraire les informations des avocats du Barreau de l'Essonne depuis le site officiel.

## 🎯 Site cible
**URL:** https://www.avocats91.com/lordre-des-avocats/annuaire-des-avocats.htm

## ✅ Données extraites

- **Nom complet** de l'avocat
- **Email** (décodage automatique des emails obfusqués)
- **Téléphone**
- **Année d'inscription** au barreau
- **Structure/Cabinet**
- **Adresses**
- **URLs de contact**

## 📊 Résultats
- **346 avocats** dans l'annuaire
- **Taux de succès:** 99,4% pour les emails, 99,7% pour les téléphones
- **Durée d'extraction:** ~30 minutes en mode complet

## 🚀 Utilisation

### Installation des dépendances
```bash
pip install selenium beautifulsoup4
```

### Scripts disponibles

#### 1. Test rapide (3 avocats)
```bash
python run_essonne_test.py
```

#### 2. Extraction complète (346 avocats)
```bash
python run_essonne_complet.py
```

#### 3. Script principal avec interface
```bash
python essonne_scraper_final.py
```

## 📁 Fichiers générés

Pour chaque extraction, 4 fichiers sont créés :

1. **`.csv`** - Format tableur (Excel compatible)
2. **`.json`** - Format structuré pour intégration
3. **`_emails.txt`** - Liste des emails uniquement
4. **`_rapport.txt`** - Rapport détaillé avec statistiques

### Exemple de nommage
```
essonne_COMPLET_FINAL_20260211_130112.csv
essonne_COMPLET_FINAL_20260211_130112.json
essonne_COMPLET_FINAL_emails_20260211_130112.txt
essonne_COMPLET_FINAL_rapport_20260211_130112.txt
```

## 🔧 Fonctionnalités techniques

### Gestion automatique
- ✅ **Acceptation des cookies**
- ✅ **Mode headless** (sans interface)
- ✅ **Décodage des emails obfusqués**
- ✅ **Sauvegardes intermédiaires** (toutes les 50 extractions)
- ✅ **Gestion robuste des erreurs**
- ✅ **Anti-détection**

### Structure des données
```json
{
  "nom_complet": "MARIE NOELLE ADAM",
  "nom": "MARIE",
  "prenom": "NOELLE ADAM", 
  "email": "adammn-avocat@outlook.fr",
  "telephone": "0660304587",
  "annee_inscription": "1990",
  "structure": "MARIE NOELLE ADAM",
  "detail_url": "https://www.avocats91.com/page/annuaire/...",
  "contact_url": "https://www.avocats91.com/page/annuaire/...#contact"
}
```

## ⚠️ Notes importantes

1. **Respect du site :** Le scraper inclut des délais entre les requêtes
2. **Mode headless :** Recommandé pour éviter les interruptions
3. **Chrome requis :** Le scraper utilise ChromeDriver
4. **Durée :** L'extraction complète prend environ 30 minutes

## 📈 Statistiques d'extraction

| Métrique | Valeur |
|----------|--------|
| Total avocats | 346 |
| Emails extraits | 344 (99,4%) |
| Téléphones | 345 (99,7%) |
| Noms complets | 346 (100%) |
| Années inscription | 346 (100%) |

## 🛠 Personnalisation

Le script principal `essonne_scraper_final.py` peut être adapté pour :
- Modifier le nombre d'avocats testés
- Changer la fréquence des sauvegardes
- Ajuster les délais entre extractions
- Personaliser les formats de sortie

## 🆕 Dernière mise à jour
**Date :** 11 février 2026  
**Version :** 1.0  
**Status :** ✅ Production Ready