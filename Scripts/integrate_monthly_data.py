#!/usr/bin/env python3
"""
Script d'intégration des données mensuelles validées dans DB_Shipping_Master.xlsx
VERSION CORRIGÉE - Respecte le format exact des colonnes
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import shutil

# Chemins
BASE_DIR = Path("/Users/julienmarboeuf/Documents/BON PLEIN/WATCHAI")
UPDATES_DIR = BASE_DIR / "Updates_Mensuels"
MASTER_DATA = BASE_DIR / "Master_Data"
VALIDATION_DIR = BASE_DIR / "Validation"
BACKUPS_DIR = BASE_DIR / "Backups"

def get_country_code_mapping():
    """Mapping des noms de pays vers codes ISO"""
    return {
        'PAYS-BAS': 'NL',
        'ALLEMAGNE': 'DE', 
        'BELGIQUE': 'BE',
        'FRANCE': 'FR',
        'ESPAGNE': 'ES',
        'ITALIE': 'IT',
        'ROYAUME-UNI': 'GB',
        'ETATS-UNIS': 'US',
        'RUSSIE': 'RU',
        'MALAISIE': 'MY',
        'SINGAPOUR': 'SG',
        'INDONESIE': 'ID',
        'TURQUIE': 'TR',
        'UKRAINE': 'UA',
        'ESTONIE': 'EE',
        'LITUANIE': 'LT',
        'LETTONIE': 'LV',
        'POLOGNE': 'PL',
        'AUTRE': 'XX'  # Code générique pour destinations non-spécifiées
    }

def load_entity_mappings():
    """Charge les mappings appris depuis Entity_Mappings.xlsx"""
    mappings_file = MASTER_DATA / "Entity_Mappings.xlsx"
    mappings = {'exportateurs': {}, 'destinataires': {}}
    
    try:
        # Lire mappings exportateurs
        exp_df = pd.read_excel(mappings_file, sheet_name='Exportateurs')
        for _, row in exp_df.iterrows():
            if pd.notna(row.get('EXPORTATEUR')) and pd.notna(row.get('EXPORTATEUR SIMPLE')):
                mappings['exportateurs'][str(row['EXPORTATEUR']).strip()] = str(row['EXPORTATEUR SIMPLE']).strip()
        
        # Lire mappings destinataires  
        dest_df = pd.read_excel(mappings_file, sheet_name='Destinataires')
        for _, row in dest_df.iterrows():
            if pd.notna(row.get('DESTINATAIRE')) and pd.notna(row.get('DESTINATAIRE SIMPLE')):
                mappings['destinataires'][str(row['DESTINATAIRE']).strip()] = str(row['DESTINATAIRE SIMPLE']).strip()
        
        print(f"✅ Mappings chargés: {len(mappings['exportateurs'])} exportateurs, {len(mappings['destinataires'])} destinataires")
        return mappings
        
    except Exception as e:
        print(f"⚠️ Erreur chargement mappings: {e}")
        return mappings

def transform_monthly_data_to_master_format(filepath, entity_mappings):
    """
    Transforme les données mensuelles selon le format exact DB_Shipping_Master
    Gère les deux formats : avant et après mars 2024
    """
    try:
        df = pd.read_excel(filepath)
        print(f"📄 Lecture {filepath.name}: {len(df):,} lignes")
        
        # Créer DataFrame avec colonnes exactes DB_Shipping_Master
        master_df = pd.DataFrame()
        
        # Détecter le format (ancien, nouveau, juillet 2025, ou août 2025)
        is_new_format = 'DATE_DECLARATION' in df.columns
        is_july_2025_format = 'TOT_PDSNET' in df.columns or 'CLIENT_EXPORT' in df.columns
        is_august_2025_format = 'DATENR' in df.columns and 'PDSNET' in df.columns and 'DESTINATAIRE' in df.columns
        
        # A. DATENR ← DATE selon le format
        if is_july_2025_format and 'DATE_DEC' in df.columns:
            # Format juillet 2025 : DATE_DEC
            master_df['DATENR'] = pd.to_datetime(df['DATE_DEC'], errors='coerce')
        elif is_new_format and 'DATE_DECLARATION' in df.columns:
            # Nouveau format (après mars 2024) : DATE_DECLARATION déjà en format date
            master_df['DATENR'] = pd.to_datetime(df['DATE_DECLARATION'], errors='coerce')
        elif 'DECLARATION_DATE' in df.columns:
            # Extraire l'année du nom de fichier (ex: "ABJ - DEC 2023.xlsx")
            import re
            year_match = re.search(r'(\d{4})', filepath.name)
            year = year_match.group(1) if year_match else '2023'

            # Mapping mois français → anglais
            french_months = {
                'janv': 'Jan', 'févr': 'Feb', 'mars': 'Mar', 'avr': 'Apr',
                'mai': 'May', 'juin': 'Jun', 'juil': 'Jul', 'août': 'Aug',
                'sept': 'Sep', 'oct': 'Oct', 'nov': 'Nov', 'déc': 'Dec'
            }

            def convert_french_date(date_str):
                date_str = str(date_str)
                for fr, en in french_months.items():
                    date_str = date_str.replace(fr, en)
                return f"{date_str}-{year}"

            # Convertir "15-déc" → "15-Dec-2023" puis en datetime
            dates_converted = df['DECLARATION_DATE'].apply(convert_french_date)
            master_df['DATENR'] = pd.to_datetime(dates_converted, format='%d-%b-%Y', errors='coerce')
        elif 'DATENR' in df.columns:
            # Format août 2025 : colonne DATENR existe déjà avec les dates
            print(f"📅 Utilisation de la colonne DATENR existante pour {filepath.name}")
            master_df['DATENR'] = pd.to_datetime(df['DATENR'], errors='coerce')
        else:
            print(f"⚠️ Aucune colonne de date trouvée dans {filepath.name}")
            print(f"   Colonnes disponibles: {list(df.columns)}")
            return None, None, 0, 0
        
        # B. ORIGINE ← Toujours "CI" 
        master_df['ORIGINE'] = 'CI'
        
        # C. DESTINATION ← Selon le format
        if is_july_2025_format and 'CODE_PAYS_DESTINATION' in df.columns:
            # Format juillet 2025 : CODE_PAYS_DESTINATION
            master_df['DESTINATION'] = df['CODE_PAYS_DESTINATION']
        elif is_new_format and 'DESTINATION' in df.columns:
            # Nouveau format : DESTINATION déjà en code ISO
            master_df['DESTINATION'] = df['DESTINATION']
        elif 'DESTINATION' in df.columns:
            # Format août 2025 : colonne DESTINATION directe
            print(f"📍 Utilisation de la colonne DESTINATION existante pour {filepath.name}")
            master_df['DESTINATION'] = df['DESTINATION']
        elif 'PAYS_DESTINATION' in df.columns:
            # Ancien format : PAYS_DESTINATION à convertir en code ISO
            country_mapping = get_country_code_mapping()
            master_df['DESTINATION'] = df['PAYS_DESTINATION'].apply(
                lambda x: country_mapping.get(str(x).strip().upper(), str(x).strip().upper()[:2]) if pd.notna(x) else 'XX'
            )
        else:
            print(f"⚠️ Colonne DESTINATION/PAYS_DESTINATION manquante dans {filepath.name}")
            return None, None, 0, 0
        
        # D. EXPORTATEUR ← Selon le format
        if is_july_2025_format and 'OPERATEUR' in df.columns:
            # Format juillet 2025 : OPERATEUR
            master_df['EXPORTATEUR'] = df['OPERATEUR']
        elif is_new_format and 'EXPORTATEUR' in df.columns:
            # Nouveau format : colonne EXPORTATEUR
            master_df['EXPORTATEUR'] = df['EXPORTATEUR']
        elif 'EXPORTATEUR' in df.columns:
            # Format août 2025 : colonne EXPORTATEUR directe
            print(f"🏭 Utilisation de la colonne EXPORTATEUR existante pour {filepath.name}")
            master_df['EXPORTATEUR'] = df['EXPORTATEUR']
        elif 'NOM_EXPORTATEUR' in df.columns:
            # Ancien format : colonne NOM_EXPORTATEUR
            master_df['EXPORTATEUR'] = df['NOM_EXPORTATEUR']
        else:
            print(f"⚠️ Colonne EXPORTATEUR/NOM_EXPORTATEUR manquante dans {filepath.name}")
            return None, None, 0, 0
        
        # E. DESTINATAIRE ← Selon le format
        if is_july_2025_format and 'CLIENT_EXPORT' in df.columns:
            # Format juillet 2025 : CLIENT_EXPORT
            master_df['DESTINATAIRE'] = df['CLIENT_EXPORT']
        elif is_new_format and 'DESTINATAIRE' in df.columns:
            # Nouveau format : colonne DESTINATAIRE
            master_df['DESTINATAIRE'] = df['DESTINATAIRE']
        elif 'DESTINATAIRE' in df.columns:
            # Format août 2025 : colonne DESTINATAIRE directe
            print(f"🏢 Utilisation de la colonne DESTINATAIRE existante pour {filepath.name}")
            master_df['DESTINATAIRE'] = df['DESTINATAIRE']
        elif 'NOM_IMPORTATEUR' in df.columns:
            # Ancien format : colonne NOM_IMPORTATEUR
            master_df['DESTINATAIRE'] = df['NOM_IMPORTATEUR']
        else:
            print(f"⚠️ Colonne DESTINATAIRE/NOM_IMPORTATEUR manquante dans {filepath.name}")
            return None, None, 0, 0
        
        # F. POSTAR ← Selon le format
        if is_august_2025_format and 'POSTAR' in df.columns:
            # Format août 2025 : POSTAR (copie directe)
            print(f"🏷️ Utilisation de la colonne POSTAR existante pour {filepath.name}")
            master_df['POSTAR'] = df['POSTAR']
        elif is_july_2025_format and 'POSTAR' in df.columns:
            # Format juillet 2025 : POSTAR (même nom)
            master_df['POSTAR'] = df['POSTAR']
        elif is_new_format and 'POSTAR' in df.columns:
            # Nouveau format : colonne POSTAR
            master_df['POSTAR'] = df['POSTAR']
        elif 'CODE_SH2' in df.columns:
            # Ancien format : colonne CODE_SH2
            master_df['POSTAR'] = df['CODE_SH2']
        else:
            print(f"⚠️ Colonne POSTAR/CODE_SH2 manquante dans {filepath.name}")
            master_df['POSTAR'] = ''
        
        # G. PDSNET ← Selon le format
        if is_august_2025_format and 'PDSNET' in df.columns:
            # Format août 2025 : PDSNET directement
            print(f"⚖️ Utilisation de la colonne PDSNET existante pour {filepath.name}")
            master_df['PDSNET'] = df['PDSNET']
            total_weight = df['PDSNET'].sum()
        elif is_july_2025_format and 'TOT_PDSNET' in df.columns:
            # Format juillet 2025 : TOT_PDSNET
            master_df['PDSNET'] = df['TOT_PDSNET']
            total_weight = df['TOT_PDSNET'].sum()
        elif 'POIDS_NET' in df.columns:
            # Formats précédents : POIDS_NET
            master_df['PDSNET'] = df['POIDS_NET']
            total_weight = df['POIDS_NET'].sum()
        else:
            print(f"⚠️ Colonne POIDS_NET/TOT_PDSNET/PDSNET manquante dans {filepath.name}")
            master_df['PDSNET'] = 0
            total_weight = 0
        
        # H. EXPORTATEUR SIMPLE ← mapping selon le format
        if is_august_2025_format and 'EXPORTATEUR' in df.columns:
            # Format août 2025 : lookup sur EXPORTATEUR avec fallback
            print(f"🏭 Application du mapping EXPORTATEUR SIMPLE pour {filepath.name}")
            master_df['EXPORTATEUR SIMPLE'] = df['EXPORTATEUR'].apply(
                lambda x: entity_mappings['exportateurs'].get(str(x).strip(), str(x).strip()) if pd.notna(x) else x
            )
        elif is_july_2025_format and 'OPERATEUR' in df.columns:
            master_df['EXPORTATEUR SIMPLE'] = df['OPERATEUR'].apply(
                lambda x: entity_mappings['exportateurs'].get(str(x).strip(), str(x).strip()) if pd.notna(x) else x
            )
        elif is_new_format and 'EXPORTATEUR' in df.columns:
            master_df['EXPORTATEUR SIMPLE'] = df['EXPORTATEUR'].apply(
                lambda x: entity_mappings['exportateurs'].get(str(x).strip(), str(x).strip()) if pd.notna(x) else x
            )
        elif 'NOM_EXPORTATEUR' in df.columns:
            master_df['EXPORTATEUR SIMPLE'] = df['NOM_EXPORTATEUR'].apply(
                lambda x: entity_mappings['exportateurs'].get(str(x).strip(), str(x).strip()) if pd.notna(x) else x
            )
        else:
            master_df['EXPORTATEUR SIMPLE'] = ''
        
        # I. DESTINATAIRE SIMPLE ← mapping selon le format (avec normalisation)
        if is_august_2025_format and 'DESTINATAIRE' in df.columns:
            # Format août 2025 : lookup sur DESTINATAIRE avec fallback
            print(f"🏢 Application du mapping DESTINATAIRE SIMPLE pour {filepath.name}")
            def normalize_and_map_destinataire(x):
                if pd.isna(x):
                    return ''

                original = str(x).strip()

                # Normaliser pour le matching exact
                normalized = original.replace('\n', ' ').replace('  ', ' ').strip().upper()

                # Chercher d'abord un match exact
                for key, value in entity_mappings['destinataires'].items():
                    key_normalized = str(key).replace('\n', ' ').replace('  ', ' ').strip().upper()
                    if key_normalized == normalized:
                        return value

                # Si pas mappé, retourner l'original - l'app validation gérera
                return original

            master_df['DESTINATAIRE SIMPLE'] = df['DESTINATAIRE'].apply(normalize_and_map_destinataire)
        elif is_july_2025_format and 'CLIENT_EXPORT' in df.columns:
            def normalize_and_map_destinataire(x):
                if pd.isna(x):
                    return ''

                original = str(x).strip()

                # Normaliser pour le matching exact
                normalized = original.replace('\n', ' ').replace('  ', ' ').strip().upper()

                # Chercher d'abord un match exact
                for key, value in entity_mappings['destinataires'].items():
                    key_normalized = str(key).replace('\n', ' ').replace('  ', ' ').strip().upper()
                    if key_normalized == normalized:
                        return value

                # Si pas mappé, retourner l'original - l'app validation gérera
                return original

            master_df['DESTINATAIRE SIMPLE'] = df['CLIENT_EXPORT'].apply(normalize_and_map_destinataire)
        elif is_new_format and 'DESTINATAIRE' in df.columns:
            def normalize_and_map_destinataire(x):
                if pd.isna(x):
                    return ''

                original = str(x).strip()

                # Normaliser pour le matching exact
                normalized = original.replace('\n', ' ').replace('  ', ' ').strip().upper()

                # Chercher d'abord un match exact
                for key, value in entity_mappings['destinataires'].items():
                    key_normalized = str(key).replace('\n', ' ').replace('  ', ' ').strip().upper()
                    if key_normalized == normalized:
                        return value

                # Si pas mappé, retourner l'original - l'app validation gérera
                return original

            master_df['DESTINATAIRE SIMPLE'] = df['DESTINATAIRE'].apply(normalize_and_map_destinataire)
        elif 'NOM_IMPORTATEUR' in df.columns:
            def normalize_and_map_destinataire(x):
                if pd.isna(x):
                    return ''

                original = str(x).strip()

                # Normaliser pour le matching exact
                normalized = original.replace('\n', ' ').replace('  ', ' ').strip().upper()

                # Chercher d'abord un match exact
                for key, value in entity_mappings['destinataires'].items():
                    key_normalized = str(key).replace('\n', ' ').replace('  ', ' ').strip().upper()
                    if key_normalized == normalized:
                        return value

                # Si pas mappé, retourner l'original - l'app validation gérera
                return original

            master_df['DESTINATAIRE SIMPLE'] = df['NOM_IMPORTATEUR'].apply(normalize_and_map_destinataire)
        else:
            master_df['DESTINATAIRE SIMPLE'] = ''
        
        # Déterminer le port
        port = "ABIDJAN" if "ABJ" in filepath.name else "SAN_PEDRO"

        # Réordonner les colonnes selon le mapping A→I fixe pour DB_Shipping_Master.xlsx
        column_order = [
            'DATENR',           # A
            'ORIGINE',          # B
            'DESTINATION',      # C
            'EXPORTATEUR',      # D
            'DESTINATAIRE',     # E
            'POSTAR',           # F
            'PDSNET',           # G
            'EXPORTATEUR SIMPLE', # H
            'DESTINATAIRE SIMPLE' # I
        ]

        # Vérifier que toutes les colonnes existent et les réordonner
        missing_cols = [col for col in column_order if col not in master_df.columns]
        if missing_cols:
            print(f"⚠️ Colonnes manquantes dans {filepath.name}: {missing_cols}")
            # Ajouter les colonnes manquantes avec des valeurs vides
            for col in missing_cols:
                master_df[col] = ''

        # Réordonner le DataFrame selon l'ordre A→I
        master_df = master_df[column_order]

        print(f"✅ Transformation réussie: {len(master_df):,} lignes, {total_weight/1000:,.0f} tonnes")
        print(f"📋 Ordre colonnes A→I: {', '.join(master_df.columns)}")
        return master_df, port, len(master_df), total_weight
        
    except Exception as e:
        print(f"❌ Erreur transformation {filepath}: {e}")
        return None, None, 0, 0

def backup_master_database():
    """Crée une sauvegarde du master avant intégration"""
    master_file = MASTER_DATA / "DB_Shipping_Master.xlsx"
    
    if not master_file.exists():
        print("⚠️ Fichier master non trouvé")
        return None
    
    # Créer dossier backups
    BACKUPS_DIR.mkdir(exist_ok=True)
    
    # Nom de sauvegarde avec timestamp
    backup_name = f"DB_Shipping_Master_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    backup_path = BACKUPS_DIR / backup_name
    
    try:
        shutil.copy2(master_file, backup_path)
        print(f"✅ Sauvegarde créée: {backup_name}")
        return backup_path
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")
        return None

def integrate_selected_files(selected_file_paths, validation_file=None, dry_run=False):
    """
    Intègre des fichiers spécifiques sélectionnés dans DB_Shipping_Master.xlsx

    Args:
        selected_file_paths: Liste des chemins de fichiers à intégrer
        validation_file: Fichier de validation JSON (optionnel)
        dry_run: Si True, simule l'intégration sans modifier les fichiers
    """

    print(f"🚀 INTÉGRATION DE {len(selected_file_paths)} FICHIERS SÉLECTIONNÉS")
    print("="*60)

    # Afficher les fichiers sélectionnés
    print("📁 Fichiers à intégrer:")
    for file_path in selected_file_paths:
        print(f"   • {file_path.name}")

    # Charger les mappings appris
    print("🔗 Chargement des mappings appris...")
    entity_mappings = load_entity_mappings()
    print(f"✅ Mappings chargés")

    if not selected_file_paths:
        print("❌ Aucun fichier à traiter")
        return {'files_processed': 0, 'total_lines': 0, 'total_volume_kg': 0, 'errors': []}

    # Statistiques d'intégration
    total_lines = 0
    total_volume_kg = 0
    files_processed = 0
    errors = []

    # Dictionnaires pour accumuler les données par port
    final_data = {'ABIDJAN': None, 'SAN_PEDRO': None}

    # Traitement de chaque fichier sélectionné
    for filepath in selected_file_paths:
        try:
            print(f"\n📄 Traitement: {filepath.name}")

            # Transformer selon le format exact DB_Shipping_Master
            master_df, port, lines, volume_kg = transform_monthly_data_to_master_format(filepath, entity_mappings)

            print(f"✅ {filepath.name}: {lines:,} lignes, {volume_kg:,} kg, Port: {port}")

            # Accumuler les données par port
            if port in final_data:
                if final_data[port] is None:
                    final_data[port] = master_df
                else:
                    final_data[port] = pd.concat([final_data[port], master_df], ignore_index=True)

            total_lines += lines
            total_volume_kg += volume_kg
            files_processed += 1

        except Exception as e:
            error_msg = f"❌ Erreur {filepath.name}: {e}"
            print(error_msg)
            errors.append(error_msg)

    if dry_run:
        print(f"\n🔍 MODE TEST - Aucune modification des fichiers")
        print(f"📊 Résumé: {files_processed} fichiers, {total_lines:,} lignes, {total_volume_kg:,} kg")
        return {
            'files_processed': files_processed,
            'total_lines': total_lines,
            'total_volume_kg': total_volume_kg,
            'errors': errors
        }

    # INTÉGRATION RÉELLE dans DB_Shipping_Master.xlsx
    if any(data is not None for data in final_data.values()):
        print(f"\n💾 INTÉGRATION DANS DB_Shipping_Master.xlsx...")

        # Créer sauvegarde avant modification
        backup_master_database()

        master_file = MASTER_DATA / "DB_Shipping_Master.xlsx"

        # Charger les données existantes
        with pd.ExcelFile(master_file, engine='openpyxl') as xls:
            updated_sheets = {}
            for sheet_name in xls.sheet_names:
                updated_sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)

        # Ajouter les nouvelles données aux feuilles correspondantes
        if final_data['ABIDJAN'] is not None:
            original_count = len(updated_sheets['DB ABJ'])
            updated_sheets['DB ABJ'] = pd.concat([updated_sheets['DB ABJ'], final_data['ABIDJAN']], ignore_index=True)
            added_count = len(updated_sheets['DB ABJ']) - original_count
            print(f"✅ DB ABJ: +{added_count:,} lignes ajoutées")

        if final_data['SAN_PEDRO'] is not None:
            original_count = len(updated_sheets['DB SP'])
            updated_sheets['DB SP'] = pd.concat([updated_sheets['DB SP'], final_data['SAN_PEDRO']], ignore_index=True)
            added_count = len(updated_sheets['DB SP']) - original_count
            print(f"✅ DB SP: +{added_count:,} lignes ajoutées")

        # Sauvegarder avec gestion d'erreur pour gros fichiers
        print("💾 Sauvegarde du master mis à jour...")

        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Créer un fichier temporaire d'abord
                temp_file = master_file.parent / f"temp_{master_file.name}"

                with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
                    for sheet_name, df in updated_sheets.items():
                        print(f"   Écriture feuille {sheet_name}: {len(df):,} lignes...")
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

                # Si succès, remplacer le fichier original
                if temp_file.exists():
                    shutil.move(str(temp_file), str(master_file))
                break

            except (TimeoutError, OSError) as e:
                print(f"⚠️  Tentative {attempt + 1}/{max_retries} échouée: {e}")
                if temp_file.exists():
                    temp_file.unlink()
                if attempt < max_retries - 1:
                    print("   Attente 5 secondes avant retry...")
                    time.sleep(5)
                else:
                    raise Exception(f"Impossible d'écrire le fichier après {max_retries} tentatives")

        print("✅ DB_Shipping_Master.xlsx mis à jour avec succès!")
        print(f"📊 Taille finale: {master_file.stat().st_size / (1024*1024):.1f} MB")

        # Créer rapport d'intégration
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        report_file = VALIDATION_DIR / f"integration_report_selected_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'integration_date': datetime.now().isoformat(),
                'files_processed': [str(f) for f in selected_file_paths],
                'total_files': files_processed,
                'total_lines': int(total_lines),
                'total_volume_kg': int(total_volume_kg),
                'errors': errors
            }, f, indent=2, ensure_ascii=False)

    return {
        'files_processed': files_processed,
        'total_lines': total_lines,
        'total_volume_kg': total_volume_kg,
        'errors': errors
    }

def integrate_monthly_data(year="2023", validation_file=None, dry_run=False):
    """
    Intègre les données mensuelles validées dans DB_Shipping_Master.xlsx
    PROMIS: Cette fois ça va marcher !
    """
    
    print(f"🚀 INTÉGRATION DES DONNÉES {year}")
    print("="*60)
    
    # Charger les mappings appris
    print("🔗 Chargement des mappings appris...")
    entity_mappings = load_entity_mappings()
    print(f"✅ Mappings chargés")
    
    # Liste des fichiers à intégrer (SEULEMENT les nouveaux fichiers dans le dossier racine Updates_Mensuels)
    files = list(UPDATES_DIR.glob("*.xlsx"))
    files = [f for f in files if not f.name.startswith('~$')]  # Ignorer les fichiers temporaires Excel
    print(f"📁 Nouveaux fichiers trouvés dans Updates_Mensuels/: {len(files)}")

    # Afficher la liste des fichiers pour confirmation
    if files:
        print("   Fichiers à intégrer:")
        for f in files:
            print(f"   • {f.name}")
    else:
        print("   Aucun nouveau fichier dans le dossier Updates_Mensuels/")
    
    if not files:
        print("❌ Aucun fichier à traiter")
        return {'files_processed': 0, 'total_lines': 0, 'total_volume_kg': 0, 'errors': []}
    
    # Statistiques d'intégration
    integration_stats = {
        'files_processed': 0,
        'total_lines': 0,
        'total_volume_kg': 0,
        'errors': []
    }
    
    # Données transformées par port
    transformed_data = {
        'ABIDJAN': [],
        'SAN_PEDRO': []
    }
    
    print(f"\n📊 TRANSFORMATION DES FICHIERS:")
    print("-" * 40)
    
    for filepath in sorted(files):
        print(f"🔄 Traitement de {filepath.name}...")
        # Transformer selon le format exact DB_Shipping_Master
        master_df, port, lines, volume_kg = transform_monthly_data_to_master_format(filepath, entity_mappings)
        print(f"   Résultat: {lines} lignes, {volume_kg/1000:.1f} tonnes")
        
        if master_df is not None and port is not None:
            transformed_data[port].append(master_df)
            
            # Mettre à jour stats
            integration_stats['files_processed'] += 1
            integration_stats['total_lines'] += lines
            integration_stats['total_volume_kg'] += volume_kg
        else:
            integration_stats['errors'].append(filepath.name)
    
    # Consolider par port
    print(f"\n🔗 CONSOLIDATION PAR PORT:")
    print("-" * 40)
    
    final_data = {}
    for port, dataframes in transformed_data.items():
        if dataframes:
            consolidated_df = pd.concat(dataframes, ignore_index=True)
            final_data[port] = consolidated_df
            print(f"  {port}: {len(consolidated_df):,} lignes consolidées")
    
    # Afficher résumé
    print(f"\n📋 RÉSUMÉ DE LA TRANSFORMATION:")
    print("="*40)
    print(f"  Fichiers traités: {integration_stats['files_processed']}/{len(files)}")
    print(f"  Total lignes: {integration_stats['total_lines']:,}")
    print(f"  Total volume: {integration_stats['total_volume_kg']/1000:,.0f} tonnes")
    
    if integration_stats['errors']:
        print(f"  Erreurs: {len(integration_stats['errors'])}")
        for error_file in integration_stats['errors']:
            print(f"    - {error_file}")
    
    if dry_run:
        print(f"\n🔍 MODE TEST - Aucune modification apportée aux fichiers")
        return integration_stats
    else:
        # Effectuer l'intégration réelle
        print(f"\n💾 INTÉGRATION DANS DB_Shipping_Master.xlsx...")
        
        # Sauvegarder le master actuel
        backup_path = backup_master_database()
        if not backup_path:
            print("❌ Impossible de continuer sans sauvegarde")
            return integration_stats
        
        master_file = MASTER_DATA / "DB_Shipping_Master.xlsx"
        
        try:
            # Lire le master existant
            print("📖 Lecture du master existant...")
            existing_sheets = {}
            with pd.ExcelFile(master_file, engine='openpyxl') as xls:
                for sheet_name in xls.sheet_names:
                    existing_sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)
                    print(f"📊 Feuille {sheet_name}: {len(existing_sheets[sheet_name]):,} lignes existantes")
            
            # Ajouter nouvelles données aux feuilles appropriées
            updated_sheets = existing_sheets.copy()
            
            if 'ABIDJAN' in final_data and 'DB ABJ' in updated_sheets:
                original_count = len(updated_sheets['DB ABJ'])
                updated_sheets['DB ABJ'] = pd.concat([updated_sheets['DB ABJ'], final_data['ABIDJAN']], ignore_index=True)
                added_count = len(updated_sheets['DB ABJ']) - original_count
                print(f"✅ DB ABJ: +{added_count:,} lignes ajoutées")
            
            if 'SAN_PEDRO' in final_data and 'DB SP' in updated_sheets:
                original_count = len(updated_sheets['DB SP'])
                updated_sheets['DB SP'] = pd.concat([updated_sheets['DB SP'], final_data['SAN_PEDRO']], ignore_index=True)
                added_count = len(updated_sheets['DB SP']) - original_count
                print(f"✅ DB SP: +{added_count:,} lignes ajoutées")
            
            # Sauvegarder directement en .xlsx avec gestion d'erreur pour gros fichiers
            print("💾 Sauvegarde du master mis à jour...")

            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Créer un fichier temporaire d'abord
                    temp_file = master_file.parent / f"temp_{master_file.name}"

                    with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
                        for sheet_name, df in updated_sheets.items():
                            print(f"   Écriture feuille {sheet_name}: {len(df):,} lignes...")
                            df.to_excel(writer, sheet_name=sheet_name, index=False)

                    # Si succès, remplacer le fichier original
                    if temp_file.exists():
                        shutil.move(str(temp_file), str(master_file))
                    break

                except (TimeoutError, OSError) as e:
                    print(f"⚠️  Tentative {attempt + 1}/{max_retries} échouée: {e}")
                    if temp_file.exists():
                        temp_file.unlink()
                    if attempt < max_retries - 1:
                        print("   Attente 5 secondes avant retry...")
                        time.sleep(5)
                    else:
                        raise Exception(f"Impossible d'écrire le fichier après {max_retries} tentatives")
            
            print("✅ DB_Shipping_Master.xlsx mis à jour avec succès!")
            print(f"📊 Taille finale: {master_file.stat().st_size / (1024*1024):.1f} MB")
            
            # Créer rapport d'intégration
            report_file = VALIDATION_DIR / f"integration_report_{year}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'integration_date': datetime.now().isoformat(),
                    'year_processed': year,
                    'stats': integration_stats,
                    'backup_file': str(backup_path)
                }, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Rapport sauvegardé: {report_file.name}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'intégration: {e}")
            print(f"💾 Fichier de sauvegarde disponible: {backup_path}")
            import traceback
            traceback.print_exc()
    
    return integration_stats

if __name__ == "__main__":
    # Intégration réelle des données 2025
    print("🚀 INTÉGRATION DES DONNÉES 2025 - OPTIMISÉE") 
    stats = integrate_monthly_data(year="2025", dry_run=False)  # Mode réel
    print(f"\n📊 RÉSULTAT FINAL: {stats}")