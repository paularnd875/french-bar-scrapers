# Barreau de Poitiers - Scraper

## 📋 Informations générales

- **Barreau**: Poitiers
- **URL**: https://www.avocats-poitiers.com/espaceprive/annuaire/
- **Total avocats**: ~293
- **Dernière mise à jour**: Mars 2026
- **Statut**: ✅ Opérationnel

## 🎯 Résultats attendus

- **Avocats extraits**: 275/293 (93.9%)
- **Emails valides**: 275/275 (100%)
- **Téléphones valides**: 274/275 (99.6%)
- **Années de serment**: 275/275 (100%)

## 🛠️ Utilisation

### Installation des dépendances

```bash
pip install requests beautifulsoup4 lxml
```

### Lancement du scraper

```bash
cd poitiers
python3 poitiers_scraper.py
```

### Avec timeout (recommandé)

```bash
timeout 300 python3 poitiers_scraper.py
```

## 📁 Fichiers générés

Le script génère automatiquement 3 fichiers avec horodatage :

1. **CSV**: `POITIERS_FINAL_XXX_avocats_YYYYMMDD_HHMMSS.csv`
2. **JSON**: `POITIERS_FINAL_XXX_avocats_YYYYMMDD_HHMMSS.json`
3. **Emails**: `POITIERS_FINAL_EMAILS_XXX_uniques_YYYYMMDD_HHMMSS.txt`

## 🔧 Spécificités techniques

### Méthode utilisée
- **Type**: Scraping AJAX via API Ultimate Member
- **Endpoint**: `/espaceprive/wp-admin/admin-ajax.php`
- **Authentification**: Nonce validé (52b4077f34)
- **Pagination**: 20 pages de 15 avocats max

### Données extraites
- Nom et prénom (parsing intelligent des noms composés)
- Email (extraction depuis HTML)
- Téléphone (extraction depuis HTML)
- Année de serment (regex sur texte libre)
- Barreau d'appartenance
- Adresse/Ville
- Spécialisations
- Cabinet d'exercice
- Lien vers profil
- ID utilisateur

### Gestion des noms composés

Le script gère intelligemment les noms composés français :

- **Particules nobiliaires**: DE, LE, AL, DA
- **Exemples traités**:
  - `AL MIAH Emmanuel` → Nom: "AL MIAH", Prénom: "Emmanuel"
  - `DE LA ROCCA Aurélia` → Nom: "DE LA ROCCA", Prénom: "Aurélia"
  - `BETOULLE BENABEN Marion` → Nom: "BETOULLE BENABEN", Prénom: "Marion"

## ⚠️ Points d'attention

1. **Nonce temporaire**: La valeur du nonce (52b4077f34) peut expirer
2. **Rate limiting**: Pause de 1s entre pages pour éviter le blocage
3. **Détection doublons**: Système intégré pour éviter les entrées dupliquées

## 🔍 Dépannage

### Erreur "Nonce incorrect"
Si vous obtenez cette erreur, le nonce a expiré :

1. Visitez l'annuaire: https://www.avocats-poitiers.com/espaceprive/annuaire/
2. Inspectez le code source pour trouver le nouveau nonce
3. Mettez à jour la variable `self.nonce` dans le script

### Erreur de connexion
- Vérifiez votre connexion internet
- Le site peut être temporairement indisponible
- Réessayez avec un timeout plus important

### Données incomplètes
- Certains avocats n'ont pas renseigné tous leurs champs
- C'est normal, le script extrait toutes les données disponibles

## 📊 Historique des performances

| Date | Avocats | Taux | Emails | Téléphones | Années |
|------|---------|------|---------|------------|---------|
| Mars 2026 | 275/293 | 93.9% | 100% | 99.6% | 100% |

## 🚀 Améliorations futures

- [ ] Auto-detection du nonce
- [ ] Gestion des erreurs réseau avancée
- [ ] Export Excel (.xlsx)
- [ ] Validation format téléphone

---

**Développé par**: Paul Arnould  
**Repository**: https://github.com/paularnd875/french-bar-scrapers  
**Support**: Issues GitHub