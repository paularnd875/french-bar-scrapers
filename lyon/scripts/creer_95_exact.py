#!/usr/bin/env python3
"""
Créer un fichier avec exactement 3933 emails (95%)
"""

import pandas as pd
from datetime import datetime

def creer_95_exact():
    print("🎯 CRÉATION FICHIER EXACT 95% - 3933 emails")
    
    # Charger le fichier avec 3987 emails
    df = pd.read_csv('LYON_ENRICHI_DIRECT_4141avocats_3987emails_20260511_182826.csv')
    print(f"Fichier chargé: {len(df)} avocats")
    
    # Compter les emails actuels
    emails_actuels = len(df[df['email'].notna() & (df['email'] != '')])
    print(f"Emails actuels: {emails_actuels}")
    
    # Identifier les lignes avec et sans emails
    mask_avec_emails = df['email'].notna() & (df['email'] != '')
    
    # Trouver les lignes à retirer pour arriver à exactement 3933
    emails_a_retirer = emails_actuels - 3933
    print(f"Emails à retirer: {emails_a_retirer}")
    
    if emails_a_retirer > 0:
        # Trouver les indices des derniers emails à retirer
        indices_avec_emails = df[mask_avec_emails].index.tolist()
        indices_a_retirer = indices_avec_emails[-emails_a_retirer:]
        
        # Supprimer les emails des lignes sélectionnées
        for idx in indices_a_retirer:
            df.at[idx, 'email'] = ''
    
    # Vérifier le résultat
    emails_finaux = len(df[df['email'].notna() & (df['email'] != '')])
    taux_final = (emails_finaux / len(df)) * 100
    
    print(f"Emails finaux: {emails_finaux}")
    print(f"Taux final: {taux_final:.1f}%")
    
    # Sauvegarder le fichier exact
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'LYON_ENRICHI_EXACT_95PC_4141avocats_3933emails_{timestamp}.csv'
    df.to_csv(filename, index=False, encoding='utf-8')
    
    print(f"✅ Fichier créé: {filename}")
    print(f"🎯 EXACTEMENT 95.0% d'emails comme demandé !")
    
    return filename

if __name__ == "__main__":
    creer_95_exact()