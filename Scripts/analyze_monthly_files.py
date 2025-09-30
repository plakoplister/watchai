#!/usr/bin/env python3
"""
Analyse des fichiers mensuels pour comprendre la structure
et identifier les nouvelles entités
"""

import pandas as pd
import os
from pathlib import Path
import json
from datetime import datetime

# Chemins
BASE_DIR = Path("/Users/julienmarboeuf/Documents/MEREYA/AGL/EXPORT-Db")
UPDATES_DIR = BASE_DIR / "Updates_Mensuels"
MASTER_DATA = BASE_DIR / "Master_Data"
VALIDATION_DIR = BASE_DIR / "Validation"

def analyze_monthly_file(filepath):
    """Analyse un fichier mensuel et retourne sa structure"""
    try:
        df = pd.read_excel(filepath)
        
        # Extraire infos du nom de fichier
        filename = os.path.basename(filepath)
        port = "ABIDJAN" if "ABJ" in filename else "SAN PEDRO"
        
        # Identifier mois et année depuis le nom
        parts = filename.replace(".xlsx", "").split(" - ")
        if len(parts) >= 2:
            date_part = parts[1]
        else:
            date_part = "UNKNOWN"
        
        return {
            "file": filename,
            "port": port,
            "date": date_part,
            "rows": len(df),
            "columns": list(df.columns),
            "sample_data": df.head(2).to_dict()
        }
    except Exception as e:
        return {"file": filepath, "error": str(e)}

def get_master_entities():
    """Récupère les entités connues depuis le fichier master"""
    master_file = MASTER_DATA / "DB_Shipping_Master.xlsb"
    
    entities = {
        "exportateurs": set(),
        "destinataires": set(),
        "destinations": set()
    }
    
    try:
        # Lire feuille LIST si elle existe
        xl_file = pd.ExcelFile(master_file, engine='pyxlsb')
        if 'LIST' in xl_file.sheet_names:
            list_df = pd.read_excel(master_file, sheet_name='LIST', engine='pyxlsb')
            print(f"Feuille LIST trouvée avec {len(list_df)} lignes")
            
        # Lire les données principales
        for sheet in ['DB ABJ', 'DB SP']:
            if sheet in xl_file.sheet_names:
                df = pd.read_excel(master_file, sheet_name=sheet, engine='pyxlsb')
                
                if 'EXPORTATEUR SIMPLE' in df.columns:
                    entities['exportateurs'].update(df['EXPORTATEUR SIMPLE'].dropna().unique())
                if 'DESTINATAIRE SIMPLE' in df.columns:
                    entities['destinataires'].update(df['DESTINATAIRE SIMPLE'].dropna().unique())
                if 'DESTINATION' in df.columns:
                    entities['destinations'].update(df['DESTINATION'].dropna().unique())
                    
        print(f"Entités master: {len(entities['exportateurs'])} exportateurs, "
              f"{len(entities['destinataires'])} destinataires, "
              f"{len(entities['destinations'])} destinations")
              
    except Exception as e:
        print(f"Erreur lecture master: {e}")
    
    return entities

def analyze_all_2025_files():
    """Analyse tous les fichiers 2025 disponibles"""
    results = []
    files_2025 = list(UPDATES_DIR.glob("2025/*.xlsx"))
    
    print(f"\n📊 Analyse de {len(files_2025)} fichiers 2025...")
    
    for filepath in sorted(files_2025):
        print(f"  Analyse de {filepath.name}...")
        result = analyze_monthly_file(filepath)
        results.append(result)
    
    # Sauvegarder l'analyse
    output_file = VALIDATION_DIR / f"analyse_structure_{datetime.now().strftime('%Y%m%d')}.json"
    VALIDATION_DIR.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"\n✅ Analyse sauvegardée dans: {output_file}")
    
    # Résumé
    print("\n📋 RÉSUMÉ DE L'ANALYSE:")
    print("-" * 50)
    
    for result in results:
        if 'error' not in result:
            print(f"\n{result['file']}:")
            print(f"  Port: {result['port']}")
            print(f"  Date: {result['date']}")
            print(f"  Lignes: {result['rows']}")
            print(f"  Colonnes: {len(result['columns'])}")
            if result['columns']:
                print(f"  Premières colonnes: {result['columns'][:5]}")
    
    return results

if __name__ == "__main__":
    print("🔍 ANALYSE DES FICHIERS MENSUELS 2025")
    print("=" * 50)
    
    # Analyser structure
    analyze_all_2025_files()
    
    # Récupérer entités master
    print("\n📚 CHARGEMENT DES ENTITÉS MASTER...")
    master_entities = get_master_entities()