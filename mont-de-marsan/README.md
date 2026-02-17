# 🏛️ Scraper Barreau de Mont-de-Marsan

## 📋 Description

Scraper complet et optimisé pour extraire **toutes les informations** des avocats du Barreau de Mont-de-Marsan.

**Version finale** : prête pour la production et la réutilisation future (testé en février 2026).

---

## 🎯 Données extraites

| Champ | Description | Taux de réussite attendu |
|-------|-------------|-------------------------|
| `civilite` | Civilité (Maître) | 100% |
| `prenom` | Prénom | 100% |
| `nom` | Nom de famille | 100% |
| `email` | Adresse email (décodée) | ~100% |
| `telephone` | Numéro de téléphone | ~90% |
| `fax` | Numéro de fax | ~70% |
| `adresse` | Adresse complète | ~85% |
| `cabinet` | Nom du cabinet/structure | ~80% |
| `annee_inscription` | Année d'inscription au barreau | ~95% |
| `specialisations` | Domaines de spécialisation juridique | ~60% |
| `detail_url` | URL de la fiche détaillée | 100% |
| `source_url` | URL source pour vérification | 100% |

---

## 🚀 Utilisation

### Installation des dépendances

```bash
pip3 install requests beautifulsoup4
```

### Lancement

**Mode test (10 avocats) :**
```bash
python3 scraper.py
```

**Mode production (tous les avocats) :**
- Ouvrir le fichier `scraper.py`
- Ligne 485 : changer `TEST_MODE = True` en `TEST_MODE = False`
- Sauvegarder et lancer

---

## 📁 Fichiers générés

Pour chaque exécution, 4 fichiers sont créés :

| Fichier | Description |
|---------|-------------|
| `MONTDEMARSAN_[MODE]_[NB]_avocats_[DATE].csv` | **Fichier principal** - Données structurées pour Excel/analyse |
| `MONTDEMARSAN_[MODE]_[NB]_avocats_[DATE].json` | Données avec métadonnées pour intégration API |
| `MONTDEMARSAN_EMAILS_ONLY_[DATE].txt` | Liste des emails seulement (un par ligne) |
| `MONTDEMARSAN_RAPPORT_COMPLET_[DATE].txt` | Rapport détaillé avec statistiques |

**Exemple de noms :**
- `MONTDEMARSAN_TEST_10_avocats_20260216_174500.csv`
- `MONTDEMARSAN_PRODUCTION_69_avocats_20260216_180000.csv`

---

## ⚙️ Configuration avancée

### Modifier le nombre d'avocats en mode test
```python
# Ligne 486
MAX_LAWYERS_TEST = 5  # Au lieu de 10
```

### Ajuster les délais entre requêtes
```python
# Ligne 334
time.sleep(random.uniform(1, 2))  # Entre 1 et 2 secondes
```

### Personnaliser les champs exportés
```python
# Ligne 360 - modifier fieldnames
fieldnames = [
    'prenom', 'nom', 'email',  # Champs de base
    'cabinet', 'annee_inscription'  # Ajouter/supprimer selon besoins
]
```

---

## 🔍 Fonctionnalités techniques

### ✅ Points forts
- **Sans Selenium** : Plus rapide, pas de navigateur visible
- **Décodage automatique** des emails encodés URL
- **Patterns robustes** pour téléphones, adresses, cabinets
- **Gestion d'erreurs** complète avec sauvegarde partielle
- **Respect du site** : délais entre requêtes
- **Statistiques détaillées** avec taux de réussite

### 🛡️ Robustesse
- Gestion des interruptions (Ctrl+C)
- Sauvegarde automatique en cas d'erreur
- Patterns multiples pour chaque type de donnée
- Nettoyage automatique des données extraites

---

## 🐛 Dépannage

### Le script ne trouve aucun avocat
**Cause probable :** Structure HTML du site modifiée
**Solution :** Vérifier que l'URL `https://www.barreau-montdemarsan.org/barreau-de-mont-de-marsan/annuaire-des-avocats.htm` est toujours valide

### Emails non décodés
**Cause :** Nouvel encodage utilisé par le site
**Solution :** Modifier la fonction `decode_email()` ligne 74

### Téléphones/adresses manquants
**Solution :** Ajuster les patterns regex lignes 87-134

---

## 📊 Historique des versions

| Version | Date | Améliorations |
|---------|------|---------------|
| 1.0 FINALE | Fév 2026 | Version optimale - prête production |
| 0.9 | Fév 2026 | Correction patterns, décodage emails |
| 0.8 | Fév 2026 | Ajout extraction cabinets/spécialisations |
| 0.7 | Fév 2026 | Premier fonctionnel avec emails |

---

## 🔄 Réutilisation future

### Avant de relancer (dans 1 an)
1. **Vérifier l'URL** : Le site existe-t-il toujours ?
2. **Test rapide** : Lancer en mode test d'abord
3. **Vérifier les patterns** : La structure HTML a-t-elle changé ?
4. **Mettre à jour les dépendances** : `pip3 install --upgrade requests beautifulsoup4`

### Adaptation à d'autres barreaux
Le script peut être adapté pour d'autres barreaux en modifiant :
- `self.annuaire_url` (ligne 32)
- Les patterns d'extraction selon la structure HTML du nouveau site
- Les sélecteurs CSS pour les éléments d'avocats

---

## 📧 Support

Ce script a été optimisé pour fonctionner de manière autonome. En cas de problème :

1. **Vérifier les URLs** sont toujours valides
2. **Tester avec 1-2 avocats** d'abord 
3. **Examiner les rapports générés** pour identifier les champs manquants
4. **Ajuster les patterns** si nécessaire

---

## ⚖️ Mentions légales

- ✅ **Usage autorisé** : Extraction d'informations publiques
- ✅ **Respect du site** : Délais entre requêtes
- ✅ **Pas de spam** : Une seule visite par page
- ⚠️ **Usage commercial** : Vérifier les conditions d'utilisation du site

---

*Scraper créé par Claude Code AI - Février 2026*  
*Optimisé pour la production et la réutilisation future*