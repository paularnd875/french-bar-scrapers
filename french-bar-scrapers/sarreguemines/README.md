# Scraper Barreau de Sarreguemines

## 📋 Description

Scraper automatisé pour extraire la liste complète des avocats du Barreau de Sarreguemines.

**URL cible**: https://www.avocats-sarreguemines.fr/annuaire-des-avocats-du-barreau.htm

## ✅ Données extraites

- ✅ **Prénoms et noms** (100%) - Gestion parfaite des noms composés
- ✅ **Numéros de téléphone** (100%)
- ✅ **Adresses complètes** (100%) - **Nettoyées du HTML parasite**
- ✅ **URLs sources** (100%) - Lien vers chaque fiche
- ⚠️ **Emails** (0%) - Formulaires de contact uniquement
- ⚠️ **Années d'inscription** (0%) - Non disponibles sur ce site
- ⚠️ **Spécialisations** (0%) - Non détaillées sur les fiches publiques

## 🚀 Utilisation

### Installation des dépendances

```bash
pip install requests beautifulsoup4 pandas
```

### Lancement du script

```bash
# Scraping complet (64 avocats)
python sarreguemines_scraper.py

# Mode test (10 premiers avocats)
python sarreguemines_scraper.py 10
```

## 📊 Résultats

Le script génère automatiquement :

1. **CSV** : `SARREGUEMINES_COMPLET_64_avocats_YYYYMMDD_HHMMSS.csv`
2. **JSON** : `SARREGUEMINES_COMPLET_64_avocats_YYYYMMDD_HHMMSS.json`  
3. **Rapport** : `SARREGUEMINES_RAPPORT_COMPLET_YYYYMMDD_HHMMSS.txt`
4. **Emails** : `SARREGUEMINES_EMAILS_YYYYMMDD_HHMMSS.txt` (si trouvés)

## 🎯 Caractéristiques techniques

### Gestion des noms composés
- **Prénoms composés** : Marie-Anne, Jean Christophe, Saskia-Lysa
- **Noms composés** : GIANNETTI-LANG, PIETERS-FIMBEL, MARTIN-LAVIOLETTE

### Extraction robuste
- Gestion automatique des cookies
- Pause intelligente entre requêtes
- Récupération exhaustive (0 avocat manqué)
- Nettoyage automatique des données

## 📈 Statistiques du dernier run

- **Total** : 64 avocats extraits (100% de l'annuaire)
- **Prénoms/Noms** : 64/64 (100%)
- **Téléphones** : 64/64 (100%) 
- **Adresses** : 64/64 (100%)
- **Emails** : 0/64 (0%) - Non publics sur ce site
- **Prénoms composés gérés** : ~10 cas

## ⚠️ Limitations identifiées

1. **Spécialisations** : Les fiches publiques ne contiennent pas de spécialisations détaillées
2. **Emails** : Uniquement des formulaires de contact, pas d'emails directs
3. **Années d'inscription** : Information non affichée publiquement

## 🔧 Configuration

Le script utilise :
- **User-Agent** : Chrome moderne pour éviter les blocages
- **Délais** : Pause de 0.5-1.5s entre requêtes, 2-4s tous les 10 avocats
- **Encodage** : UTF-8 avec BOM pour Excel
- **Format de sortie** : CSV compatible Excel, JSON structuré

## 📝 Exemple de données extraites

```json
{
  "prenom": "Marie-Anne",
  "nom": "BURON", 
  "nom_complet": "Maître Marie-Anne BURON",
  "telephone": "0354812096",
  "adresse": "46 Rue Nationale 57600 FORBACH",
  "source_url": "https://www.avocats-sarreguemines.fr/page/annuaire/maitre-marie-anne-buron-14.htm"
}
```

## 🕐 Temps d'exécution

- **Mode test (10 avocats)** : ~30 secondes
- **Mode complet (64 avocats)** : ~3-5 minutes

## 🔄 Mise à jour

Pour mettre à jour la base de données, relancer simplement :

```bash
python sarreguemines_scraper.py
```

Les nouveaux fichiers seront générés avec timestamp automatique.

---

## 🔄 Historique des améliorations

**Version 2.0 (Février 2026)**
- ✅ **Correction des adresses** : Nettoyage complet du HTML parasite (`<span class="btnTel..."`)  
- ✅ **Gestion optimisée des spécialisations** : Champs laissés vides si non disponibles (pas de fausses données)
- ✅ **Amélioration de l'extraction** : Pattern matching plus robuste pour les adresses
- ✅ **Gestion parfaite des noms composés** : 3 prénoms composés et 7 noms composés détectés

---

*Dernière mise à jour : 20 Février 2026*  
*Status : ✅ Fonctionnel - Extraction complète validée avec corrections*