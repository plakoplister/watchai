#!/usr/bin/env python3
"""
Contrôle qualité avant intégration des données
Vérifie que toutes les entités sont correctement mappées
"""

import pandas as pd
from pathlib import Path
import re

# Chemins
BASE_DIR = Path("/Users/julienmarboeuf/Documents/MEREYA/AGL/EXPORT-Db")
UPDATES_DIR = BASE_DIR / "Updates_Mensuels"
MASTER_DATA = BASE_DIR / "Master_Data"

def normalize_for_exact_match(full_name):
    """Normalise un nom pour correspondance exacte"""
    if pd.isna(full_name):
        return ""
    
    name = str(full_name).upper().strip()
    name = re.sub(r'[\n\r]+', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    
    return name

def load_mappings():
    """Charge tous les mappings existants"""
    mappings_file = MASTER_DATA / "Entity_Mappings.xlsx"
    
    try:
        exp_df = pd.read_excel(mappings_file, sheet_name='Exportateurs')
        dest_df = pd.read_excel(mappings_file, sheet_name='Destinataires')
        
        # Index normalisé pour recherche rapide
        exp_normalized = {}
        dest_normalized = {}
        
        for _, row in exp_df.iterrows():
            if pd.notna(row['EXPORTATEUR']) and pd.notna(row['EXPORTATEUR SIMPLE']):
                key = normalize_for_exact_match(row['EXPORTATEUR'])
                exp_normalized[key] = row['EXPORTATEUR SIMPLE']
        
        for _, row in dest_df.iterrows():
            if pd.notna(row['DESTINATAIRE']) and pd.notna(row['DESTINATAIRE SIMPLE']):
                key = normalize_for_exact_match(row['DESTINATAIRE'])
                dest_normalized[key] = row['DESTINATAIRE SIMPLE']
        
        return exp_normalized, dest_normalized
        
    except Exception as e:
        print(f"❌ Erreur chargement mappings: {e}")
        return {}, {}

def check_data_quality(year="2023", max_length=50):
    """
    Vérifie la qualité des données avant intégration
    
    Args:
        year: Année à vérifier
        max_length: Longueur max acceptable pour les noms simples
    """
    
    print(f"🔍 CONTRÔLE QUALITÉ - DONNÉES {year}")
    print("=" * 60)
    
    # Charger les mappings
    print("📋 Chargement des mappings...")
    exp_mappings, dest_mappings = load_mappings()
    print(f"✅ Mappings chargés: {len(exp_mappings)} exportateurs, {len(dest_mappings)} destinataires")
    
    # Lister les fichiers
    files = list(UPDATES_DIR.glob(f"{year}/*.xlsx"))
    files = [f for f in files if not f.name.startswith('~$')]
    
    if not files:
        print(f"❌ Aucun fichier trouvé pour l'année {year}")
        return False
    
    print(f"📁 Fichiers à vérifier: {len(files)}")
    
    # Statistiques de contrôle
    issues = {
        'exportateurs_non_mappes': [],
        'destinataires_non_mappes': [],
        'exportateurs_longs': [],
        'destinataires_longs': [],
        'dates_invalides': [],
        'destinations_inconnues': []
    }
    
    total_lines = 0
    
    for file in files:
        print(f"\n📄 Vérification {file.name}:")
        
        try:
            df = pd.read_excel(file)
            total_lines += len(df)
            print(f"  📊 {len(df)} lignes")
            
            # 1. Vérifier les dates
            if 'DECLARATION_DATE' in df.columns:
                invalid_dates = df[df['DECLARATION_DATE'].isna()]
                if len(invalid_dates) > 0:
                    issues['dates_invalides'].append(f"{file.name}: {len(invalid_dates)} dates vides")
            
            # 2. Vérifier les exportateurs
            if 'NOM_EXPORTATEUR' in df.columns:
                exportateurs = df['NOM_EXPORTATEUR'].dropna().unique()
                
                for exp in exportateurs:
                    exp_normalized = normalize_for_exact_match(exp)
                    
                    if exp_normalized not in exp_mappings:
                        issues['exportateurs_non_mappes'].append(f"{file.name}: {str(exp)[:60]}...")
                    else:
                        simple_name = exp_mappings[exp_normalized]
                        if len(simple_name) > max_length:
                            issues['exportateurs_longs'].append(f"{simple_name} ({len(simple_name)} chars)")
            
            # 3. Vérifier les destinataires
            if 'NOM_IMPORTATEUR' in df.columns:
                destinataires = df['NOM_IMPORTATEUR'].dropna().unique()
                
                for dest in destinataires:
                    dest_normalized = normalize_for_exact_match(dest)
                    
                    if dest_normalized not in dest_mappings:
                        issues['destinataires_non_mappes'].append(f"{file.name}: {str(dest)[:60]}...")
                    else:
                        simple_name = dest_mappings[dest_normalized]
                        if len(simple_name) > max_length:
                            issues['destinataires_longs'].append(f"{simple_name} ({len(simple_name)} chars)")
            
            # 4. Vérifier les destinations (pays)
            if 'PAYS_DESTINATION' in df.columns:
                destinations = df['PAYS_DESTINATION'].dropna().unique()
                
                known_countries = {
                    'PAYS-BAS', 'ALLEMAGNE', 'BELGIQUE', 'FRANCE', 'ESPAGNE', 'ITALIE',
                    'ROYAUME-UNI', 'ETATS-UNIS', 'RUSSIE', 'MALAISIE', 'SINGAPOUR',
                    'INDONESIE', 'TURQUIE', 'UKRAINE', 'ESTONIE', 'LITUANIE', 
                    'LETTONIE', 'POLOGNE', 'AUTRE'
                }
                
                for dest in destinations:
                    if str(dest).strip().upper() not in known_countries:
                        issues['destinations_inconnues'].append(f"{file.name}: {dest}")
            
        except Exception as e:
            print(f"  ❌ Erreur lecture {file.name}: {e}")
    
    # Afficher le rapport
    print(f"\n📊 RAPPORT DE CONTRÔLE QUALITÉ")
    print("=" * 40)
    print(f"Total lignes analysées: {total_lines:,}")
    
    all_good = True
    
    # Exportateurs non mappés
    if issues['exportateurs_non_mappes']:
        print(f"\n❌ EXPORTATEURS NON MAPPÉS ({len(issues['exportateurs_non_mappes'])}):")
        for i, issue in enumerate(issues['exportateurs_non_mappes'][:5]):  # Afficher les 5 premiers
            print(f"  {i+1}. {issue}")
        if len(issues['exportateurs_non_mappes']) > 5:
            print(f"  ... et {len(issues['exportateurs_non_mappes']) - 5} autres")
        all_good = False
    
    # Destinataires non mappés
    if issues['destinataires_non_mappes']:
        print(f"\n❌ DESTINATAIRES NON MAPPÉS ({len(issues['destinataires_non_mappes'])}):")
        for i, issue in enumerate(issues['destinataires_non_mappes'][:5]):
            print(f"  {i+1}. {issue}")
        if len(issues['destinataires_non_mappes']) > 5:
            print(f"  ... et {len(issues['destinataires_non_mappes']) - 5} autres")
        all_good = False
    
    # Noms simples trop longs
    if issues['exportateurs_longs']:
        print(f"\n⚠️ EXPORTATEURS SIMPLES TROP LONGS ({len(issues['exportateurs_longs'])}):")
        for i, issue in enumerate(issues['exportateurs_longs'][:3]):
            print(f"  {i+1}. {issue}")
        all_good = False
    
    if issues['destinataires_longs']:
        print(f"\n⚠️ DESTINATAIRES SIMPLES TROP LONGS ({len(issues['destinataires_longs'])}):")
        for i, issue in enumerate(issues['destinataires_longs'][:3]):
            print(f"  {i+1}. {issue}")
        all_good = False
    
    # Destinations inconnues
    if issues['destinations_inconnues']:
        print(f"\n⚠️ DESTINATIONS INCONNUES ({len(issues['destinations_inconnues'])}):")
        for i, issue in enumerate(issues['destinations_inconnues'][:3]):
            print(f"  {i+1}. {issue}")
        all_good = False
    
    # Dates invalides
    if issues['dates_invalides']:
        print(f"\n⚠️ DATES INVALIDES:")
        for issue in issues['dates_invalides']:
            print(f"  - {issue}")
        all_good = False
    
    # Conclusion
    print(f"\n{'✅ DONNÉES PRÊTES POUR INTÉGRATION' if all_good else '❌ PROBLÈMES DÉTECTÉS - VALIDATION REQUISE'}")
    
    return all_good

if __name__ == "__main__":
    check_data_quality(year="2023")