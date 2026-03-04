#!/usr/bin/env python3
"""
Lanceur automatique du scraping Arras Enhanced
Configuration automatique pour lancement en arrière-plan
"""

from arras_scraper_enhanced import ArrasEnhancedScraper

def main():
    """Lance le scraping avec configuration automatique"""
    print("🚀 LANCEMENT AUTOMATIQUE SCRAPER ARRAS ENHANCED")
    print("=" * 55)
    
    # Configuration automatique
    delay = 2  # 2 secondes entre requêtes
    resume = True  # Reprise automatique activée
    
    print(f"⚙️ Configuration automatique:")
    print(f"   • Délai: {delay}s")
    print(f"   • Reprise: {'Activée' if resume else 'Désactivée'}")
    print("🚀 Démarrage du scraping enhanced...\n")
    
    # Lancement du scraper
    scraper = ArrasEnhancedScraper(delay_between_requests=delay)
    
    # Chargement automatique de session existante si disponible
    if scraper.load_session():
        print(f"🔄 Session existante trouvée: {len(scraper.lawyers_data)} avocats déjà traités")
        print("✅ Reprise automatique de la session\n")
    
    success = scraper.run_enhanced_scraping(resume_session=resume)
    
    if success:
        print("\n🎉 SCRAPING ENHANCED TERMINÉ AVEC SUCCÈS!")
        print("📁 Fichiers générés:")
        print("   • JSON avec métadonnées complètes")
        print("   • CSV pour analyse")
        print("   • Rapport détaillé")
        print("   • Logs d'exécution")
        
        # Statistiques finales
        total = len(scraper.lawyers_data)
        emails = scraper.stats['emails_found']
        phones = scraper.stats['phones_found']
        
        print(f"\n📊 Résultats:")
        print(f"   • Total avocats: {total}")
        print(f"   • Emails trouvés: {emails} ({emails/total*100:.1f}%)" if total > 0 else "   • Emails: 0")
        print(f"   • Téléphones trouvés: {phones} ({phones/total*100:.1f}%)" if total > 0 else "   • Téléphones: 0")
        
        # Score moyen
        if scraper.lawyers_data:
            avg_score = sum(l.get('data_quality_score', 0) for l in scraper.lawyers_data) / len(scraper.lawyers_data)
            print(f"   • Score qualité moyen: {avg_score:.1f}/10")
        
    else:
        print("\n❌ Le scraping enhanced a échoué.")
        print("📋 Vérifiez les logs pour plus d'informations.")

if __name__ == "__main__":
    main()