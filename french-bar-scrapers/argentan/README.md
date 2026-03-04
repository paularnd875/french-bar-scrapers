# 📋 Scraper Barreau d'Argentan

## 🎯 Vue d'ensemble
Ce scraper extrait **automatiquement** la liste complète des avocats du Barreau d'Argentan depuis leur site officiel : http://www.barreau-argentan.fr

## 📊 Résultats
- ✅ **20 avocats extraits** (100% du barreau)
- 📧 **100% avec email** (20/20)
- 📞 **100% avec téléphone** (20/20)  
- 🌐 **55% avec site web** (11/20)
- 📍 **Adresses complètes** pour la majorité

## 🚀 Utilisation

### Installation des dépendances
```bash
pip install selenium beautifulsoup4 fake-useragent
```

### Lancement du scraper
```bash
python argentan_scraper_production.py
```

## 📁 Fichiers générés
- `argentan_COMPLET_[timestamp].csv` - **Données Excel** avec tous les champs
- `argentan_EMAILS_ONLY_[timestamp].txt` - **Liste pure des emails**
- `argentan_COMPLET_[timestamp].json` - **Données structurées JSON**
- `argentan_RAPPORT_COMPLET_[timestamp].txt` - **Rapport détaillé**

## 📋 Données extraites pour chaque avocat
| Champ | Description | Taux de réussite |
|-------|-------------|------------------|
| **Prénom** | Prénom de l'avocat | 100% |
| **Nom** | Nom de famille | 100% |
| **Email** | Adresse email professionnelle | 100% |
| **Téléphone** | Numéro de téléphone du cabinet | 100% |
| **Fax** | Numéro de fax (si disponible) | ~40% |
| **Site web** | Site internet du cabinet | 55% |
| **Adresse** | Adresse complète du cabinet | ~80% |
| **Structure** | Type de cabinet (SCP, Cabinet, etc.) | ~60% |
| **Spécialisations** | Domaines juridiques (si mentionnés) | Variable |
| **Année inscription** | Année d'inscription au barreau | Variable |

## 🔧 Caractéristiques techniques
- **Navigation naturelle** : Contourne les protections anti-bot
- **Gestion automatique des cookies**
- **Mode headless** : Fonctionne en arrière-plan sans ouvrir de fenêtres
- **Extraction précise** : Parsing intelligent des fiches individuelles
- **Délais humains** : Respecte le serveur avec des pauses aléatoires
- **Sauvegarde multiple** : CSV, JSON, TXT et rapport détaillé

## ⚠️ Notes importantes
- Le barreau d'Argentan a **uniquement 20 avocats** inscrits
- Malgré l'URL "de-a-a-d.html", tous les avocats (A à V) sont sur la même page
- Le script fonctionne en mode headless pour ne pas interférer avec votre travail
- Extraction complète en ~2 minutes

## 📅 Dernière extraction
- **Date** : 09/02/2026 à 17:39:00
- **Nombre d'avocats** : 20
- **Taux de succès** : 100%

## 🎉 Exemple de données extraites
```csv
prenom,nom,email,telephone,site_web
Jean,Michel ARIN,jm.arin.hla@orange.fr,0233660226,huaume-lepelletier-arin.fr
Marianne,BARRY,m.barry.avocat@orange.fr,0233667314,barrymarianne-avocat-flers.fr
Céline,BOLLOTTE,cabinet@lerayer-avocats.com,0233672571,www.lerayer-avocats.com
```

---
*Scraper développé pour l'extraction automatisée des données publiques du Barreau d'Argentan*