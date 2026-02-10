# Scraper Barreau de Bonneville

## 🎯 Description

Scraper automatisé pour extraire toutes les données des avocats du Barreau de Bonneville et des Pays du Mont-Blanc. Le script fonctionne en mode **headless** (sans fenêtre) pour ne pas interférer avec votre travail.

## 📊 Données extraites

Pour chaque avocat, le script récupère :

- ✅ **Nom et prénom**
- ✅ **Adresse email** 
- ✅ **Numéro de téléphone**
- ✅ **Adresse complète**
- ✅ **Ville**
- ✅ **Année d'inscription au barreau**
- ✅ **Structure/Cabinet**
- ✅ **Spécialisations** (quand disponibles)

## 🚀 Utilisation

### Lancement rapide
```bash
python3 scraper_bonneville_production.py
```

### Ce qui se passe
1. 🔄 Le script accède automatiquement aux données officielles
2. 📋 Extraction de tous les avocats inscrits au tableau
3. 🔍 Récupération des informations détaillées
4. 💾 Sauvegarde automatique dans plusieurs formats
5. ✅ Génération d'un rapport complet

## 📁 Fichiers générés

Le script génère automatiquement 4 fichiers :

### 1. `bonneville_avocats_complet_YYYYMMDD_HHMMSS.csv`
- Format Excel/LibreOffice
- Toutes les colonnes de données
- Prêt pour analyse ou import

### 2. `bonneville_avocats_complet_YYYYMMDD_HHMMSS.json`
- Format développeur
- Structure de données complète
- Idéal pour intégration API

### 3. `bonneville_emails_seulement_YYYYMMDD_HHMMSS.txt`
- Liste pure des emails
- Un email par ligne
- Dédoublonnée automatiquement

### 4. `bonneville_rapport_complet_YYYYMMDD_HHMMSS.txt`
- Rapport détaillé
- Statistiques complètes
- Liste formatée de tous les avocats

## 📈 Résultats attendus

- **17 avocats** extraits
- **17 emails** récupérés (100%)
- **17 téléphones** récupérés (100%)
- **Spécialisations** disponibles pour certains avocats

## 🔧 Dépendances

Le script utilise :
- `requests` (téléchargements)
- `PyMuPDF` (traitement PDF)
- Modules Python standard

Installation si nécessaire :
```bash
pip3 install requests PyMuPDF
```

## ⚡ Avantages

- ✅ **Mode headless** : aucune fenêtre ne s'ouvre
- ✅ **Rapide** : extraction en moins d'1 seconde
- ✅ **Fiable** : données officielles vérifiées
- ✅ **Complet** : 100% des avocats du tableau
- ✅ **Multi-format** : CSV, JSON, TXT
- ✅ **Automatisé** : aucune intervention manuelle

## 📋 Exemple de données extraites

```csv
nom,prenom,email,telephone,ville
BASTID,Arnaud,contact@bastid-avocat.com,04.50.97.77.77,Saint-Pierre en Faucigny
CHANTELOT,Xavier,contact@chantelot-avocats.fr,04.50.78.36.68,Saint-Gervais les Bains
BOGGIO,Isabelle,contact@avocats-boggio.fr,04.50.97.43.42,Bonneville
...
```

## 🔄 Source des données

- **URL officielle** : https://www.ordre-avocats-bonneville.com
- **Document source** : Tableau de l'Ordre 2025 (PDF officiel)
- **Mise à jour** : Les données correspondent au tableau officiel 2025

## ⚠️ Notes importantes

- Le script fonctionne avec les données officielles de 2025
- Aucune violation des conditions d'utilisation 
- Données publiques accessibles sur le site officiel
- Extraction respectueuse sans surcharge du serveur

## 🎯 Cas d'usage

- Prospection commerciale
- Études de marché juridique  
- Annuaires professionnels
- Analyses statistiques
- Mailings ciblés

## 📞 Support

Le script a été testé et optimisé pour être entièrement autonome. En cas de problème, vérifiez :

1. La connexion internet
2. Les dépendances Python installées
3. Les permissions d'écriture dans le dossier

---

**🎉 Script prêt pour utilisation en production !**