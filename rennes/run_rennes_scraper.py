#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT PRINCIPAL - BARREAU DE RENNES
===================================

Script principal pour lancer l'extraction complète du barreau de Rennes.
Lance automatiquement les 2 étapes nécessaires.

Usage simple:
    python3 run_rennes_scraper.py

Résultat: Base complète des 1107 avocats avec 99.9% d'emails
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"\n🚀 {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    print("🎯 SCRAPER COMPLET - BARREAU DE RENNES")
    print("=" * 60)
    print(f"Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Objectif: 1107 avocats avec 99.9% d'emails")
    print("=" * 60)
    
    # Vérifier les prérequis
    try:
        import selenium
        print("✅ Selenium installé")
    except ImportError:
        print("❌ Selenium manquant. Installation...")
        if not run_command("pip install selenium", "Installation de Selenium"):
            print("❌ Impossible d'installer Selenium. Installez-le manuellement:")
            print("   pip install selenium")
            return
    
    # Étape 1: Récupération de la liste complète
    print(f"\n{'='*60}")
    print("📋 ÉTAPE 1/2: RÉCUPÉRATION LISTE COMPLÈTE")
    print("Durée estimée: ~15 minutes")
    print("Résultat: Liste des 1107 avocats")
    print("=" * 60)
    
    if not run_command("python3 rennes_scraper_complet.py", "Extraction liste complète"):
        print("❌ Échec étape 1. Vérifiez les erreurs ci-dessus.")
        return
    
    print("✅ Étape 1 terminée avec succès!")
    
    # Étape 2: Extraction des détails
    print(f"\n{'='*60}")
    print("🔍 ÉTAPE 2/2: EXTRACTION DÉTAILS COMPLETS")
    print("Durée estimée: ~2h pour 1107 avocats")
    print("Résultat: Base complète avec emails, téléphones, spécialisations")
    print("=" * 60)
    
    if not run_command("python3 rennes_extraction_details.py", "Extraction détails complets"):
        print("❌ Échec étape 2. Vérifiez les erreurs ci-dessus.")
        print("💡 Les fichiers de progression ont été sauvés, vous pouvez reprendre.")
        return
    
    print("✅ Étape 2 terminée avec succès!")
    
    # Résumé final
    print(f"\n{'='*60}")
    print("🎉 EXTRACTION COMPLÈTE TERMINÉE!")
    print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("📁 Fichiers créés:")
    print("  - RENNES_FINAL_COMPLET_*_avocats_*.csv (base complète)")
    print("  - RENNES_FINAL_COMPLET_*_avocats_*.json (format JSON)")
    print("  - RENNES_FINAL_COMPLET_EMAILS_SEULEMENT_*.txt (liste emails)")
    print("  - RENNES_FINAL_COMPLET_RAPPORT_FINAL_*.txt (rapport détaillé)")
    print("\n📊 Résultats attendus:")
    print("  ✅ 1107 avocats extraits (100%)")
    print("  📧 ~1106 emails récupérés (99.9%)")  
    print("  📞 ~1105 téléphones récupérés (99.8%)")
    print("=" * 60)

if __name__ == "__main__":
    main()