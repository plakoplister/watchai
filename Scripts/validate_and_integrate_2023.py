#!/usr/bin/env python3
"""
Script automatique pour valider et intégrer les fichiers 2023
"""

import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import sys

# Chemins
BASE_DIR = Path("/Users/julienmarboeuf/Documents/MEREYA/AGL/EXPORT-Db")
UPDATES_DIR = BASE_DIR / "Updates_Mensuels" / "2023"
MASTER_DATA = BASE_DIR / "Master_Data"
VALIDATION_DIR = BASE_DIR / "Validation"
WEBAPP_DATA = BASE_DIR / "Webapp" / "data"

def validate_2023_files():
    """Valide tous les fichiers 2023"""
    print("="*60)
    print("🔍 VALIDATION DES FICHIERS 2023")
    print("="*60)
    
    # Lister les fichiers Excel de 2023
    files = list(UPDATES_DIR.glob("*.xlsx"))
    print(f"\n📁 {len(files)} fichiers trouvés dans Updates_Mensuels/2023/")
    
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "year": "2023",
        "files_validated": [],
        "total_rows": 0,
        "total_volume_kg": 0,
        "new_entities": {
            "exportateurs": set(),
            "destinataires": set(),
            "destinations": set()
        }
    }
    
    # Charger les entités existantes depuis Entity_Mappings.xlsx
    mappings_file = MASTER_DATA / "Entity_Mappings.xlsx"
    existing_exportateurs = set()
    existing_destinataires = set()
    existing_destinations = set()
    
    try:
        exp_df = pd.read_excel(mappings_file, sheet_name='Exportateurs')
        existing_exportateurs = set(exp_df['EXPORTATEUR SIMPLE'].dropna().unique())
        
        dest_df = pd.read_excel(mappings_file, sheet_name='Destinataires')
        existing_destinataires = set(dest_df['DESTINATAIRE SIMPLE'].dropna().unique())
        
        dest_pays_df = pd.read_excel(mappings_file, sheet_name='Destinations')
        existing_destinations = set(dest_pays_df['DESTINATION SIMPLE'].dropna().unique())
        
        print(f"\n✅ Entités existantes chargées:")
        print(f"   - {len(existing_exportateurs)} exportateurs")
        print(f"   - {len(existing_destinataires)} destinataires")
        print(f"   - {len(existing_destinations)} destinations")
    except Exception as e:
        print(f"⚠️ Erreur chargement Entity_Mappings: {e}")
    
    # Analyser chaque fichier
    for filepath in sorted(files):
        print(f"\n📄 Traitement: {filepath.name}")
        
        try:
            df = pd.read_excel(filepath)
            rows = len(df)
            
            # Calculer le volume (POIDS_NET en kg)
            volume_kg = 0
            if 'POIDS_NET' in df.columns:
                volume_kg = df['POIDS_NET'].sum()
            
            validation_results["total_rows"] += rows
            validation_results["total_volume_kg"] += volume_kg
            
            file_info = {
                "filename": filepath.name,
                "rows": rows,
                "volume_kg": volume_kg,
                "columns": list(df.columns)[:10]  # Premiers colonnes pour référence
            }
            
            # Identifier nouvelles entités (structure 2023)
            if 'NOM_EXPORTATEUR' in df.columns:
                exportateurs = set(df['NOM_EXPORTATEUR'].dropna().unique())
                new_exp = exportateurs - existing_exportateurs
                validation_results["new_entities"]["exportateurs"].update(new_exp)
                file_info["new_exportateurs"] = len(new_exp)
            
            if 'NOM_IMPORTATEUR' in df.columns:
                destinataires = set(df['NOM_IMPORTATEUR'].dropna().unique())
                new_dest = destinataires - existing_destinataires
                validation_results["new_entities"]["destinataires"].update(new_dest)
                file_info["new_destinataires"] = len(new_dest)
            
            if 'PAYS_DESTINATION' in df.columns:
                destinations = set(df['PAYS_DESTINATION'].dropna().unique())
                new_dest_pays = destinations - existing_destinations
                validation_results["new_entities"]["destinations"].update(new_dest_pays)
                file_info["new_destinations"] = len(new_dest_pays)
            
            validation_results["files_validated"].append(file_info)
            
            print(f"   ✅ {rows} lignes, {volume_kg/1000:.2f} tonnes")
            if 'new_exportateurs' in file_info:
                print(f"   🆕 {file_info['new_exportateurs']} nouveaux exportateurs")
                print(f"   🆕 {file_info['new_destinataires']} nouveaux destinataires")
                print(f"   🆕 {file_info['new_destinations']} nouvelles destinations")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            validation_results["files_validated"].append({
                "filename": filepath.name,
                "error": str(e)
            })
    
    # Convertir sets en listes pour JSON
    validation_results["new_entities"]["exportateurs"] = list(validation_results["new_entities"]["exportateurs"])
    validation_results["new_entities"]["destinataires"] = list(validation_results["new_entities"]["destinataires"])
    validation_results["new_entities"]["destinations"] = list(validation_results["new_entities"]["destinations"])
    
    # Sauvegarder résultats de validation
    validation_file = VALIDATION_DIR / f"validation_2023_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    VALIDATION_DIR.mkdir(exist_ok=True)
    
    with open(validation_file, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DE LA VALIDATION")
    print("="*60)
    print(f"✅ Fichiers validés: {len(files)}")
    print(f"📈 Total lignes: {validation_results['total_rows']:,}")
    print(f"⚖️ Volume total: {validation_results['total_volume_kg']/1000:,.2f} tonnes")
    print(f"\n🆕 Nouvelles entités détectées:")
    print(f"   - {len(validation_results['new_entities']['exportateurs'])} exportateurs")
    print(f"   - {len(validation_results['new_entities']['destinataires'])} destinataires")
    print(f"   - {len(validation_results['new_entities']['destinations'])} destinations")
    print(f"\n💾 Validation sauvegardée: {validation_file.name}")
    
    return validation_results

def integrate_to_webapp(validation_results):
    """Intègre les données validées dans la webapp"""
    print("\n" + "="*60)
    print("🚀 INTÉGRATION DANS LA WEBAPP")
    print("="*60)
    
    # Charger ou créer le fichier data.json de la webapp
    data_file = WEBAPP_DATA / "data.json"
    
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            webapp_data = json.load(f)
        print(f"📂 Données webapp existantes chargées")
    else:
        webapp_data = {
            "last_update": None,
            "years_available": [],
            "statistics": {},
            "files_integrated": []
        }
        print(f"🆕 Création nouvelle structure webapp")
    
    # Mettre à jour les données
    webapp_data["last_update"] = datetime.now().isoformat()
    
    if "2023" not in webapp_data["years_available"]:
        webapp_data["years_available"].append("2023")
    
    # Ajouter statistiques 2023
    webapp_data["statistics"]["2023"] = {
        "files_count": len(validation_results["files_validated"]),
        "total_rows": validation_results["total_rows"],
        "total_volume_tonnes": validation_results["total_volume_kg"] / 1000,
        "new_entities": {
            "exportateurs": len(validation_results["new_entities"]["exportateurs"]),
            "destinataires": len(validation_results["new_entities"]["destinataires"]),
            "destinations": len(validation_results["new_entities"]["destinations"])
        }
    }
    
    # Ajouter les fichiers intégrés
    for file_info in validation_results["files_validated"]:
        if "error" not in file_info:
            webapp_data["files_integrated"].append({
                "year": "2023",
                "filename": file_info["filename"],
                "integration_date": datetime.now().isoformat(),
                "rows": file_info["rows"],
                "volume_kg": file_info["volume_kg"]
            })
    
    # Sauvegarder
    WEBAPP_DATA.mkdir(parents=True, exist_ok=True)
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(webapp_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Données intégrées dans: {data_file}")
    print(f"📊 Statistiques 2023 ajoutées à la webapp")
    
    # Créer un rapport d'intégration
    report_file = VALIDATION_DIR / f"integration_report_2023_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    integration_report = {
        "timestamp": datetime.now().isoformat(),
        "year": "2023",
        "files_integrated": len([f for f in validation_results["files_validated"] if "error" not in f]),
        "webapp_data_updated": True,
        "webapp_statistics": webapp_data["statistics"]["2023"]
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(integration_report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Rapport d'intégration: {report_file.name}")
    
    return integration_report

def main():
    print("\n🎯 DÉMARRAGE DU PROCESSUS DE VALIDATION ET INTÉGRATION 2023")
    print("="*70)
    
    try:
        # Étape 1: Validation
        validation_results = validate_2023_files()
        
        # Étape 2: Intégration
        if validation_results["files_validated"]:
            integration_report = integrate_to_webapp(validation_results)
            
            print("\n" + "="*70)
            print("✨ PROCESSUS TERMINÉ AVEC SUCCÈS!")
            print("="*70)
            print(f"✅ {len(validation_results['files_validated'])} fichiers validés")
            print(f"✅ Données intégrées dans la webapp")
            print(f"✅ Nouvelles entités identifiées pour validation manuelle")
            
            # Suggestions pour la suite
            print("\n📋 PROCHAINES ÉTAPES:")
            print("1. Vérifier les nouvelles entités dans l'interface de validation")
            print("2. Mapper les entités non reconnues vers les entités existantes")
            print("3. Lancer la webapp pour visualiser les données 2023")
            print(f"   cd Webapp && python3 webapp_volumes_reels.py")
            
            return 0
        else:
            print("⚠️ Aucun fichier à intégrer")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())