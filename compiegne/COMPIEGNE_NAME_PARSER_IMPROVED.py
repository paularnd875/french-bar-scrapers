#!/usr/bin/env python3
"""
Parseur de noms amélioré pour le Barreau de Compiègne
Gestion correcte des noms composés, particules nobiliaires et prénoms composés
"""

import re
import json
from typing import Tuple, List, Dict

class ImprovedNameParser:
    def __init__(self):
        # Particules nobiliaires françaises et internationales
        self.particules = {
            'françaises': ['de', 'du', 'des', 'de la', 'de le', 'du', 'des', 'd\'', 'de l\''],
            'internationales': ['van', 'von', 'della', 'del', 'da', 'di', 'le', 'la', 'los', 'las', 'mac', 'mc', 'o\'']
        }
        
        # Tous les patterns de particules
        self.all_particules = []
        for category in self.particules.values():
            self.all_particules.extend(category)
        
        # Prénoms composés français courants
        self.prenoms_composes = [
            'jean-pierre', 'marie-claire', 'anne-laure', 'jean-claude', 'marie-france',
            'jean-michel', 'marie-thérèse', 'jean-françois', 'marie-christine', 'pierre-yves',
            'jean-luc', 'marie-hélène', 'jean-paul', 'anne-marie', 'marie-josé',
            'jean-louis', 'marie-rose', 'charles-henri', 'marie-noëlle', 'jean-baptiste'
        ]
        
        # Cas de test connus
        self.test_cases = [
            # Format: (input, expected_prenom, expected_nom)
            ('CARON - DE WILDE Stéphanie', 'Stéphanie', 'CARON - DE WILDE'),
            ('DANNE - THIEFINE Florence', 'Florence', 'DANNE - THIEFINE'),
            ('GUEVENOUX - GLORIAN Christophe', 'Christophe', 'GUEVENOUX - GLORIAN'),
            ('NOEL - PETRI Séverine', 'Séverine', 'NOEL - PETRI'),
            ('LEONARD - LE PIVERT Elisabeth', 'Elisabeth', 'LEONARD - LE PIVERT'),
            ('THOMA - BRUNIERE Sabine', 'Sabine', 'THOMA - BRUNIERE'),
            ('de SAINT ANDRIEU Isabelle', 'Isabelle', 'de SAINT ANDRIEU'),
            ('VAN ZEVENTER Robert', 'Robert', 'VAN ZEVENTER'),
            ('ZEITER DURAND Océane', 'Océane', 'ZEITER DURAND'),
            ('DE LANGLADE Guillaume', 'Guillaume', 'DE LANGLADE'),
            ('ALEXANDRE Anthony', 'Anthony', 'ALEXANDRE'),
            ('ANGOTTI Frédérique', 'Frédérique', 'ANGOTTI'),
        ]

    def clean_name(self, full_name: str) -> str:
        """Nettoie le nom en supprimant les titres"""
        if not full_name:
            return ""
        
        # Supprimer les titres
        name = re.sub(r'^(Maître|Me\.?|M\.?|Mme\.?)\s+', '', full_name.strip(), flags=re.IGNORECASE)
        # Nettoyer les espaces multiples
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name

    def has_particule(self, word: str) -> bool:
        """Vérifie si un mot est une particule nobiliaire"""
        word_lower = word.lower()
        return any(word_lower == particule.lower() or word_lower == particule.lower().rstrip("'") 
                  for particule in self.all_particules)

    def is_compound_surname(self, text: str) -> bool:
        """Détecte si le texte contient un nom de famille composé"""
        # Pattern 1: Mots en majuscules avec tiret (CARON - DE WILDE)
        if re.search(r'[A-Z]{2,}\s*-\s*[A-Z]{2,}', text):
            return True
        
        # Pattern 2: Particule suivie de nom en majuscules (de SAINT ANDRIEU)
        words = text.split()
        for i, word in enumerate(words):
            if self.has_particule(word) and i + 1 < len(words):
                next_word = words[i + 1]
                if next_word.isupper() and len(next_word) > 1:
                    return True
        
        # Pattern 3: Nom composé sans tiret mais deux mots majuscules consécutifs
        if re.search(r'[A-Z]{2,}\s+[A-Z]{2,}', text):
            return True
        
        return False

    def find_surname_boundary(self, words: List[str]) -> int:
        """Trouve la frontière entre prénom et nom de famille"""
        if not words:
            return 0
        
        # Reconstruction pour détecter les noms composés avec tirets
        full_text = ' '.join(words)
        
        # Cas 1: Pattern spécial pour noms composés type "CARON - DE WILDE Stéphanie"
        # Rechercher pattern: MAJUSCULES - MAJUSCULES prénom_mixte
        compound_pattern = re.search(r'^([A-Z]+\s*-\s*[A-Z\s]+?)\s+([A-Za-zÀ-ÿ][a-zà-ÿ]+(?:\s+[A-Za-zÀ-ÿ][a-zà-ÿ]+)*)$', full_text)
        if compound_pattern:
            compound_surname = compound_pattern.group(1).strip()
            # Compter les mots du nom composé pour trouver la frontière
            surname_words = len(compound_surname.split())
            return surname_words
        
        # Cas 2: Rechercher une particule
        for i, word in enumerate(words):
            if self.has_particule(word):
                return i
        
        # Cas 3: Rechercher deux mots consécutifs en majuscules (sans tiret au milieu)
        for i in range(len(words) - 1):
            if (words[i].isupper() and len(words[i]) > 1 and 
                words[i+1].isupper() and len(words[i+1]) > 1 and
                '-' not in words[i]):
                return i
        
        # Cas 4: Le dernier mot en majuscules est probablement le nom (cas simple)
        for i in range(len(words) - 1, -1, -1):
            if words[i].isupper() and len(words[i]) > 1:
                return i
        
        # Par défaut, le dernier mot
        return len(words) - 1

    def parse_name_advanced(self, full_name: str) -> Tuple[str, str]:
        """Parse un nom avec gestion avancée des cas complexes"""
        try:
            clean_name = self.clean_name(full_name)
            if not clean_name:
                return "", ""
            
            words = clean_name.split()
            if not words:
                return "", clean_name
            
            if len(words) == 1:
                return "", words[0]
            
            # APPROCHE NOUVELLE: Détecter d'abord les patterns spécifiques
            full_text = clean_name
            
            # Pattern 1: Nom composé avec tiret + prénom à la fin
            # Ex: "CARON - DE WILDE Stéphanie" -> nom="CARON - DE WILDE", prénom="Stéphanie"
            compound_match = re.match(r'^([A-Z][A-Z\s-]+?)\s+([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)*)$', full_text)
            if compound_match:
                potential_nom = compound_match.group(1).strip()
                potential_prenom = compound_match.group(2).strip()
                
                # Vérifier que le nom contient bien des caractères en majuscules majoritaires
                if len(re.findall(r'[A-Z]', potential_nom)) >= len(re.findall(r'[a-z]', potential_nom)):
                    return potential_prenom, potential_nom
            
            # Pattern 2: Particule + nom + prénom
            # Ex: "de SAINT ANDRIEU Isabelle"
            particule_match = re.match(r'^((?:de|du|des|van|von|della|del)\s+[A-Z\s]+?)\s+([A-Z][a-zà-ÿ]+)$', full_text, re.IGNORECASE)
            if particule_match:
                nom = particule_match.group(1).strip()
                prenom = particule_match.group(2).strip()
                return prenom, nom
            
            # Pattern 3: Deux noms majuscules + prénom
            # Ex: "ZEITER DURAND Océane"
            double_surname_match = re.match(r'^([A-Z]{2,}\s+[A-Z]{2,})\s+([A-Z][a-zà-ÿ]+)$', full_text)
            if double_surname_match:
                nom = double_surname_match.group(1).strip()
                prenom = double_surname_match.group(2).strip()
                return prenom, nom
            
            # Pattern 4: Cas standard - nom simple + prénom
            # Ex: "ALEXANDRE Anthony"
            simple_match = re.match(r'^([A-Z]{2,})\s+([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)*)$', full_text)
            if simple_match:
                nom = simple_match.group(1).strip()
                prenom = simple_match.group(2).strip()
                return prenom, nom
            
            # Fallback: utiliser l'ancienne méthode
            surname_start = self.find_surname_boundary(words)
            
            if surname_start == 0:
                if len(words) > 1:
                    prenom = words[-1]
                    nom = ' '.join(words[:-1])
                else:
                    prenom = ""
                    nom = words[0]
            else:
                prenom = ' '.join(words[:surname_start]) if surname_start > 0 else ""
                nom = ' '.join(words[surname_start:])
            
            return prenom.strip(), nom.strip()
            
        except Exception as e:
            print(f"⚠️ Erreur lors du parsing de '{full_name}': {e}")
            return "", full_name

    def validate_parsing(self, full_name: str, prenom: str, nom: str) -> Dict:
        """Valide le parsing et retourne un score de confiance"""
        validation = {
            'confiance': 100,
            'warnings': [],
            'suggestions': []
        }
        
        # Vérification 1: Le prénom ne devrait pas contenir de tirets entre mots majuscules
        if '-' in prenom and re.search(r'[A-Z]{2,}.*-.*[A-Z]{2,}', prenom):
            validation['confiance'] -= 50
            validation['warnings'].append("Prénom contient un pattern de nom composé")
        
        # Vérification 2: Le nom devrait contenir les mots les plus longs en majuscules
        words = full_name.split()
        longest_upper_words = [w for w in words if w.isupper() and len(w) > 2]
        
        if longest_upper_words:
            if not any(w in nom for w in longest_upper_words):
                validation['confiance'] -= 30
                validation['warnings'].append("Mots majuscules principaux pas dans le nom")
        
        # Vérification 3: Cohérence avec les patterns connus
        if any(particule in nom.lower() for particule in self.all_particules):
            validation['confiance'] += 10
            validation['suggestions'].append("Particule détectée correctement")
        
        return validation

    def run_test_cases(self) -> Dict:
        """Exécute tous les cas de test"""
        results = {
            'total': len(self.test_cases),
            'correct': 0,
            'incorrect': 0,
            'details': []
        }
        
        for input_name, expected_prenom, expected_nom in self.test_cases:
            prenom, nom = self.parse_name_advanced(input_name)
            
            is_correct = (prenom == expected_prenom and nom == expected_nom)
            
            if is_correct:
                results['correct'] += 1
            else:
                results['incorrect'] += 1
            
            validation = self.validate_parsing(input_name, prenom, nom)
            
            results['details'].append({
                'input': input_name,
                'expected': {'prenom': expected_prenom, 'nom': expected_nom},
                'actual': {'prenom': prenom, 'nom': nom},
                'correct': is_correct,
                'confidence': validation['confiance'],
                'warnings': validation['warnings']
            })
        
        results['accuracy'] = (results['correct'] / results['total']) * 100
        return results

def main():
    """Test du nouveau parseur"""
    print("=== TEST DU PARSEUR DE NOMS AMÉLIORÉ ===\n")
    
    parser = ImprovedNameParser()
    results = parser.run_test_cases()
    
    print(f"📊 RÉSULTATS DES TESTS:")
    print(f"   Total: {results['total']}")
    print(f"   Correct: {results['correct']}")
    print(f"   Incorrect: {results['incorrect']}")
    print(f"   Précision: {results['accuracy']:.1f}%\n")
    
    print("📋 DÉTAIL DES TESTS:")
    for detail in results['details']:
        status = "✅" if detail['correct'] else "❌"
        print(f"{status} {detail['input']}")
        print(f"   Attendu: '{detail['expected']['prenom']}' / '{detail['expected']['nom']}'")
        print(f"   Obtenu:  '{detail['actual']['prenom']}' / '{detail['actual']['nom']}'")
        print(f"   Confiance: {detail['confidence']}%")
        
        if detail['warnings']:
            print(f"   ⚠️  {', '.join(detail['warnings'])}")
        print()
    
    # Sauvegarder les résultats
    with open('/Users/paularnould/test_results_parsing.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Résultats sauvegardés dans test_results_parsing.json")

if __name__ == "__main__":
    main()