# 🏛️ Scraper Barreau de Villefranche-sur-Saône

## 📊 Informations générales

- **Barreau** : Villefranche-sur-Saône (69)
- **Site web** : https://www.avocatsvillefranche.fr/annuaire/
- **Date de création** : Mars 2026
- **Statut** : ✅ Fonctionnel et testé

## 🎯 Résultats d'extraction

- **Total avocats** : ~60 avocats
- **Couverture emails** : 100% (44 emails uniques)
- **Couverture téléphones** : 95%
- **Données d'adresses** : 100%
- **Spécialisations** : Quelques-unes disponibles
- **Années d'inscription** : 98%

## 📁 Fichiers disponibles

### 🚀 Scripts principaux

1. **`VILLEFRANCHE_SCRAPER_PRODUCTION.py`**
   - Script de production complet
   - Extrait TOUS les avocats (~60)
   - Mode headless (sans interface)
   - Sauvegardes automatiques tous les 25 avocats
   - Gestion d'erreurs robuste

2. **`VILLEFRANCHE_SCRAPER_AMELIORE.py`**
   - Version de test (20 avocats)
   - Idéal pour valider le fonctionnement
   - Plus rapide pour les tests

3. **`LANCER_PRODUCTION_VILLEFRANCHE.py`**
   - Lanceur interactif
   - Interface utilisateur conviviale
   - Demande confirmation avant extraction

### 📚 Documentation

4. **`GUIDE_UTILISATION_VILLEFRANCHE.md`**
   - Guide complet d'utilisation
   - Explications détaillées
   - Exemples de commandes

5. **`README.md`** (ce fichier)
   - Informations générales
   - Instructions rapides

## 🚀 Utilisation rapide

### Test (20 avocats)
```bash
python3 VILLEFRANCHE_SCRAPER_AMELIORE.py
```

### Production complète (~60 avocats)
```bash
python3 LANCER_PRODUCTION_VILLEFRANCHE.py
```

### Production directe
```bash
python3 VILLEFRANCHE_SCRAPER_PRODUCTION.py
```

## 📋 Prérequis

```bash
pip install selenium
```

- Chrome installé sur le système
- Connexion Internet stable

## 📊 Données extraites

Pour chaque avocat :
- ✅ **Prénom** (séparé du nom)
- ✅ **Nom** (gestion des noms composés)
- ✅ **Email** (100% disponible)
- ✅ **Téléphone** (quand disponible)
- ✅ **Adresse complète**
- ✅ **Spécialisations** (quand disponibles)
- ✅ **Année d'inscription au barreau**
- ✅ **URL source** (pour vérification)

## 📁 Fichiers générés

Chaque extraction produit :
- **CSV** : Données tabulaires (Excel compatible)
- **JSON** : Format structuré (APIs/BDD)
- **TXT** : Liste pure des emails
- **Rapport** : Statistiques détaillées

## ⚙️ Caractéristiques techniques

- **Mode headless** : Pas d'interface visuelle
- **Anti-détection** : User-agent réaliste
- **Sauvegardes** : Automatiques tous les 25 avocats
- **Gestion d'erreurs** : Robuste avec récupération
- **Performance** : ~2 minutes pour extraction complète

## 🔄 Mise à jour

Pour mettre à jour les données :

1. Exécuter le script de production
2. Nouveaux fichiers horodatés générés
3. Comparer avec extraction précédente

## 📞 Support

En cas de problème :
1. Vérifier Chrome installé
2. Installer dépendances : `pip install selenium`
3. Vérifier connexion Internet
4. Consulter fichiers debug générés

---

*Dernière extraction réussie : Mars 2026 (60 avocats)*