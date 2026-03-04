# 🏛️ Scraper Barreau d'Orléans

## 📋 Description

Scraper complet et optimisé pour extraire **tous les 220 avocats** du Barreau d'Orléans avec séparation parfaite des noms composés.

**URL cible:** https://www.ordre-avocats-orleans.fr/annuaire-avocat-orleans/

## ✨ Fonctionnalités

- ✅ **Extraction exhaustive** : Tous les 220 avocats du barreau
- ✅ **Séparation parfaite des noms** : Gestion intelligente des noms composés et particules
- ✅ **Mode headless** : Exécution discrète sans interface graphique  
- ✅ **Extraction d'emails** : Récupération des adresses email disponibles
- ✅ **Exports multiples** : CSV, JSON, TXT et rapport détaillé
- ✅ **Gestion anti-détection** : User-agent et options optimisées

## 🎯 Données extraites

| Champ | Description | Taux de couverture |
|-------|-------------|-------------------|
| **Prénom** | Prénom de l'avocat | 100% |
| **Nom** | Nom de famille | 100% |
| **Email** | Adresse email professionnelle | ~15.9% |
| **Adresse** | Adresse du cabinet | ~90.5% |
| **Spécialisations** | Domaines de spécialisation | Variable |
| **Activités dominantes** | Activités principales | ~7.7% |
| **URL source** | Lien vers la fiche avocat | 100% |

## 🚀 Utilisation

### Installation des dépendances

```bash
pip install selenium requests beautifulsoup4
```

### Exécution

```bash
python3 orleans_scraper_final.py
```

### Résultats générés

- `ORLEANS_FINAL_220_avocats_YYYYMMDD_HHMMSS.csv`
- `ORLEANS_FINAL_220_avocats_YYYYMMDD_HHMMSS.json`  
- `ORLEANS_FINAL_EMAILS_YYYYMMDD_HHMMSS.txt`
- `ORLEANS_FINAL_RAPPORT_YYYYMMDD_HHMMSS.txt`

## 🎨 Spécificités techniques

### Séparation parfaite des noms composés

Le scraper inclut un dictionnaire exhaustif pour gérer correctement les cas complexes :

**✅ Noms avec particules :**
- `Sandra DE BARROS` → Prénom: `Sandra` | Nom: `DE BARROS`
- `Clémence LE MARCHAND` → Prénom: `Clémence` | Nom: `LE MARCHAND`

**✅ Noms composés :**
- `Anne MADRID FOUSSEREAU` → Prénom: `Anne` | Nom: `MADRID FOUSSEREAU`
- `Mélanie BEGUIDE BONOMA` → Prénom: `Mélanie` | Nom: `BEGUIDE BONOMA`

**✅ Prénoms composés :**
- `Jean-Michel LICOINE` → Prénom: `Jean-Michel` | Nom: `LICOINE`
- `Marie-Françoise CASADEI-JUNG` → Prénom: `Marie-Françoise` | Nom: `CASADEI-JUNG`

### Extraction d'emails multi-méthodes

1. **Liens mailto** : Détection des liens `href="mailto:"`
2. **Expressions régulières** : Recherche pattern email dans le texte
3. **Validation automatique** : Vérification format email

## 📊 Résultats type

```
🎉 EXTRACTION FINALE TERMINÉE!
   👥 Total avocats: 220
   📧 Emails trouvés: 35
   🏢 Adresses: 199
   📈 Taux d'emails: 15.9%
```

## 🔧 Configuration

### Options Chrome optimisées

```python
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox") 
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
```

### Anti-détection

```python
chrome_options.add_argument("--user-agent=Mozilla/5.0...")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
```

## 🏗️ Architecture

```
orleans_scraper_final.py
├── setup_driver()              # Configuration Chrome
├── split_lawyer_name_perfectly() # Séparation noms
├── extract_lawyer_info()       # Extraction données
├── scrape_orleans_lawyers()    # Scraping principal  
├── save_results()              # Sauvegarde fichiers
└── main()                      # Orchestration
```

## 📝 Format CSV

```csv
prenom,nom,nom_complet,email,annee_inscription,specialisations,activites_dominantes,cabinet,adresse,telephone,source_url
Hélène,KROVNIKOFF,Maître Hélène KROVNIKOFF,h.krovnikoff@derubay.fr,,,,,2 boulevard pierre segelle,,https://www.ordre-avocats-orleans.fr/avocats/maitre-helene-krovnikoff/
```

## ⚙️ Prérequis système

- **Python 3.7+**
- **Chrome/Chromium** installé
- **ChromeDriver** dans le PATH
- Connexion internet stable

## 📈 Performance

- **Temps d'exécution** : ~5-10 minutes
- **Taux de succès** : 100% (220/220 avocats)
- **Mode headless** : Oui (discret)
- **Gestion erreurs** : Robuste avec retry

## 🆕 Historique des versions

### v1.0 (2026-02-17)
- ✅ Extraction complète 220 avocats
- ✅ Séparation parfaite noms composés  
- ✅ Mode headless optimisé
- ✅ Export multi-formats
- ✅ Rapport détaillé avec statistiques

## 📞 Support

En cas de problème :
1. Vérifier que Chrome est installé
2. Mettre à jour ChromeDriver
3. Vérifier la connexion internet
4. Consulter les logs d'erreur

---

*Scraper développé pour le projet french-bar-scrapers*