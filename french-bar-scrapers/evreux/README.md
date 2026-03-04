# Scraper Barreau d'Évreux

## 🎯 Objectif
Extraire toutes les informations des **137 avocats** du Barreau de l'Eure depuis leur annuaire officiel : https://www.barreau-evreux.avocat.fr/annuaire-des-avocats/liste-et-recherche

## ✅ Fonctionnalités
- ✅ Extraction des noms complets, prénoms et noms
- ✅ Récupération des téléphones (100% de réussite)
- ✅ Extraction des années d'inscription/serment au barreau (100% de réussite)
- ✅ Récupération des adresses complètes avec codes postaux et villes (100% de réussite)
- ✅ Identification des spécialisations en droit (33.6% de réussite)
- ⚠️ Emails limités (protection anti-spam du barreau - seulement 1 email public trouvé)
- ✅ Mode headless (sans interface visuelle)
- ✅ Génération de multiples formats de sortie
- ✅ Sauvegardes intermédiaires automatiques
- ✅ Gestion d'erreurs robuste

## 📊 Résultats attendus
- **137 avocats** répartis sur **6 pages**
- **100% de réussite** pour les noms, téléphones, années et adresses
- **~34% de réussite** pour les spécialisations
- **Très peu d'emails** (protection du barreau contre le spam)

## 🚀 Utilisation

### Installation des dépendances
```bash
pip install -r requirements.txt
```

### Lancement du scraper
```bash
python evreux_scraper.py
```

## 📁 Fichiers générés

Le scraper génère automatiquement 4 fichiers :

### 1. Données complètes JSON
- `EVREUX_FINAL_COMPLET_137_avocats_[timestamp].json`
- Format JSON avec toutes les données structurées
- Inclut les métadonnées d'extraction et statistiques

### 2. Données CSV pour Excel
- `EVREUX_FINAL_COMPLET_137_avocats_[timestamp].csv` 
- Format CSV compatible Excel/Google Sheets
- Prêt pour analyse et traitement

### 3. Emails uniquement
- `EVREUX_EMAILS_SEULEMENT_137_avocats_[timestamp].txt`
- Liste des emails trouvés (très peu)
- Format simple nom : email

### 4. Rapport d'extraction
- `EVREUX_RAPPORT_FINAL_137_avocats_[timestamp].txt`
- Statistiques détaillées de l'extraction
- Pourcentages de réussite par type de données

## 📋 Structure des données

Chaque avocat extrait contient :

```json
{
  "url": "URL de la fiche officielle",
  "nom_complet": "Maître Prénom NOM",
  "prenom": "Prénom", 
  "nom": "NOM",
  "email": "email@domain.fr ou null",
  "telephone": "02 XX XX XX XX",
  "adresse_complete": "Adresse complète",
  "code_postal": "27XXX",
  "ville": "VILLE",
  "annee_inscription": "2023",
  "specialisations": ["Droit Civil", "Droit Pénal"],
  "structure": "Cabinet/SCP/SELARL",
  "page_source": 1,
  "extraction_timestamp": "2026-02-12 11:10:31"
}
```

## ⚙️ Configuration

### Paramètres modifiables dans le script :
- **Délai entre requêtes** : 1.5 secondes (respectueux du serveur)
- **Timeout des requêtes** : 15 secondes
- **Sauvegardes intermédiaires** : Tous les 25 profils
- **Mode headless** : Activé par défaut

## 🛡️ Limitations connues

### Emails très limités
- Le barreau d'Évreux protège les emails contre le spam
- Seuls quelques avocats ont leur email public
- Exemple : seulement 1 email trouvé sur 137 avocats lors du test

### Spécialisations partielles
- Les spécialisations ne sont pas toujours clairement indiquées
- Détection basée sur des mots-clés dans le contenu
- Environ 1/3 des profils ont des spécialisations détectées

## 📈 Performances

- **Temps d'exécution** : ~5-6 minutes pour les 137 avocats
- **Taux de réussite global** : 99.3% (0 erreur lors du test)
- **Données de qualité** : Noms, téléphones et adresses fiables à 100%

## 🔧 Dépannage

### Erreurs courantes
1. **Timeout** : Augmenter la valeur timeout dans le script
2. **Blocage IP** : Attendre quelques minutes puis relancer
3. **Erreur réseau** : Vérifier la connexion internet

### Mode debug
Pour un debug avancé, modifier le script pour sauvegarder le HTML des pages problématiques.

## 📞 Contact

Pour toute question sur ce scraper :
- Repo principal : https://github.com/paularnd875/french-bar-scrapers
- Issues GitHub pour les bugs et améliorations

---

*Scraper développé dans le respect des conditions d'utilisation du site officiel du Barreau de l'Eure.*