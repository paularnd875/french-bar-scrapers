#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de fusion final pour le Barreau de Bordeaux
Croise les données principales avec les spécialisations
"""

import json
import csv
import pandas as pd
from datetime import datetime
from collections import defaultdict

class BordeauxFusionFinal:
    def __init__(self):
        self.main_file = 'bordeaux_CORRIGÉ_COMPLET_20260210_165557.csv'
        self.specialisations_file = 'bordeaux_specialisations_relations_20260210_170101.csv'
        
    def normalize_name(self, name):
        """Normalise un nom pour la comparaison"""
        # Enlever les espaces multiples, convertir en majuscules
        normalized = ' '.join(name.strip().upper().split())
        # Enlever les caractères spéciaux communs
        normalized = normalized.replace('-', ' ').replace('\'', ' ').replace('.', ' ')
        return normalized
    
    def extract_name_parts_from_concat(self, concat_name):
        """Extrait nom et prénom d'un nom concaténé comme 'DURANDPierre' """
        # Chercher où finit le nom (généralement avant une majuscule)
        import re
        
        # Pattern : majuscules suivies d'au moins une majuscule + minuscule (= début prénom)
        match = re.match(r'^([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ-]+)([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ][a-zàâäéèêëïîôöùûüç-]+.*)$', concat_name)
        
        if match:
            nom_part = match.group(1)
            prenom_part = match.group(2)
            return nom_part.strip(), prenom_part.strip()
        
        return None, None
    
    def load_main_data(self):
        """Charge les données principales"""
        print("Chargement des données principales...")
        
        main_data = []
        with open(self.main_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                main_data.append(row)
        
        print(f"  ✅ {len(main_data)} avocats chargés")
        return main_data
    
    def load_specialisations_data(self):
        """Charge les données de spécialisations"""
        print("Chargement des spécialisations...")
        
        # Grouper par avocat
        specialisations_by_lawyer = defaultdict(list)
        
        with open(self.specialisations_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nom_complet_concat = row['nom_complet']
                specialisation = row['specialisation']
                
                # Extraire nom et prénom du format concaténé
                nom, prenom = self.extract_name_parts_from_concat(nom_complet_concat)
                
                if nom and prenom:
                    # Créer plusieurs variantes normalisées pour la recherche
                    variants = [
                        self.normalize_name(f"{prenom} {nom}"),  # Pierre DURAND
                        self.normalize_name(f"{nom} {prenom}"),  # DURAND Pierre  
                        self.normalize_name(nom_complet_concat), # DURANDPierre
                    ]
                    
                    for variant in variants:
                        specialisations_by_lawyer[variant].append(specialisation)
        
        print(f"  ✅ {len(specialisations_by_lawyer)} variantes de noms avec spécialisations")
        return specialisations_by_lawyer
    
    def find_matching_lawyer(self, main_lawyer, specialisations_data):
        """Trouve les spécialisations d'un avocat"""
        # Essayer plusieurs variantes du nom
        nom_complet = main_lawyer['nom_complet']
        
        search_variants = [
            self.normalize_name(nom_complet),
            self.normalize_name(f"{main_lawyer['prenom']} {main_lawyer['nom']}"),
            self.normalize_name(f"{main_lawyer['nom']} {main_lawyer['prenom']}"),
        ]
        
        for variant in search_variants:
            if variant in specialisations_data:
                return specialisations_data[variant]
        
        return []
    
    def merge_data(self):
        """Fusionne les données principales avec les spécialisations"""
        print("\n=== FUSION DES DONNÉES ===")
        
        # Charger les données
        main_data = self.load_main_data()
        specialisations_data = self.load_specialisations_data()
        
        print("\nCroisement des données...")
        
        # Statistiques
        matches_found = 0
        total_specialisations_added = 0
        
        # Fusionner
        for lawyer in main_data:
            specialisations = self.find_matching_lawyer(lawyer, specialisations_data)
            
            if specialisations:
                matches_found += 1
                total_specialisations_added += len(specialisations)
                lawyer['specialisations'] = ' | '.join(specialisations)
            else:
                lawyer['specialisations'] = ''
        
        print(f"  ✅ {matches_found} avocats avec spécialisations trouvées")
        print(f"  ✅ {total_specialisations_added} spécialisations ajoutées au total")
        
        return main_data, matches_found, total_specialisations_added
    
    def save_final_data(self, merged_data, matches_found, total_specialisations):
        """Sauvegarde les données finales"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV final
        csv_filename = f'bordeaux_FINAL_COMPLET_{timestamp}.csv'
        with open(csv_filename, 'w', encoding='utf-8', newline='') as f:
            if merged_data:
                fieldnames = list(merged_data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(merged_data)
        
        # JSON final
        json_filename = f'bordeaux_FINAL_COMPLET_{timestamp}.json'
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'source': 'Barreau de Bordeaux - Données complètes avec spécialisations',
                'total_avocats': len(merged_data),
                'avocats_avec_specialisations': matches_found,
                'total_specialisations': total_specialisations,
                'taux_specialisations': f"{matches_found/len(merged_data)*100:.1f}%" if merged_data else "0%",
                'avocats': merged_data
            }, f, indent=2, ensure_ascii=False)
        
        # Emails finaux uniquement
        emails_filename = f'bordeaux_FINAL_EMAILS_{timestamp}.txt'
        emails = [lawyer['email'] for lawyer in merged_data if lawyer.get('email')]
        unique_emails = sorted(set(emails))
        
        with open(emails_filename, 'w', encoding='utf-8') as f:
            for i, email in enumerate(unique_emails, 1):
                f.write(f"{i:>6}→{email}\n")
        
        # Rapport final
        rapport_filename = f'bordeaux_FINAL_RAPPORT_{timestamp}.txt'
        with open(rapport_filename, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("RAPPORT FINAL COMPLET - BARREAU DE BORDEAUX\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Date et heure: {timestamp}\n")
            f.write("Source: Barreau de Bordeaux (https://www.barreau-bordeaux.com)\n")
            f.write("Méthode: Extraction individuelle + Recherche par spécialisation\n\n")
            
            f.write("RÉSULTATS GLOBAUX:\n")
            f.write("-"*40 + "\n")
            f.write(f"Total d'avocats: {len(merged_data)}\n")
            f.write(f"Avocats avec email: {len([l for l in merged_data if l.get('email')])}\n")
            f.write(f"Avocats avec téléphone: {len([l for l in merged_data if l.get('telephone')])}\n")
            f.write(f"Avocats avec cabinet: {len([l for l in merged_data if l.get('cabinet')])}\n")
            f.write(f"Avocats avec spécialisations: {matches_found}\n")
            f.write(f"Emails uniques: {len(unique_emails)}\n\n")
            
            f.write("TAUX DE COMPLÉTUDE:\n")
            f.write("-"*40 + "\n")
            total = len(merged_data)
            f.write(f"Emails: {len([l for l in merged_data if l.get('email')])/total*100:.1f}%\n")
            f.write(f"Téléphones: {len([l for l in merged_data if l.get('telephone')])/total*100:.1f}%\n") 
            f.write(f"Cabinets: {len([l for l in merged_data if l.get('cabinet')])/total*100:.1f}%\n")
            f.write(f"Spécialisations: {matches_found/total*100:.1f}%\n\n")
            
            f.write("SPÉCIALISATIONS LES PLUS REPRÉSENTÉES:\n")
            f.write("-"*40 + "\n")
            
            # Compter les spécialisations
            spec_count = defaultdict(int)
            for lawyer in merged_data:
                if lawyer.get('specialisations'):
                    specs = lawyer['specialisations'].split(' | ')
                    for spec in specs:
                        spec_count[spec] += 1
            
            # Top 10
            top_specs = sorted(spec_count.items(), key=lambda x: x[1], reverse=True)[:10]
            for spec, count in top_specs:
                f.write(f"- {spec}: {count} avocats\n")
            
            f.write(f"\n" + "="*70 + "\n")
            f.write("FICHIERS GÉNÉRÉS:\n")
            f.write(f"- {csv_filename} (données complètes CSV)\n")
            f.write(f"- {json_filename} (données complètes JSON)\n")
            f.write(f"- {emails_filename} (emails uniques)\n")
            f.write(f"- {rapport_filename} (ce rapport)\n")
            f.write("="*70 + "\n")
        
        return {
            'csv': csv_filename,
            'json': json_filename, 
            'emails': emails_filename,
            'rapport': rapport_filename
        }
    
    def run(self):
        """Lance la fusion complète"""
        print("="*70)
        print("FUSION FINALE - BARREAU DE BORDEAUX")
        print("Données principales + Spécialisations")
        print("="*70)
        
        try:
            # Fusion
            merged_data, matches_found, total_specialisations = self.merge_data()
            
            # Sauvegarde
            print("\nSauvegarde des données finales...")
            files_created = self.save_final_data(merged_data, matches_found, total_specialisations)
            
            # Résumé final
            print(f"\n" + "="*70)
            print("FUSION TERMINÉE AVEC SUCCÈS")
            print("="*70)
            print(f"Total avocats: {len(merged_data)}")
            print(f"Avec spécialisations: {matches_found} ({matches_found/len(merged_data)*100:.1f}%)")
            print(f"Total spécialisations: {total_specialisations}")
            print(f"Emails uniques: {len(set([l['email'] for l in merged_data if l.get('email')]))}")
            
            print(f"\nFichiers créés:")
            for file_type, filename in files_created.items():
                print(f"  - {filename}")
            
            print("="*70)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la fusion: {e}")
            return False

if __name__ == "__main__":
    fusion = BordeauxFusionFinal()
    fusion.run()