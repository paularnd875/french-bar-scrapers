# French Bar Association Scrapers

Collection de scripts de scraping pour extraire les données des annuaires des barreaux français.

## Vue d'ensemble

Ce projet contient des scripts Python pour extraire automatiquement les informations des avocats depuis les annuaires officiels des barreaux français. Chaque script est spécialement adapté à l'architecture et aux spécificités techniques du site web du barreau correspondant.

## Barreaux couverts

- **Agen** - Barreau d'Agen
- **Alençon** - Barreau d'Alençon  
- **Annecy** - Barreau d'Annecy (302 avocats extraits)
- **Arras** - Barreau d'Arras (100 avocats extraits)
- **Besançon** - Barreau de Besançon
- **Brest** - Barreau de Brest (258 avocats extraits - 100% emails) ⭐ **NOUVEAU**
- **Caen** - Barreau de Caen  
- **Castres** - Barreau de Castres (50 avocats extraits - 100% emails)
- **Chalon-sur-Saône** - Barreau de Chalon-sur-Saône (100 avocats extraits - 100% emails) ⭐ **NOUVEAU**
- **Essonne** - Barreau de l'Essonne (346 avocats extraits - 99,4% emails) ⭐ **NOUVEAU**
- **Grenoble** - Barreau de Grenoble
- **Guadeloupe** - Barreau de la Guadeloupe
- **Le Havre** - Barreau du Havre
- **Lille** - Barreau de Lille
- **Lisieux** - Barreau de Lisieux
- **Lozère** - Barreau de la Lozère
- **Lyon** - Barreau de Lyon (extraction massive avec filtres)
- **Mayotte** - Barreau de Mayotte
- **Meuse** - Barreau de la Meuse
- **Nantes** - Barreau de Nantes
- **Senlis** - Barreau de Senlis
- **Saint-Pierre (Réunion)** - Barreau de Saint-Pierre
- **Thonon** - Barreau de Thonon-les-Bains
- **Val-de-Marne** - Barreau du Val-de-Marne

## Structure du projet

```
french-bar-scrapers/
├── README.md
├── requirements.txt
├── agen/
│   └── agen_scraper_final.py
├── alencon/
│   └── alencon_scraper_final.py
├── annecy/
│   └── annecy_scraper_final.py
├── arras/
│   └── arras_scraper_production.py
├── brest/
│   ├── brest_scraper_final.py
│   ├── brest_scraper_test_rapide.py
│   ├── run_brest_scraper.sh
│   ├── monitor_brest.py
│   └── README.md
├── castres/
│   ├── castres_scraper_final.py
│   ├── run_castres_scraper.sh
│   └── README.md
├── essonne/
│   ├── essonne_scraper_final.py
│   ├── run_essonne_complet.py
│   ├── run_essonne_test.py
│   ├── examples/
│   ├── requirements.txt
│   └── README.md
└── ...
```

## Prérequis techniques

- Python 3.7+
- Selenium WebDriver
- BeautifulSoup4
- Requests
- Pandas
- Playwright (pour certains scripts)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

## Utilisation

Chaque script est autonome et peut être exécuté indépendamment :

```bash
cd agen/
python agen_scraper_final.py

# Ou pour Brest (avec outils avancés)
cd brest/
./run_brest_scraper.sh              # Script complet
python3 brest_scraper_final.py      # Script direct
```

## Données extraites

Les scripts extraient généralement :
- **Nom et prénom** de l'avocat
- **Adresse** du cabinet
- **Numéro de téléphone**
- **Email** (quand disponible)
- **Spécialisations** juridiques
- **Date d'inscription** au barreau

## Formats de sortie

Les données sont exportées en :
- **CSV** (format principal)
- **JSON** (format détaillé avec métadonnées)

## Défis techniques résolus

### Sites avec JavaScript dynamique
- **Annecy, Lyon, Val-de-Marne** : Utilisation de Selenium pour gérer les contenus chargés en AJAX
- **Thonon** : Navigation complexe avec pagination dynamique

### Anti-bot et protection
- **Agen, Besançon** : Gestion des delays et rotation des user-agents
- **Lille** : Contournement des protections CAPTCHA

### Structures de données complexes
- **Nantes** : Extraction depuis formulaires multi-étapes
- **Grenoble** : Parsing de listes paginées avec filtres

### Sites PDF uniquement
- **Mayotte, Meuse** : OCR et parsing de PDF avec extraction structurée

## Statistiques d'extraction

| Barreau | Nombre d'avocats | Taux de réussite emails |
|---------|------------------|-------------------------|
| Annecy | 302 | 100% |
| Arras | 100 | 100% |
| Brest | 258 | 100% |
| Lyon | 2,500+ | 95% |
| Lille | 1,600+ | 98% |
| Val-de-Marne | 400+ | 92% |
| Castres | 50 | 100% |
| Autres | Variable | 85-100% |

## Notes importantes

⚠️ **Conformité légale** : Ces scripts sont destinés à un usage de recherche et doivent respecter les conditions d'utilisation des sites web ciblés.

⚠️ **Rate limiting** : Tous les scripts incluent des délais entre les requêtes pour éviter la surcharge des serveurs.

⚠️ **Maintenance** : Les sites web évoluent régulièrement. Les scripts peuvent nécessiter des ajustements.

## Date de développement

Scripts développés entre janvier et février 2026, testés et validés sur les versions actuelles des sites des barreaux.

## Contribution

Chaque script a été développé et testé pour un barreau spécifique. Les contributions pour améliorer la robustesse ou ajouter de nouveaux barreaux sont les bienvenues.