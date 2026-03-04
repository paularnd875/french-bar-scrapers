# Guide d'Utilisation Rapide - Scraper Nevers

## 🚀 Lancement Rapide

### Option 1: Script automatique (recommandé)
```bash
cd nevers
./run.sh
```

### Option 2: Exécution manuelle
```bash
cd nevers
pip install -r requirements.txt
python3 nevers_scraper_complete.py
```

## 📊 Résultats Attendus

Le script va générer automatiquement :

1. **CSV complet** : `NEVERS_FINAL_COMPLETE_49_avocats_YYYYMMDD_HHMMSS.csv`
   - Toutes les données des 49 avocats
   - Format: nom_complet, prenom, nom, email, telephone, adresse, etc.

2. **Liste emails** : `NEVERS_EMAILS_FINAUX_49_YYYYMMDD_HHMMSS.txt`
   - 49 emails purs (1 par ligne)
   - Idéal pour import dans vos outils

3. **Rapport détaillé** : `NEVERS_RAPPORT_YYYYMMDD_HHMMSS.txt`
   - Statistiques complètes
   - Résumé de l'extraction

## ⏱️ Temps d'Exécution

- **Durée** : ~45 minutes
- **Taux de réussite** : 100%
- **Sauvegarde automatique** : Tous les 10 avocats

## 🔄 Mise à Jour de Vos Bases

Pour mettre à jour vos données :

1. **Télécharger le script**:
   ```bash
   git clone https://github.com/paularnd875/french-bar-scrapers.git
   cd french-bar-scrapers/nevers
   ```

2. **Lancer l'extraction**:
   ```bash
   ./run.sh
   ```

3. **Récupérer les fichiers** générés dans le dossier `results_YYYYMMDD_HHMMSS/`

## 📞 Support

- **Taux de réussite garanti** : 100% pour les emails
- **Robustesse** : Gestion automatique des erreurs réseau
- **Fiabilité** : Script testé et validé sur l'ensemble de l'annuaire

**URL de référence** : https://github.com/paularnd875/french-bar-scrapers/tree/main/nevers