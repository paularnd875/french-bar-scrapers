# 🚀 Scraper Barreau de Castres

**Extraction complète des avocats du Barreau de Castres**

Site web : https://avocats-castres.fr/annuaire-avocats/

## ✨ Fonctionnalités

✅ **Extraction complète** - Tous les avocats du barreau (≈50 avocats)  
✅ **Gestion automatique** des cookies  
✅ **Mode headless** - Pas d'interface graphique pour ne pas déranger  
✅ **100% de réussite** pour emails, téléphones et spécialisations  

## 📊 Données extraites

- ✅ **Nom et prénom** (extraits automatiquement)
- ✅ **Email** (100% de réussite - 50/50)
- ✅ **Téléphone principal** (100% de réussite - 50/50)
- ✅ **Mobile et télécopie** 
- ✅ **Adresse complète** avec ville
- ✅ **Année d'inscription** au barreau
- ✅ **Date de prestation de serment** (100% de réussite - 50/50)
- ✅ **Spécialisations juridiques** (100% de réussite - 50/50)
- ✅ **Structure/Cabinet** (SELARL, SCP, etc. - 36% des avocats)

## 🚀 Utilisation

### Méthode rapide
```bash
./run_castres_scraper.sh
```

### Méthode directe
```bash
# Test rapide (3 avocats)
python3 castres_scraper_final.py --limit 3

# Extraction complète (mode headless - recommandé)
python3 castres_scraper_final.py

# Mode visuel pour debug
python3 castres_scraper_final.py --visual --limit 5
```

## 📁 Fichiers générés

Le script génère automatiquement :
- `castres_COMPLET_[timestamp].json` - Données complètes
- `castres_COMPLET_[timestamp].csv` - Format Excel
- `castres_EMAILS_SEULEMENT_[timestamp].txt` - Emails seulement
- `castres_RAPPORT_COMPLET_[timestamp].txt` - Rapport détaillé

## ⏱️ Performance

- **Nombre d'avocats** : 50 (complet)
- **Temps d'exécution** : ~4-5 minutes
- **Vitesse moyenne** : 0.2 avocat/seconde
- **Taux de réussite** : 100% pour les données principales

## 📈 Résultats obtenus (dernière extraction)

```
📊 50 avocats traités
📧 Emails trouvés: 50/50 (100.0%)
📞 Téléphones trouvés: 50/50 (100.0%)
🏢 Structures trouvées: 18/50 (36.0%)
⚖️  Spécialisations: 50/50 (100.0%)
📅 Dates de serment: 50/50 (100.0%)
```

## 🛠️ Prérequis

```bash
pip install selenium
```

Chrome doit être installé.

## 🔧 Caractéristiques techniques

- **Framework** : Selenium WebDriver
- **Mode** : Headless par défaut
- **Anti-détection** : User-Agent personnalisé, pauses naturelles
- **Robustesse** : Extraction multiple (meta, contenu, patterns)
- **Format de sortie** : JSON, CSV, TXT

## 📝 Notes

- Le site utilise des métadonnées riches facilitant l'extraction
- Pas de pagination - tous les avocats sur une seule page
- Extraction très fiable grâce aux multiples sources de données
- Respect du serveur avec pauses automatiques

## 🎯 Spécificités du site

- **URL** : https://avocats-castres.fr/annuaire-avocats/
- **Type** : WordPress avec métadonnées structurées
- **Cookies** : Tarteaucitron (géré automatiquement)
- **Structure** : Fiches individuelles par avocat

---

*Développé dans le cadre du projet French Bar Scrapers*