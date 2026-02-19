#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de nettoyage des emails génériques pour le Barreau de Saintes
Ce script supprime les emails génériques qui apparaissent sur toutes les fiches
"""

import pandas as pd
from datetime import datetime
import argparse
import sys
import os

def clean_generic_emails(csv_file, threshold=50):
    """
    Nettoyer les emails génériques d'un fichier CSV
    
    Args:
        csv_file (str): Chemin vers le fichier CSV à nettoyer
        threshold (int): Seuil pour considérer un email comme générique
    
    Returns:
        str: Chemin vers le fichier nettoyé
    """
    
    print(f"🧹 Nettoyage des emails génériques dans: {csv_file}")
    print(f"🎯 Seuil de détection générique: {threshold} occurrences")
    
    # Vérifier que le fichier existe
    if not os.path.exists(csv_file):
        print(f"❌ Fichier non trouvé: {csv_file}")
        return None
    
    # Charger le fichier
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"📊 Chargé {len(df)} avocats")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return None
    
    # Analyser la fréquence des emails
    email_counts = {}
    for emails_str in df['emails']:
        if pd.notna(emails_str) and emails_str:
            emails = [email.strip() for email in emails_str.split(';')]
            for email in emails:
                if email:
                    email_counts[email] = email_counts.get(email, 0) + 1
    
    print(f"\n📈 Fréquence des emails:")
    for email, count in sorted(email_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {email}: {count} occurrences")
    
    # Identifier les emails génériques
    generic_emails = {email for email, count in email_counts.items() if count >= threshold}
    print(f"\n🎯 Emails identifiés comme génériques: {generic_emails}")
    
    # Fonction de nettoyage
    def clean_emails_remove_generic(email_str):
        if pd.isna(email_str) or not email_str:
            return ""
        
        emails = [email.strip() for email in email_str.split(';')]
        specific_emails = [email for email in emails if email and email not in generic_emails]
        
        return "; ".join(specific_emails) if specific_emails else ""
    
    # Appliquer le nettoyage
    print(f"\n🧹 Suppression des emails génériques...")
    df['emails'] = df['emails'].apply(clean_emails_remove_generic)
    
    # Compter les résultats
    avocats_avec_emails = sum(1 for emails in df['emails'] if emails and pd.notna(emails))
    
    # Collecter tous les emails restants
    all_remaining_emails = []
    for emails_str in df['emails']:
        if emails_str and pd.notna(emails_str):
            all_remaining_emails.extend([email.strip() for email in emails_str.split(';')])
    
    unique_specific_emails = sorted(list(set([email for email in all_remaining_emails if email])))
    
    # Générer les noms de fichiers de sortie
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = csv_file.replace('.csv', '')
    
    # Sauvegarder le fichier principal nettoyé
    clean_csv = f"{base_name}_CLEAN_{timestamp}.csv"
    df.to_csv(clean_csv, index=False, encoding='utf-8')
    
    # Créer un fichier avec seulement les avocats ayant des emails spécifiques
    df_with_emails = df[df['emails'].notna() & (df['emails'] != "")].copy()
    specific_csv = f"{base_name}_AVEC_EMAILS_SPECIFIQUES_{len(df_with_emails)}avocats_{timestamp}.csv"
    df_with_emails.to_csv(specific_csv, index=False, encoding='utf-8')
    
    # Fichier des emails spécifiques uniquement
    emails_file = f"{base_name}_EMAILS_SPECIFIQUES_{len(unique_specific_emails)}emails_{timestamp}.txt"
    with open(emails_file, 'w', encoding='utf-8') as f:
        for email in unique_specific_emails:
            f.write(email + '\n')
    
    # Rapport de nettoyage
    report_file = f"{base_name}_RAPPORT_NETTOYAGE_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"RAPPORT DE NETTOYAGE - BARREAU DE SAINTES - {timestamp}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("EMAILS GÉNÉRIQUES SUPPRIMÉS:\n")
        f.write("-" * 30 + "\n")
        for email in generic_emails:
            f.write(f"• {email}\n")
        f.write("\n")
        
        f.write("RÉSULTATS FINAUX:\n")
        f.write("-" * 15 + "\n")
        f.write(f"Nombre total d'avocats: {len(df)}\n")
        f.write(f"Avocats avec emails spécifiques: {avocats_avec_emails}\n")
        f.write(f"Emails spécifiques uniques: {len(unique_specific_emails)}\n\n")
        
        f.write("EMAILS SPÉCIFIQUES TROUVÉS:\n")
        f.write("-" * 27 + "\n")
        for i, email in enumerate(unique_specific_emails, 1):
            # Trouver quel(s) avocat(s) ont cet email
            avocats_avec_cet_email = []
            for _, row in df.iterrows():
                if row['emails'] and email in row['emails']:
                    avocats_avec_cet_email.append(row['nom_complet'])
            f.write(f"{i}. {email} → {', '.join(avocats_avec_cet_email)}\n")
        f.write("\n")
        
        f.write("FICHIERS GÉNÉRÉS:\n")
        f.write("-" * 15 + "\n")
        f.write(f"• {clean_csv} - Fichier complet nettoyé\n")
        f.write(f"• {specific_csv} - Avocats avec emails spécifiques\n")
        f.write(f"• {emails_file} - Liste emails spécifiques\n")
        f.write(f"• {report_file} - Ce rapport\n")
    
    # Affichage des résultats
    print(f"\n🎉 NETTOYAGE TERMINÉ!")
    print(f"✅ Emails génériques supprimés: {len(generic_emails)}")
    print(f"✅ Avocats avec emails spécifiques: {avocats_avec_emails}")
    print(f"✅ Emails spécifiques uniques: {len(unique_specific_emails)}")
    
    print(f"\n📁 Fichiers générés:")
    print(f"   📊 Principal: {clean_csv}")
    print(f"   👥 Avec emails: {specific_csv}")
    print(f"   📧 Emails: {emails_file}")
    print(f"   📄 Rapport: {report_file}")
    
    if unique_specific_emails:
        print(f"\n📧 EMAILS SPÉCIFIQUES TROUVÉS:")
        for email in unique_specific_emails:
            print(f"   • {email}")
    else:
        print(f"\n⚠️  AUCUN EMAIL SPÉCIFIQUE (tous étaient génériques)")
    
    return clean_csv

def main():
    """Fonction principale avec gestion d'arguments"""
    parser = argparse.ArgumentParser(description='Nettoyer les emails génériques d\'un fichier CSV d\'avocats')
    parser.add_argument('csv_file', help='Fichier CSV à nettoyer')
    parser.add_argument('--threshold', '-t', type=int, default=50, 
                       help='Seuil pour considérer un email comme générique (défaut: 50)')
    
    args = parser.parse_args()
    
    result = clean_generic_emails(args.csv_file, args.threshold)
    
    if result:
        print(f"\n🎯 Fichier nettoyé: {result}")
        sys.exit(0)
    else:
        print(f"\n❌ Échec du nettoyage")
        sys.exit(1)

if __name__ == "__main__":
    main()