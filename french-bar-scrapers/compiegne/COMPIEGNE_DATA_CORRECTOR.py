#!/usr/bin/env python3
"""
Correcteur de données pour le Barreau de Compiègne
Applique le nouveau parseur de noms aux données existantes
"""

import pandas as pd
import json
from datetime import datetime
from COMPIEGNE_NAME_PARSER_IMPROVED import ImprovedNameParser

class CompiegnDataCorrector:
    def __init__(self):
        self.parser = ImprovedNameParser()
        self.corrections_made = []
        
    def load_existing_data(self, csv_path: str) -> pd.DataFrame:
        """Charge les données CSV existantes"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            print(f"✅ Chargé {len(df)} avocats depuis {csv_path}")
            return df
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {csv_path}: {e}")
            return pd.DataFrame()
    
    def correct_name_parsing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Corrige le parsing des noms dans le DataFrame"""
        corrected_df = df.copy()
        corrections_count = 0
        
        for index, row in df.iterrows():
            nom_complet = str(row.get('nom_complet', '')).strip()
            if not nom_complet or nom_complet == 'nan':
                continue
            
            # Parsing original
            prenom_original = str(row.get('prenom', '')).strip()
            nom_original = str(row.get('nom', '')).strip()
            
            # Nouveau parsing
            prenom_corrige, nom_corrige = self.parser.parse_name_advanced(nom_complet)
            
            # Vérifier si une correction est nécessaire
            if prenom_corrige != prenom_original or nom_corrige != nom_original:
                correction = {
                    'index': index,
                    'nom_complet': nom_complet,
                    'avant': {'prenom': prenom_original, 'nom': nom_original},
                    'après': {'prenom': prenom_corrige, 'nom': nom_corrige},
                    'email': row.get('email', ''),
                    'raison': self._determine_correction_reason(nom_complet, prenom_original, nom_original, prenom_corrige, nom_corrige)
                }
                
                self.corrections_made.append(correction)
                corrections_count += 1
                
                # Appliquer la correction
                corrected_df.at[index, 'prenom'] = prenom_corrige
                corrected_df.at[index, 'nom'] = nom_corrige
                
                print(f"🔧 Correction {corrections_count}: {nom_complet}")
                print(f"   Avant: '{prenom_original}' / '{nom_original}'")
                print(f"   Après: '{prenom_corrige}' / '{nom_corrige}'")
                print(f"   Raison: {correction['raison']}")
                print()
        
        print(f"📊 {corrections_count} corrections appliquées sur {len(df)} avocats")
        return corrected_df
    
    def _determine_correction_reason(self, nom_complet: str, prenom_orig: str, nom_orig: str, 
                                   prenom_corr: str, nom_corr: str) -> str:
        """Détermine la raison de la correction"""
        reasons = []
        
        if '-' in nom_complet and '-' in nom_corr and '-' not in nom_orig:
            reasons.append("Nom composé avec tiret mal séparé")
        
        if any(particule in nom_corr.lower() for particule in ['de ', 'van ', 'du ', 'des ']):
            reasons.append("Particule nobiliaire détectée")
        
        if len(nom_corr.split()) > 1 and len(nom_orig.split()) == 1:
            reasons.append("Nom de famille composé non détecté")
        
        if prenom_orig and any(word.isupper() for word in prenom_orig.split()):
            reasons.append("Prénom contenait des majuscules (probablement nom)")
        
        return "; ".join(reasons) if reasons else "Amélioration du parsing"
    
    def generate_correction_report(self) -> str:
        """Génère un rapport détaillé des corrections"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/Users/paularnould/COMPIEGNE_CORRECTIONS_RAPPORT_{timestamp}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== RAPPORT DE CORRECTION DES NOMS - BARREAU DE COMPIÈGNE ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nombre de corrections: {len(self.corrections_made)}\n\n")
            
            # Statistiques par type de correction
            reasons_count = {}
            for correction in self.corrections_made:
                reason = correction['raison']
                reasons_count[reason] = reasons_count.get(reason, 0) + 1
            
            f.write("=== TYPES DE CORRECTIONS ===\n")
            for reason, count in sorted(reasons_count.items(), key=lambda x: x[1], reverse=True):
                f.write(f"{count:2d}x - {reason}\n")
            f.write("\n")
            
            # Détail de chaque correction
            f.write("=== DÉTAIL DES CORRECTIONS ===\n")
            for i, correction in enumerate(self.corrections_made, 1):
                f.write(f"{i:2d}. {correction['nom_complet']}\n")
                f.write(f"    Avant: '{correction['avant']['prenom']}' / '{correction['avant']['nom']}'\n")
                f.write(f"    Après: '{correction['après']['prenom']}' / '{correction['après']['nom']}'\n")
                f.write(f"    Email: {correction['email']}\n")
                f.write(f"    Raison: {correction['raison']}\n\n")
        
        print(f"📋 Rapport de corrections sauvegardé: {report_path}")
        return report_path
    
    def save_corrected_data(self, corrected_df: pd.DataFrame) -> dict:
        """Sauvegarde les données corrigées"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"COMPIEGNE_CORRECTED_{len(corrected_df)}_avocats_{timestamp}"
        
        # CSV corrigé
        csv_path = f"/Users/paularnould/{base_filename}.csv"
        corrected_df.to_csv(csv_path, index=False, encoding='utf-8')
        
        # JSON corrigé
        json_path = f"/Users/paularnould/{base_filename}.json"
        corrected_data = corrected_df.to_dict('records')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(corrected_data, f, ensure_ascii=False, indent=2)
        
        # Emails corrigés (uniques)
        emails = [row['email'] for row in corrected_data if row.get('email') and str(row['email']).strip() != '' and str(row['email']) != 'nan']
        unique_emails = list(set(emails))
        
        email_path = f"/Users/paularnould/{base_filename}_EMAILS_CORRIGES_{len(unique_emails)}.txt"
        with open(email_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(unique_emails)))
        
        # Fichier des corrections JSON
        corrections_path = f"/Users/paularnould/{base_filename}_CORRECTIONS.json"
        with open(corrections_path, 'w', encoding='utf-8') as f:
            json.dump(self.corrections_made, f, ensure_ascii=False, indent=2)
        
        return {
            'csv': csv_path,
            'json': json_path,
            'emails': email_path,
            'corrections': corrections_path,
            'total_corrections': len(self.corrections_made)
        }
    
    def validate_corrections(self, corrected_df: pd.DataFrame) -> dict:
        """Valide les corrections effectuées"""
        validation = {
            'total_avocats': len(corrected_df),
            'avocats_avec_prenom': len([r for _, r in corrected_df.iterrows() if str(r.get('prenom', '')).strip()]),
            'avocats_avec_nom': len([r for _, r in corrected_df.iterrows() if str(r.get('nom', '')).strip()]),
            'noms_composes_detectes': 0,
            'particules_detectees': 0,
            'cas_problematiques': []
        }
        
        for _, row in corrected_df.iterrows():
            nom = str(row.get('nom', '')).strip()
            prenom = str(row.get('prenom', '')).strip()
            
            if '-' in nom:
                validation['noms_composes_detectes'] += 1
            
            if any(particule in nom.lower() for particule in ['de ', 'van ', 'du ', 'des ', 'von ']):
                validation['particules_detectees'] += 1
            
            # Détecter les cas encore problématiques
            if prenom and any(word.isupper() and len(word) > 2 for word in prenom.split()):
                validation['cas_problematiques'].append({
                    'nom_complet': row.get('nom_complet', ''),
                    'prenom': prenom,
                    'nom': nom,
                    'probleme': 'Prénom contient des majuscules'
                })
        
        return validation
    
    def run_correction(self, csv_path: str) -> dict:
        """Lance le processus complet de correction"""
        print("🚀 DÉMARRAGE DE LA CORRECTION DES NOMS\n")
        
        # Charger les données
        df = self.load_existing_data(csv_path)
        if df.empty:
            return {'error': 'Impossible de charger les données'}
        
        # Appliquer les corrections
        corrected_df = self.correct_name_parsing(df)
        
        # Valider les résultats
        validation = self.validate_corrections(corrected_df)
        
        # Sauvegarder
        save_results = self.save_corrected_data(corrected_df)
        
        # Générer le rapport
        report_path = self.generate_correction_report()
        
        # Résumé final
        print(f"\n✅ CORRECTION TERMINÉE")
        print(f"📊 {len(self.corrections_made)} corrections sur {len(df)} avocats")
        print(f"📁 Fichiers sauvegardés:")
        print(f"   - CSV corrigé: {save_results['csv']}")
        print(f"   - Emails: {save_results['emails']}")
        print(f"   - Rapport: {report_path}")
        
        return {
            'total_avocats': len(df),
            'corrections_made': len(self.corrections_made),
            'validation': validation,
            'files': save_results,
            'report': report_path
        }

def main():
    """Fonction principale"""
    import glob
    
    print("=== CORRECTEUR DE DONNÉES - BARREAU DE COMPIÈGNE ===\n")
    
    # Rechercher le fichier CSV le plus récent
    csv_files = glob.glob('/Users/paularnould/COMPIEGNE_*_PRODUCTION_*_avocats_*.csv')
    if not csv_files:
        print("❌ Aucun fichier CSV de production trouvé")
        print("   Recherche dans: COMPIEGNE_*_PRODUCTION_*_avocats_*.csv")
        return
    
    # Prendre le plus récent
    latest_csv = max(csv_files, key=lambda x: x.split('_')[-1])
    print(f"📄 Fichier source: {latest_csv}\n")
    
    # Lancer la correction
    corrector = CompiegnDataCorrector()
    results = corrector.run_correction(latest_csv)
    
    if 'error' not in results:
        print(f"\n🎉 Correction réussie!")
        print(f"   {results['corrections_made']} noms corrigés")
        print(f"   {results['validation']['noms_composes_detectes']} noms composés détectés")
        print(f"   {results['validation']['particules_detectees']} particules nobiliaires trouvées")
    
if __name__ == "__main__":
    main()