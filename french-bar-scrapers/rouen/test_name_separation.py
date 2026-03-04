#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TEST DE CORRECTION DES NOMS COMPOSÉS - BARREAU DE ROUEN
=======================================================

Test rapide pour valider la nouvelle logique de séparation prenom/nom
avec les cas problématiques détectés sur le site du Barreau de Rouen.
"""

import sys
import re
import unicodedata
sys.path.append('.')

class TestNomCorrection:
    def clean_text(self, text):
        """Nettoyer le texte (version simplifiée)"""
        if not text:
            return ""
        
        # Normaliser Unicode 
        text = unicodedata.normalize('NFD', text)
        
        # Nettoyer caractères spéciaux mais garder lettres accentuées
        text = re.sub(r'[^\w\s\-\.@àâäéèêëïîôöùûüÿñç]', '', text, flags=re.UNICODE)
        
        return text.strip()

    def separate_first_last_name(self, full_name):
        """Séparer prénom et nom avec logique améliorée pour noms composés français"""
        if not full_name:
            return "", ""
        
        # Nettoyer
        full_name = self.clean_text(full_name)
        
        # Supprimer titres
        titles = ["Me", "Maître", "Dr", "Pr", "M.", "Mme", "Mlle"]
        for title in titles:
            if full_name.startswith(title + " "):
                full_name = full_name.replace(title + " ", "", 1).strip()
        
        # Supprimer suffixes
        suffixes = ["(Avocat)", "(Avocate)", "Avocat", "Avocate"]
        for suffix in suffixes:
            full_name = full_name.replace(suffix, "").strip()
        
        parts = full_name.split()
        
        if len(parts) == 1:
            return "", parts[0]
        elif len(parts) == 2:
            # Format : "NOM Prénom" ou "Prénom NOM"
            # Logique basée sur les majuscules/minuscules
            if parts[0].isupper() and not parts[1].isupper():
                # "ABDOU Sophia" -> prénom=Sophia, nom=ABDOU
                return parts[1], parts[0]
            elif not parts[0].isupper() and parts[1].isupper():
                # "Sophia ABDOU" -> prénom=Sophia, nom=ABDOU  
                return parts[0], parts[1]
            else:
                # Si les deux sont en majuscules ou les deux en minuscules
                # On suppose format "NOM Prénom" par défaut sur ce site
                return parts[1], parts[0]
        else:
            # Noms composés : analyser la structure
            # Cas 1: "CHAILLÉ DE NÉRÉ Dixie" -> prénom=Dixie, nom=CHAILLÉ DE NÉRÉ
            # Cas 2: "ALVES DA COSTA David" -> prénom=David, nom=ALVES DA COSTA
            
            # Le prénom est généralement le dernier mot s'il n'est pas en majuscules
            last_word = parts[-1]
            if not last_word.isupper() and len(parts) > 2:
                # Les mots précédents forment le nom de famille
                prenom = last_word
                nom = " ".join(parts[:-1])
                return prenom, nom
            
            # Cas avec particules au début du nom : "DE LA BRUNIÈRE Arnaud"
            elif len(parts) > 2 and parts[0].upper() in ['DE', 'DU', 'DES', 'LE', 'LA', 'VAN', 'VON', "D'"]:
                # Tout sauf le dernier mot = nom, dernier mot = prénom
                if not parts[-1].isupper():
                    return parts[-1], " ".join(parts[:-1])
                # Sinon logique par défaut
                return parts[0], " ".join(parts[1:])
            
            # Cas avec tiret dans prénom : "Marie-Claire DUPONT"
            elif "-" in parts[0]:
                return " ".join(parts[:-1]), parts[-1]
            
            # Par défaut : si le dernier mot n'est pas en majuscules, c'est le prénom
            elif not parts[-1].isupper():
                return parts[-1], " ".join(parts[:-1])
            else:
                # Logique par défaut : premier mot = prénom, reste = nom
                return parts[0], " ".join(parts[1:])

def test_noms():
    """Tester les cas problématiques du Barreau de Rouen"""
    tester = TestNomCorrection()
    
    # Cas de test avec résultats attendus (basés sur le site Rouen)
    test_cases = [
        # (nom_complet, prenom_attendu, nom_attendu)
        ("ALVES DA COSTA David", "David", "ALVES DA COSTA"),
        ("CHAILLÉ DE NÉRÉ Dixie", "Dixie", "CHAILLÉ DE NÉRÉ"),
        ("DE LA BRUNIÈRE Arnaud", "Arnaud", "DE LA BRUNIÈRE"),
        ("ALQUIER Claudie", "Claudie", "ALQUIER"),
        ("M. ABSIRE Marc", "Marc", "ABSIRE"),
        ("ALBERT Patrick", "Patrick", "ALBERT"),
        ("Marie-Claire DUPONT", "Marie-Claire", "DUPONT"),
        ("HOUSARD DE LA POTTERIE Bénédicte", "Bénédicte", "HOUSARD DE LA POTTERIE"),
        # Cas problématiques détectés sur Rouen
        ("ABDOU Sophia", "Sophia", "ABDOU"),
        ("ALEXANDRE Gaëlle", "Gaëlle", "ALEXANDRE"),
        ("ALLO Mylène", "Mylène", "ALLO"),
        ("ANO-DUVILLA Sidonie", "Sidonie", "ANO-DUVILLA"),
        ("AUDRA-MOISSON Stéphanie", "Stéphanie", "AUDRA-MOISSON"),
    ]
    
    print("🧪 TEST DE CORRECTION DES NOMS COMPOSÉS - BARREAU DE ROUEN")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for nom_complet, prenom_attendu, nom_attendu in test_cases:
        prenom, nom = tester.separate_first_last_name(nom_complet)
        
        success = (prenom == prenom_attendu and nom == nom_attendu)
        
        if success:
            print(f"✅ '{nom_complet}' -> prenom='{prenom}', nom='{nom}'")
            passed += 1
        else:
            print(f"❌ '{nom_complet}':")
            print(f"   Obtenu   : prenom='{prenom}', nom='{nom}'")
            print(f"   Attendu  : prenom='{prenom_attendu}', nom='{nom_attendu}'")
            failed += 1
    
    print("=" * 70)
    print(f"📊 RÉSULTATS: {passed} réussis, {failed} échecs")
    
    if failed == 0:
        print("🎉 Tous les tests sont RÉUSSIS! La logique est corrigée.")
        print("✅ Prêt pour l'extraction complète du Barreau de Rouen")
        return True
    else:
        print("⚠️  Des améliorations sont encore nécessaires.")
        return False

def main():
    """Test principal"""
    success = test_noms()
    
    if success:
        print(f"\n🚀 Pour lancer l'extraction complète:")
        print(f"   python3 run_extraction.py")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())