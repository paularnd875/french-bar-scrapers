# Scraper Barreau de Libourne

Ce scraper extrait automatiquement les informations complètes de tous les avocats du Barreau de Libourne.

## 🏆 Résultats

- ✅ **77/77 avocats extraits** (100% de l'annuaire)
- ✅ **100% de taux de réussite** 
- ✅ **77 emails + 77 téléphones** récupérés
- ✅ **Classification prénom/nom perfectionnée**
- ✅ **Mode headless** sans interruption

## 📁 Fichiers

- `libourne_scraper.py` - Script principal d'extraction
- `corriger_classification_libourne.py` - Script de correction prénom/nom

## 🚀 Utilisation

### Installation des dépendances
```bash
pip3 install selenium
```

### Mode test (10 premiers avocats)
```bash
python3 libourne_scraper.py --test
```

### Mode complet (77 avocats)
```bash
python3 libourne_scraper.py --headless
```

### Correction de classification (si nécessaire)
```bash
python3 corriger_classification_libourne.py
```

## 📊 Données extraites

Pour chaque avocat :
- ✅ **Prénom** (correctement séparé)
- ✅ **Nom de famille** (format MAJUSCULES)
- ✅ **Email personnel/professionnel**
- ✅ **Téléphone** (format français)
- ✅ **Adresse complète** (quand disponible)
- ✅ **Code postal et ville**
- ✅ **URL du profil**

## 🎯 Spécificités techniques

### Gestion des noms composés
- ✅ **Prénoms composés** : "Anne-Claire", "Jean-Philippe"
- ✅ **Noms à particule** : "DE LUNARDO", "DE VASSELOT"
- ✅ **Noms d'usage** : "BONNER-BRISSAUD"

### Anti-détection
- ✅ **User-Agent réaliste**
- ✅ **Délais aléatoires** entre requêtes
- ✅ **Headers anti-bot**
- ✅ **Mode headless** optimisé

### Structure des URLs
Le site a 2 types d'URLs :
- **Type 1** : `/annuaire/liste-des-avocats/nom-prenom/`
- **Type 2** : `/annuaire-1/nom-prenom/`

Le scraper gère automatiquement les deux formats.

## 📈 Performance

- **Vitesse** : ~3-4 secondes par avocat
- **Durée totale** : ~6-8 minutes pour les 77 avocats
- **Fiabilité** : 100% de réussite sans blocage

## 📋 Fichiers de sortie

- `LIBOURNE_FINAL_*.csv` - Données complètes
- `LIBOURNE_FINAL_*EMAILS_*.txt` - Liste d'emails uniquement  
- `LIBOURNE_FINAL_*RAPPORT_*.txt` - Rapport détaillé

## ⚠️ Notes importantes

1. **Cookies** : Aucun banner de cookies sur ce site
2. **Pagination** : Pas de pagination, profils individuels
3. **Protection** : Site peu protégé contre le scraping
4. **Stabilité** : URLs stables, structure cohérente

## 🔧 Dépannage

### Erreur de classification prénom/nom
```bash
python3 corriger_classification_libourne.py
```

### Mode debug avec fenêtre visible
```bash
python3 libourne_scraper.py --test
# (sans --headless)
```

### Vérification des progrès
```bash
ls -la LIBOURNE_*
```

## 📞 Contact

Site officiel : https://www.barreaulibourne.fr/annuaire-1/

---

**Status** : ✅ Production Ready  
**Dernière extraction** : 12/02/2026  
**Taux de réussite** : 100%