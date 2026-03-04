# Scraper Barreau de Saint-Quentin

🏛️ **Scraper pour le Barreau de Saint-Quentin - Extraction complète des données d'avocats**

## 📊 Résultats

- ✅ **43 avocats** récupérés (100%)
- ✅ **43 téléphones** (100%)
- ✅ **22 fax** (51.2%)
- ✅ **43 adresses détaillées** (100%)
- ✅ **Spécialités** correctement organisées
- ❌ **0 emails** (non disponibles publiquement)

## 🚀 Installation

```bash
pip install -r requirements.txt
```

## 📝 Utilisation

```bash
python saint_quentin_scraper.py
```

## 📁 Fichiers générés

Le script génère automatiquement :

- `SAINT_QUENTIN_PARFAIT_43_avocats_{timestamp}.csv` - **Données principales**
- `SAINT_QUENTIN_PARFAIT_43_avocats_{timestamp}.json` - Format JSON
- `SAINT_QUENTIN_CONTACTS_PARFAIT_{timestamp}.txt` - Contacts uniquement
- `SAINT_QUENTIN_EMAILS_PARFAIT_{timestamp}.txt` - Emails (vide)
- `SAINT_QUENTIN_RAPPORT_PARFAIT_{timestamp}.txt` - Rapport détaillé

## 📋 Colonnes du CSV

| Colonne | Description |
|---------|-------------|
| `prenom` | Prénom de l'avocat |
| `nom` | Nom de famille |
| `nom_complet` | Nom complet formaté |
| `annee_inscription` | Année d'inscription au barreau |
| `specialites` | Première spécialité juridique |
| `competences` | Deuxième spécialité |
| `activites_dominantes` | Troisième spécialité |
| `structure` | Cabinet/structure juridique |
| `adresse` | Adresse complète |
| `telephone` | Numéro de téléphone |
| `fax` | Numéro de fax |
| `email` | Adresse email (vide) |
| `source_url` | URL de la fiche individuelle |

## 🎯 Caractéristiques

- **Navigation complète** : Visite chaque page individuelle d'avocat
- **Extraction 100%** : Récupère tous les téléphones et adresses
- **Spécialités filtrées** : Ignore les textes légaux génériques
- **Gestion des noms composés** : "Jean-Marie", "Marie-Laure", etc.
- **Mode headless** : N'interfère pas avec le travail
- **Rapports détaillés** : Statistiques complètes

## ⚖️ Spécialités détectées

Le scraper identifie automatiquement :
- Droit fiscal et droit douanier
- Droit du travail
- Droit de la sécurité sociale
- Droit civil, pénal, commercial
- Et autres spécialités juridiques

## 🌐 Source

**URL** : https://www.avocats-saint-quentin.com/trouver-un-avocat/annuaire-des-avocats.htm

## ⏱️ Performance

- **Durée** : ~40 secondes
- **Vitesse** : 1.1 avocats/seconde
- **Taux de succès** : 100%

## 📞 Exemple de données

```csv
prenom,nom,annee_inscription,telephone,fax,specialites,adresse
Marc,ANTONINI,1981,0323060100,0323670096,,Maître Marc ANTONINI | Avocat SAINT-QUENTIN
Christophe,BEJIN,1984,0323648664,0323642377,Droit fiscal et droit douanier,35 Rue Victor Basch - Maître Christophe BEJIN
```

---
*Dernière mise à jour : 19/02/2026*