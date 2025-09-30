#!/usr/bin/env python3
"""
Interface web de validation des nouvelles entités
avant intégration dans la base master
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import os
from difflib import get_close_matches
import re
from integrate_monthly_data import load_entity_mappings

st.set_page_config(
    page_title="WatchAI - Validation Export",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Chemins
BASE_DIR = Path("/Users/julienmarboeuf/Documents/BON PLEIN/WATCHAI")
UPDATES_DIR = BASE_DIR / "Updates_Mensuels"
MASTER_DATA = BASE_DIR / "Master_Data"
VALIDATION_DIR = BASE_DIR / "Validation"

def normalize_for_exact_match(full_name):
    """Normalise un nom pour correspondance exacte (garde tout le contenu)"""
    if pd.isna(full_name):
        return ""
    
    name = str(full_name).upper().strip()
    
    # Normaliser les retours à la ligne → espaces
    name = re.sub(r'[\n\r]+', ' ', name)
    
    # Nettoyer espaces multiples seulement
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    
    return name

def extract_company_core_name(full_name):
    """Extrait le nom principal de l'entreprise (sans adresse/BP)"""
    if pd.isna(full_name):
        return ""
    
    name = normalize_for_exact_match(full_name)
    
    # Mots/expressions à ignorer pour extraire le nom principal
    ignore_patterns = [
        r'\d+\s*BP\s+\d+.*',  # Adresses BP
        r'BP\s+[A-Z]*\s*\d+.*',  # Variantes BP
        r'\d+\s*RUE\s+.*',  # Adresses rue
        r'ABIDJAN.*', r'SAN.?PEDRO.*', r'VILLE.*',  # Villes
        r'ZONE\s+\d+.*', r'COCODY.*', r'MARCORY.*',  # Quartiers
        r'IMPORT.?EXPORT.*', r'TRADING.*', r'INTERNATIONAL.*',  # Suffixes commerciaux
        r'CI$', r'COTE\s+D.?IVOIRE$'  # Suffixes pays
    ]
    
    # Appliquer les patterns d'exclusion
    for pattern in ignore_patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Nettoyer les espaces multiples et la ponctuation
    name = re.sub(r'[,\.;:\(\)]+', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    
    return name

def group_destinataires_intelligent(entities_dict):
    """Regroupe intelligemment les destinataires avec règles spéciales"""
    groups = {}
    
    # Mappings spéciaux pour destinataires - CONSERVATEUR pour garder la granularité marché
    special_mappings = {
        # Seulement les aliases évidents, pas de regroupement excessif
        'BC': 'BARRY',  # BC = Barry Callebaut
        'B C': 'BARRY',
        
        'THEOBROMA': 'ECOM',  # Theobroma appartient à ECOM
        'ATLANTIC': 'ECOM',   # Atlantic aussi
        
        'OUTSPAN': 'OLAM',    # Outspan appartient à OLAM
        
        'SUCRES': 'SUCDEN',   # Sucres et Denrées = SUCDEN
        'DENREES': 'SUCDEN',
        'DENRÉES': 'SUCDEN',
        
        'ARCHER': 'ADM',      # Archer Daniels Midland
        'DANIELS': 'ADM',
        
        'WRIGLEY': 'MARS',    # Mars Wrigley
        'CADBURY': 'MONDELEZ' # Cadbury appartient à Mondelez
    }
    
    for full_name, files in entities_dict.items():
        # Extraire le nom principal
        core_name = extract_company_core_name(full_name)
        if not core_name:
            core_name = str(full_name).upper().strip()
        
        # Normaliser pour la comparaison
        normalized = core_name.replace('&', ' ').replace('-', ' ').replace('.', ' ')
        words = normalized.split()
        
        group_key = None
        
        # 1. Vérifier les mappings spéciaux d'abord
        for word in words[:3]:  # Regarder les 3 premiers mots
            if word in special_mappings:
                group_key = special_mappings[word]
                break
        
        # 2. Cas spéciaux composés (SUCRES ET DENREES, JB FOODS, etc.)
        if not group_key and len(words) >= 2:
            # Vérifier "SUCRES [ET/&] DENREES"
            if 'SUCRES' in words and any(d in words for d in ['DENREES', 'DENRÉES']):
                group_key = 'SUCDEN'
            # Vérifier "JB FOODS" ou "JB COCOA"
            elif words[0] == 'JB' and any(w in ['FOODS', 'COCOA'] for w in words[1:3]):
                group_key = 'JB COCOA'
            # Vérifier "B C" pour Barry Callebaut
            elif words[0] == 'B' and len(words) > 1 and words[1] == 'C':
                group_key = 'BARRY CALLEBAUT'
        
        # 3. Si pas de mapping spécial, utiliser le premier mot significatif
        if not group_key:
            for word in words:
                # Règle conservatrice: >4 lettres ou mots spéciaux acceptés
                if (len(word) > 4 or word in ['AGRI', 'ADM', 'JB']) and word not in ['THE', 'LES', 'DES', 'AND', 'LTD', 'LIMITED', 'INC', 'GMBH', 'SARL', 'S.A.', 'COMPANY', 'CORP', 'TRADING']:
                    # Vérifier si c'est déjà dans special_mappings
                    mapped = special_mappings.get(word, word)
                    group_key = mapped
                    break
        
        # 4. Si toujours pas de groupe, prendre les 2 premiers mots
        if not group_key:
            if len(words) >= 2:
                group_key = f"{words[0]} {words[1]}"
            elif words:
                group_key = words[0]
            else:
                group_key = core_name[:30]
        
        # Ajouter au groupe
        if group_key in groups:
            groups[group_key]['entities'].append({
                'full_name': full_name,
                'files': files
            })
            groups[group_key]['total_files'].extend(files)
            groups[group_key]['count'] += 1
        else:
            groups[group_key] = {
                'core_name': group_key,
                'entities': [{
                    'full_name': full_name,
                    'files': files
                }],
                'total_files': files.copy(),
                'count': 1
            }
    
    # Fusion finale des groupes similaires
    # Par exemple, fusionner "CARGILL" et "CARGILL BV" si les deux existent
    merged_groups = {}
    processed = set()
    
    for key1, data1 in groups.items():
        if key1 in processed:
            continue
            
        # Chercher des groupes à fusionner
        keys_to_merge = [key1]
        for key2, data2 in groups.items():
            if key2 != key1 and key2 not in processed:
                # Fusionner si l'un contient l'autre
                if key1 in key2 or key2 in key1:
                    keys_to_merge.append(key2)
                    processed.add(key2)
        
        # Créer le groupe fusionné
        main_key = min(keys_to_merge, key=len)  # Prendre le nom le plus court
        merged_data = {
            'core_name': main_key,
            'entities': [],
            'total_files': [],
            'count': 0
        }
        
        for key in keys_to_merge:
            if key in groups:
                merged_data['entities'].extend(groups[key]['entities'])
                merged_data['total_files'].extend(groups[key]['total_files'])
                merged_data['count'] += groups[key]['count']
        
        merged_data['total_files'] = list(set(merged_data['total_files']))
        merged_groups[main_key] = merged_data
        processed.add(key1)
    
    # Garder la granularité des vraies compagnies pour l'analyse marché
    final_groups = {}
    other_group = {
        'core_name': 'OTHER',
        'entities': [],
        'total_files': [],
        'count': 0
    }
    
    # Regrouper les petits groupes (1-2 occurrences) dans OTHER
    for group_key, group_data in merged_groups.items():
        if group_data['count'] <= 2:
            other_group['entities'].extend(group_data['entities'])
            other_group['total_files'].extend(group_data['total_files'])
            other_group['count'] += group_data['count']
        else:
            final_groups[group_key] = group_data
    
    # Ajouter le groupe OTHER s'il contient des entités
    if other_group['count'] > 0:
        other_group['total_files'] = list(set(other_group['total_files']))
        final_groups['OTHER'] = other_group
    
    # Trier par nombre d'entités (les plus gros groupes en premier)
    sorted_groups = dict(sorted(final_groups.items(), key=lambda x: x[1]['count'], reverse=True))
    
    return sorted_groups

def group_exportateurs_by_company(entities_dict):
    """Regroupe les exportateurs en gardant la granularité par société"""
    groups = {}
    
    # Mappings spécialisés pour exportateurs (aliases connus)
    exportateur_mappings = {
        # Société Ivoirienne de Cacao
        'SIC': 'SIC',
        'SICC': 'SIC',
        
        # UniCacao
        'UNICACAO': 'UNICACAO', 
        'UNIC': 'UNICACAO',
        
        # Cargill variations
        'CARGILL': 'CARGILL',
        
        # Barry Callebaut variations  
        'BARRY': 'BARRY',
        'BC': 'BARRY',
        'CALLEBAUT': 'BARRY',
        
        # Touton variations
        'TOUTON': 'TOUTON',
        
        # Olam variations
        'OLAM': 'OLAM',
        
        # Cemoi variations
        'CEMOI': 'CEMOI'
    }
    
    for full_name, files in entities_dict.items():
        # Extraire le nom principal
        core_name = extract_company_core_name(full_name)
        if not core_name:
            core_name = str(full_name).upper().strip()
        
        # Normaliser
        normalized = core_name.replace('&', ' ').replace('-', ' ').replace('.', ' ')
        words = normalized.split()
        
        group_key = None
        
        # 1. Vérifier les mappings spécialisés d'abord
        for word in words[:3]:
            if word in exportateur_mappings:
                group_key = exportateur_mappings[word]
                break
        
        # 2. Si pas de mapping spécial, garder le nom complet de la société
        if not group_key:
            # Pour les exportateurs, on garde la granularité fine
            # Prendre les 2-3 premiers mots significatifs
            significant_words = []
            for word in words:
                if len(word) > 3 and word not in ['LTD', 'LIMITED', 'INC', 'GMBH', 'SARL', 'S.A.', 'COMPANY', 'CORP']:
                    significant_words.append(word)
                if len(significant_words) >= 2:  # Max 2 mots pour le nom de société
                    break
            
            if significant_words:
                group_key = ' '.join(significant_words[:2])
            else:
                group_key = words[0] if words else core_name[:20]
        
        # Ajouter au groupe
        if group_key in groups:
            groups[group_key]['entities'].append({
                'full_name': full_name,
                'files': files
            })
            groups[group_key]['total_files'].extend(files)
            groups[group_key]['count'] += 1
        else:
            groups[group_key] = {
                'core_name': group_key,
                'entities': [{
                    'full_name': full_name,
                    'files': files
                }],
                'total_files': files.copy(),
                'count': 1
            }
    
    # Nettoyer et trier
    for group_key in groups:
        groups[group_key]['total_files'] = list(set(groups[group_key]['total_files']))
    
    return dict(sorted(groups.items(), key=lambda x: x[1]['count'], reverse=True))

def group_similar_entities(entities_dict, entity_type='default'):
    """Interface générale qui utilise le bon algorithme selon le type"""
    
    if entity_type == 'destinataires':
        # Utiliser l'algorithme spécial pour destinataires
        return group_destinataires_intelligent(entities_dict)
    elif entity_type == 'exportateurs':
        # Utiliser l'algorithme spécial pour exportateurs (granularité par société)
        return group_exportateurs_by_company(entities_dict)
    else:
        # Pour destinations : pas de regroupement, la webapp de lecture reconnaît les codes pays
        return {}

def save_learned_mapping(full_name, simple_name, entity_type='destinataire'):
    """Sauvegarde un nouveau mapping appris dans Entity_Mappings.xlsx"""
    mappings_file = MASTER_DATA / "Entity_Mappings.xlsx"
    
    try:
        # Déterminer la feuille selon le type
        if entity_type == 'destinataire':
            sheet_name = 'Destinataires'
            column_full = 'DESTINATAIRE'
            column_simple = 'DESTINATAIRE SIMPLE'
        elif entity_type == 'exportateur':
            sheet_name = 'Exportateurs'
            column_full = 'EXPORTATEUR'
            column_simple = 'EXPORTATEUR SIMPLE'
        elif entity_type == 'destination':
            sheet_name = 'Destinations'
            column_full = 'DESTINATION'
            column_simple = 'DESTINATION SIMPLE'
        else:
            st.error(f"Type d'entité non reconnu: {entity_type}")
            return False
        
        # Lire la feuille existante
        df = pd.read_excel(mappings_file, sheet_name=sheet_name)
        
        # Vérifier si le mapping existe déjà
        existing = df[df[column_full].str.strip() == full_name.strip()]
        if len(existing) > 0:
            st.info(f"Mapping déjà existant: {full_name} → {simple_name}")
            return False
        
        # Ajouter la nouvelle ligne
        new_row = {column_full: full_name, column_simple: simple_name}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Lire les autres feuilles pour préservation
        other_sheets = {}
        for sheet in ['Exportateurs', 'Destinataires', 'Destinations']:
            if sheet != sheet_name:
                other_sheets[sheet] = pd.read_excel(mappings_file, sheet_name=sheet)
        
        # Sauvegarder toutes les feuilles
        with pd.ExcelWriter(mappings_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            for sheet, data in other_sheets.items():
                data.to_excel(writer, sheet_name=sheet, index=False)
        
        st.success(f"Apprentissage sauvegardé: {full_name} → {simple_name}")
        return True
        
    except Exception as e:
        st.error(f"Erreur sauvegarde apprentissage: {e}")
        return False

def batch_save_learned_mappings(mappings_dict, entity_type='destinataire'):
    """Sauvegarde plusieurs mappings appris en une fois"""
    mappings_file = MASTER_DATA / "Entity_Mappings.xlsx"
    
    if not mappings_dict:
        return False
    
    try:
        # Déterminer la feuille selon le type
        if entity_type == 'destinataire':
            sheet_name = 'Destinataires'
            column_full = 'DESTINATAIRE'
            column_simple = 'DESTINATAIRE SIMPLE'
        elif entity_type == 'exportateur':
            sheet_name = 'Exportateurs'
            column_full = 'EXPORTATEUR'
            column_simple = 'EXPORTATEUR SIMPLE'
        elif entity_type == 'destination':
            sheet_name = 'Destinations'
            column_full = 'DESTINATION'
            column_simple = 'DESTINATION SIMPLE'
        else:
            st.error(f"Type d'entité non supporté: {entity_type}")
            return False
        
        # Lire la feuille existante
        df = pd.read_excel(mappings_file, sheet_name=sheet_name)
        
        # Préparer les nouvelles lignes
        new_rows = []
        for full_name, simple_name in mappings_dict.items():
            # Vérifier si le mapping existe déjà (avec normalisation)
            full_name_normalized = normalize_for_exact_match(full_name)
            
            # Chercher correspondance normalisée
            found = False
            for _, row in df.iterrows():
                if pd.notna(row[column_full]):
                    existing_normalized = normalize_for_exact_match(str(row[column_full]))
                    if existing_normalized == full_name_normalized:
                        found = True
                        break
            
            if not found:  # Seulement si pas déjà existant
                new_rows.append({column_full: full_name, column_simple: simple_name})
        
        if not new_rows:
            st.info("Tous les mappings existent déjà")
            return False
        
        # Ajouter toutes les nouvelles lignes
        new_df = pd.DataFrame(new_rows)
        df = pd.concat([df, new_df], ignore_index=True)
        
        # Lire les autres feuilles pour préservation
        other_sheets = {}
        for sheet in ['Exportateurs', 'Destinataires', 'Destinations']:
            if sheet != sheet_name:
                other_sheets[sheet] = pd.read_excel(mappings_file, sheet_name=sheet)
        
        # Sauvegarder toutes les feuilles
        with pd.ExcelWriter(mappings_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            for sheet, data in other_sheets.items():
                data.to_excel(writer, sheet_name=sheet, index=False)
        
        st.success(f"{len(new_rows)} nouveaux apprentissages sauvegardés!")
        return True
        
    except Exception as e:
        st.error(f"Erreur sauvegarde batch: {e}")
        return False

def find_similar_entity(new_name, master_entities, threshold=0.6):
    """Trouve des entités similaires dans le master avec fuzzy matching"""
    new_core = extract_company_core_name(new_name)
    
    best_match = None
    best_score = 0.0
    
    for entity in master_entities:
        entity_core = extract_company_core_name(entity)
        
        if not new_core or not entity_core:
            continue
            
        # Calcul de similarité entre noms principaux
        from difflib import SequenceMatcher
        score = SequenceMatcher(None, new_core, entity_core).ratio()
        
        # Bonus si correspondance de mots-clés
        new_words = set(new_core.split())
        entity_words = set(entity_core.split())
        common_words = new_words & entity_words
        
        if common_words and len(common_words) > 0:
            word_bonus = len(common_words) / max(len(new_words), len(entity_words))
            score = (score + word_bonus) / 2
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = entity
    
    return best_match, best_score

@st.cache_data(ttl=3600)  # Cache pour 1 heure
def load_master_entities_with_mapping():
    """Charge et indexe les entités avec cache pour performance optimale"""
    mappings_file = MASTER_DATA / "Entity_Mappings.xlsx"
    
    entities = {
        "exportateurs": set(),
        "destinataires": set(), 
        "destinations": set()
    }
    
    # Mappings avec index pour recherche O(1)
    exportateur_mapping = {}
    destinataire_mapping = {}
    destination_mapping = {}
    
    # Index inversés pour recherche ultra-rapide
    exportateur_normalized_index = {}  # normalized -> simple
    exportateur_core_index = {}  # core_name -> simple
    destinataire_normalized_index = {}
    destinataire_core_index = {}
    
    try:
        # Charger exportateurs (252 lignes - rapide)
        exp_df = pd.read_excel(mappings_file, sheet_name='Exportateurs')
        if 'EXPORTATEUR SIMPLE' in exp_df.columns:
            entities['exportateurs'].update(exp_df['EXPORTATEUR SIMPLE'].dropna().unique())
        
        # Indexer exportateurs
        if 'EXPORTATEUR' in exp_df.columns and 'EXPORTATEUR SIMPLE' in exp_df.columns:
            for _, row in exp_df.iterrows():
                if pd.notna(row.get('EXPORTATEUR')) and pd.notna(row.get('EXPORTATEUR SIMPLE')):
                    full_name = str(row['EXPORTATEUR']).strip()
                    simple_name = str(row['EXPORTATEUR SIMPLE']).strip()
                    exportateur_mapping[full_name] = simple_name
                    
                    # Index normalisé
                    normalized = normalize_for_exact_match(full_name)
                    exportateur_normalized_index[normalized] = simple_name
                    
                    # Index par nom principal
                    core = extract_company_core_name(full_name)
                    if core:
                        exportateur_core_index[core] = simple_name
        
        # Charger destinataires (20K lignes - optimisé avec vectorisation)
        dest_df = pd.read_excel(mappings_file, sheet_name='Destinataires')
        if 'DESTINATAIRE SIMPLE' in dest_df.columns:
            entities['destinataires'].update(dest_df['DESTINATAIRE SIMPLE'].dropna().unique())
        
        # Indexer destinataires - OPTIMISÉ
        if 'DESTINATAIRE' in dest_df.columns and 'DESTINATAIRE SIMPLE' in dest_df.columns:
            # Vectorisation pour éviter les boucles
            valid_rows = dest_df[['DESTINATAIRE', 'DESTINATAIRE SIMPLE']].dropna()
            
            # Créer les mappings en batch
            for _, row in valid_rows.iterrows():
                full_name = str(row['DESTINATAIRE']).strip()
                simple_name = str(row['DESTINATAIRE SIMPLE']).strip()
                destinataire_mapping[full_name] = simple_name
                
                # Index normalisé
                normalized = normalize_for_exact_match(full_name)
                destinataire_normalized_index[normalized] = simple_name
                
                # Index par nom principal (limité aux 5000 premiers pour performance)
                if len(destinataire_core_index) < 5000:
                    core = extract_company_core_name(full_name)
                    if core:
                        destinataire_core_index[core] = simple_name
        
        # Charger destinations (76 lignes - instantané)
        dest_pays_df = pd.read_excel(mappings_file, sheet_name='Destinations')
        if 'DESTINATION SIMPLE' in dest_pays_df.columns:
            entities['destinations'].update(dest_pays_df['DESTINATION SIMPLE'].dropna().unique())
        
        # Index destinations
        if 'DESTINATION' in dest_pays_df.columns and 'DESTINATION SIMPLE' in dest_pays_df.columns:
            for _, row in dest_pays_df.iterrows():
                if pd.notna(row.get('DESTINATION')) and pd.notna(row.get('DESTINATION SIMPLE')):
                    code = str(row['DESTINATION']).strip()
                    name = str(row['DESTINATION SIMPLE']).strip()
                    destination_mapping[code] = name
        
        # Retourner avec les index pour recherche rapide
        return {
            'entities': entities,
            'mappings': {
                'exportateur': exportateur_mapping,
                'destinataire': destinataire_mapping,
                'destination': destination_mapping
            },
            'indexes': {
                'exp_normalized': exportateur_normalized_index,
                'exp_core': exportateur_core_index,
                'dest_normalized': destinataire_normalized_index,
                'dest_core': destinataire_core_index
            }
        }
        
    except Exception as e:
        st.error(f"Erreur chargement Entity_Mappings.xlsx: {e}")
        # Fallback
        return {
            'entities': entities,
            'mappings': {'exportateur': {}, 'destinataire': {}, 'destination': {}},
            'indexes': {'exp_normalized': {}, 'exp_core': {}, 'dest_normalized': {}, 'dest_core': {}}
        }

def load_master_entities_fallback():
    """Fallback vers l'ancien système si Entity_Mappings.xlsx échoue"""
    master_file = MASTER_DATA / "DB_Shipping_Master.xlsx"
    entities = {"exportateurs": set(), "destinataires": set(), "destinations": set()}
    
    try:
        for sheet in ['DB ABJ', 'DB SP']:
            df = pd.read_excel(master_file, sheet_name=sheet, engine='openpyxl', nrows=1000)
            if 'EXPORTATEUR SIMPLE' in df.columns:
                entities['exportateurs'].update(df['EXPORTATEUR SIMPLE'].dropna().unique())
            if 'DESTINATAIRE SIMPLE' in df.columns:
                entities['destinataires'].update(df['DESTINATAIRE SIMPLE'].dropna().unique())
            if 'DESTINATION' in df.columns:
                entities['destinations'].update(df['DESTINATION'].dropna().unique())
    except Exception as e:
        st.error(f"Erreur fallback: {e}")
    
    return entities, {}, {}, {}

def load_master_entities():
    """Version simplifiée pour compatibilité"""
    master_data = load_master_entities_with_mapping()
    return master_data['entities']

def analyze_monthly_files(year="2025"):
    """Analyse les fichiers mensuels avec matching intelligent"""
    
    # Ignorer les fichiers temporaires Excel (commencent par ~$)
    all_files = list(UPDATES_DIR.glob(f"{year}/*.xlsx"))
    files = [f for f in all_files if not f.name.startswith('~$')]
    
    
    new_entities = {
        "exportateurs": {},
        "destinataires": {},
        "destinations": {}
    }
    
    # Nouvelles structures avec suggestions
    suggested_mappings = {
        "exportateurs": {},
        "destinataires": {},
        "destinations": {}
    }
    
    volume_stats = []
    
    # Charger avec cache et index optimisés
    st.write(f"PREUVE : Chargement de Entity_Mappings.xlsx...")
    with st.spinner("Chargement optimisé des mappings..."):
        master_data = load_master_entities_with_mapping()
        master_entities = master_data['entities']
        mappings = master_data['mappings']
        st.write(f"PREUVE : {len(master_entities['exportateurs'])} exportateurs existants dans Entity_Mappings")
        st.write(f"PREUVE : {len(master_entities['destinataires'])} destinataires existants dans Entity_Mappings")
        indexes = master_data['indexes']
    
    st.success(f"Mappings indexés et prêts")
    
    progress_bar = st.progress(0)
    
    for idx, filepath in enumerate(files):
        progress_bar.progress((idx + 1) / len(files), f"Analyse de {filepath.name}...")
        
        try:
            df = pd.read_excel(filepath)
            
            # Identifier les colonnes selon la structure
            
            # Exportateurs - gestion des différentes structures
            exportateur_col = None
            if 'OPERATEUR' in df.columns:  # Structure juillet 2025
                exportateur_col = 'OPERATEUR'
            elif 'EXPORTATEUR' in df.columns:  # Structure 2024-2025
                exportateur_col = 'EXPORTATEUR'
            elif 'NOM_EXPORTATEUR' in df.columns:  # Structure 2023
                exportateur_col = 'NOM_EXPORTATEUR'
            
            if exportateur_col:
                exportateurs = set(df[exportateur_col].dropna().unique())
                for exp in exportateurs:
                    exp_str = str(exp).strip()
                    exp_normalized = normalize_for_exact_match(exp_str)
                    
                    # 1. Recherche O(1) dans l'index normalisé
                    if exp_normalized in indexes['exp_normalized']:
                        continue  # Déjà connu via index
                    
                    # 2. Recherche O(1) dans les entités simples
                    if exp_str in master_entities['exportateurs']:
                        continue  # Déjà connu
                    
                    # 3. Recherche O(1) dans l'index par nom principal
                    exp_core = extract_company_core_name(exp_str)
                    if exp_core and exp_core in indexes['exp_core']:
                        suggested_mappings['exportateurs'][exp] = {
                            'suggestion': indexes['exp_core'][exp_core],
                            'score': 1.0,
                            'files': [filepath.name],
                            'reason': 'core_match'
                        }
                        continue
                    
                    # 4. Vraiment nouveau
                    if exp not in new_entities['exportateurs']:
                        new_entities['exportateurs'][exp] = []
                    new_entities['exportateurs'][exp].append(filepath.name)
            
            # Destinataires - gestion des différentes structures
            destinataire_col = None
            if 'CLIENT_EXPORT' in df.columns:  # Structure juillet 2025
                destinataire_col = 'CLIENT_EXPORT'
            elif 'DESTINATAIRE' in df.columns:  # Structure 2024-2025
                destinataire_col = 'DESTINATAIRE'
            elif 'NOM_IMPORTATEUR' in df.columns:  # Structure 2023 (importateur = destinataire)
                destinataire_col = 'NOM_IMPORTATEUR'
            
            if destinataire_col:
                destinataires = set(df[destinataire_col].dropna().unique())
                for dest in destinataires:
                    dest_str = str(dest).strip()
                    dest_normalized = normalize_for_exact_match(dest_str)
                    
                    # 1. Recherche O(1) dans l'index normalisé
                    if dest_normalized in indexes['dest_normalized']:
                        continue  # Déjà connu
                    
                    # 2. Recherche O(1) dans les entités simples
                    if dest_str in master_entities['destinataires']:
                        continue  # Déjà connu
                    
                    # 3. Recherche O(1) dans l'index par nom principal (5000 premiers)
                    dest_core = extract_company_core_name(dest_str)
                    if dest_core and dest_core in indexes['dest_core']:
                        if dest not in suggested_mappings['destinataires']:
                            suggested_mappings['destinataires'][dest] = {
                                'suggestion': indexes['dest_core'][dest_core],
                                'score': 1.0,
                                'files': [],
                                'reason': 'core_match'
                            }
                        suggested_mappings['destinataires'][dest]['files'].append(filepath.name)
                        continue
                    
                    # 4. Vraiment nouveau
                    if dest not in new_entities['destinataires']:
                        new_entities['destinataires'][dest] = []
                    new_entities['destinataires'][dest].append(filepath.name)
            
            # Destinations - gestion des différentes structures
            destination_col = None
            if 'CODE_PAYS_DESTINATION' in df.columns:  # Structure juillet 2025
                destination_col = 'CODE_PAYS_DESTINATION'
            elif 'DESTINATION' in df.columns:  # Structure 2024-2025
                destination_col = 'DESTINATION'
            elif 'PAYS_DESTINATION' in df.columns:  # Structure 2023
                destination_col = 'PAYS_DESTINATION'
            
            if destination_col:
                destinations = set(df[destination_col].dropna().unique())
                for dest in destinations:
                    dest_str = str(dest).strip().upper()
                    
                    # 1. Recherche O(1) dans le mapping des codes pays
                    if dest_str in mappings['destination']:
                        continue  # Déjà connu
                    
                    # 2. Recherche O(1) dans les entités destinations
                    if dest_str in master_entities['destinations']:
                        continue  # Déjà connu
                    
                    # 3. Vraiment nouveau (pas de fuzzy pour codes pays)
                    if dest not in new_entities['destinations']:
                        new_entities['destinations'][dest] = []
                    new_entities['destinations'][dest].append(filepath.name)
            
            # Stats volumes - gestion des différentes structures
            poids_col = None
            if 'TOT_PDSNET' in df.columns:  # Structure juillet 2025
                poids_col = 'TOT_PDSNET'
            elif 'POIDS_NET' in df.columns:  # Structures précédentes
                poids_col = 'POIDS_NET'
            
            if poids_col:
                volume = df[poids_col].sum() / 1000  # en tonnes
                volume_stats.append({
                    'Fichier': filepath.name,
                    'Lignes': len(df),
                    'Volume (tonnes)': round(volume, 2)
                })
                
        except Exception as e:
            st.warning(f"Erreur avec {filepath.name}: {e}")
    
    progress_bar.empty()
    
    # Afficher résumé des suggestions automatiques
    total_suggestions = (len(suggested_mappings['exportateurs']) + 
                        len(suggested_mappings['destinataires']) + 
                        len(suggested_mappings['destinations']))
    
    if total_suggestions > 0:
        st.success(f"{total_suggestions} suggestions automatiques générées "
                  f"(évitant {total_suggestions} validations manuelles)")
    
    # Regrouper les entités restantes par similarité avec algorithmes spécialisés
    grouped_entities = {
        'exportateurs': group_similar_entities(new_entities['exportateurs'], entity_type='exportateurs'),
        'destinataires': group_similar_entities(new_entities['destinataires'], entity_type='destinataires'),
        'destinations': group_similar_entities(new_entities['destinations'], entity_type='destinations')
    }
    
    # Afficher résumé des regroupements
    total_groups = (len(grouped_entities['exportateurs']) + 
                   len(grouped_entities['destinataires']) + 
                   len(grouped_entities['destinations']))
    
    total_individual = (len(new_entities['exportateurs']) + 
                       len(new_entities['destinataires']) + 
                       len(new_entities['destinations']))
    
    if total_individual > 0:
        reduction = ((total_individual - total_groups) / total_individual * 100)
        st.info(f"Regroupement intelligent: {total_individual} entités → {total_groups} groupes "
                f"(réduction de {reduction:.0f}%)")
    
    return new_entities, volume_stats, suggested_mappings, grouped_entities

def get_available_files():
    """Détecte les nouveaux fichiers Excel non encore traités dans Updates_Mensuels"""
    available_files = []

    # Chemins
    updates_dir = Path("/Users/julienmarboeuf/Documents/BON PLEIN/WATCHAI/Updates_Mensuels")
    suivi_file = MASTER_DATA / "fichiers_traites.json"

    # Charger la liste des fichiers déjà traités
    fichiers_traites = set()
    try:
        with open(suivi_file, 'r', encoding='utf-8') as f:
            suivi_data = json.load(f)
            fichiers_traites = set(f['nom'] for f in suivi_data.get('fichiers_integres', []))
        print(f"Fichiers déjà traités: {len(fichiers_traites)}")
    except Exception as e:
        print(f"Impossible de lire le suivi: {e}")

    if not updates_dir.exists():
        print(f"Le dossier {updates_dir} n'existe pas!")
        return available_files

    # Regex pour valider le format "PORT - MOIS ANNÉE.xlsx"
    import re
    pattern = re.compile(r'^(ABJ|SPY) - (JAN|FEV|MAR|AVR|MAI|JUN|JUL|AOU|SEP|OCT|NOV|DEC) \d{4}\.xlsx$', re.IGNORECASE)

    # Chercher tous les fichiers .xlsx non traités
    for file_path in updates_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == '.xlsx' and not file_path.name.startswith('~$'):
            # Vérifier le format du nom de fichier
            if pattern.match(file_path.name):
                # Vérifier si pas encore traité
                if file_path.name not in fichiers_traites:
                    try:
                        available_files.append({
                            'path': file_path,
                            'name': file_path.name,
                            'location': 'Nouveaux fichiers',
                            'size_mb': file_path.stat().st_size / (1024*1024),
                            'modified': file_path.stat().st_mtime
                        })
                        print(f"Nouveau fichier détecté: {file_path.name}")
                    except Exception as e:
                        print(f"Erreur avec {file_path.name}: {e}")
                else:
                    print(f"Déjà traité: {file_path.name}")
            else:
                print(f"Format invalide (ignoré): {file_path.name}")

    print(f"{len(available_files)} nouveaux fichiers à traiter")
    return available_files

def analyze_selected_files(selected_files):
    """Analyse les fichiers sélectionnés avec matching intelligent"""
    if not selected_files:
        st.error("Aucun fichier sélectionné pour l'analyse")
        return {}, [], {}, {}

    # Conversion en liste de paths si nécessaire
    file_paths = []
    for f in selected_files:
        if isinstance(f, dict):
            file_paths.append(f['path'])
        else:
            file_paths.append(UPDATES_DIR / f)


    # Ignorer les fichiers temporaires Excel (commencent par ~$)
    files = [f for f in file_paths if not f.name.startswith('~$')]


    new_entities = {
        "exportateurs": {},
        "destinataires": {},
        "destinations": {}
    }

    # Nouvelles structures avec suggestions
    suggested_mappings = {
        "exportateurs": {},
        "destinataires": {},
        "destinations": {}
    }

    # Regroupement intelligent des entités
    grouped_entities = {}

    volume_stats = []

    # Charger avec cache et index optimisés
    st.write(f"PREUVE : Chargement de Entity_Mappings.xlsx...")
    with st.spinner("Chargement optimisé des mappings..."):
        master_data = load_master_entities_with_mapping()
        master_entities = master_data['entities']
        mappings = master_data['mappings']
        st.write(f"PREUVE : {len(master_entities['exportateurs'])} exportateurs existants dans Entity_Mappings")
        st.write(f"PREUVE : {len(master_entities['destinataires'])} destinataires existants dans Entity_Mappings")
        indexes = master_data['indexes']

    st.success(f"Mappings indexés et prêts")

    progress_bar = st.progress(0)

    for idx, filepath in enumerate(files):
        progress_bar.progress((idx + 1) / len(files), f"Analyse de {filepath.name}...")

        try:
            df = pd.read_excel(filepath)

            # Calcul volume pour ce fichier
            volume = 0
            if 'PDSNET' in df.columns:
                volume = df['PDSNET'].sum() / 1000  # en tonnes
            elif 'TOT_PDSNET' in df.columns:
                volume = df['TOT_PDSNET'].sum() / 1000
            elif 'POIDS_NET' in df.columns:
                volume = df['POIDS_NET'].sum() / 1000

            volume_stats.append({
                'Fichier': filepath.name,
                'Lignes': len(df),
                'Volume (tonnes)': round(volume, 2)
            })

            # Identifier les colonnes selon la structure

            # Exportateurs - gestion des différentes structures
            exportateur_col = None
            if 'OPERATEUR' in df.columns:  # Structure juillet 2025
                exportateur_col = 'OPERATEUR'
            elif 'EXPORTATEUR' in df.columns:  # Structure 2024-2025
                exportateur_col = 'EXPORTATEUR'
            elif 'NOM_EXPORTATEUR' in df.columns:  # Structure 2023
                exportateur_col = 'NOM_EXPORTATEUR'

            if exportateur_col:
                exportateurs = set(df[exportateur_col].dropna().unique())
                for exp in exportateurs:
                    exp_str = str(exp).strip()
                    exp_normalized = normalize_for_exact_match(exp_str)

                    # 1. Recherche O(1) dans l'index normalisé
                    if exp_normalized in indexes['exp_normalized']:
                        continue  # Déjà connu via index

                    # 2. Recherche O(1) dans les entités simples
                    if exp_str in master_entities['exportateurs']:
                        continue  # Déjà connu

                    # 3. Recherche O(1) dans l'index par nom principal
                    exp_core = extract_company_core_name(exp_str)
                    if exp_core and exp_core in indexes['exp_core']:
                        suggested_mappings['exportateurs'][exp] = {
                            'suggestion': indexes['exp_core'][exp_core],
                            'score': 0.95,
                            'reason': 'same_core_name'
                        }
                        continue

                    # C'est un nouvel exportateur
                    new_entities['exportateurs'][exp_str] = {'status': 'new', 'files': [filepath.name]}

            # Destinataires
            destinataire_col = None
            if 'ACHETEUR' in df.columns:  # Structure juillet 2025
                destinataire_col = 'ACHETEUR'
            elif 'DESTINATAIRE' in df.columns:  # Structure 2024-2025
                destinataire_col = 'DESTINATAIRE'
            elif 'NOM_DESTINATAIRE' in df.columns:  # Structure 2023
                destinataire_col = 'NOM_DESTINATAIRE'

            if destinataire_col:
                destinataires = set(df[destinataire_col].dropna().unique())
                for dest in destinataires:
                    dest_str = str(dest).strip()
                    dest_normalized = normalize_for_exact_match(dest_str)

                    # 1. Recherche O(1) dans l'index normalisé
                    if dest_normalized in indexes['dest_normalized']:
                        continue  # Déjà connu via index

                    # 2. Recherche O(1) dans les entités simples
                    if dest_str in master_entities['destinataires']:
                        continue  # Déjà connu

                    # 3. Recherche O(1) dans l'index par nom principal
                    dest_core = extract_company_core_name(dest_str)
                    if dest_core and dest_core in indexes['dest_core']:
                        suggested_mappings['destinataires'][dest] = {
                            'suggestion': indexes['dest_core'][dest_core],
                            'score': 0.95,
                            'reason': 'same_core_name'
                        }
                        continue

                    # C'est un nouveau destinataire
                    new_entities['destinataires'][dest_str] = {'status': 'new', 'files': [filepath.name]}

            # Destinations
            destination_col = None
            if 'PAYS_DESTINATION' in df.columns:  # Structure juillet 2025
                destination_col = 'PAYS_DESTINATION'
            elif 'DESTINATION' in df.columns:  # Structure 2024-2025
                destination_col = 'DESTINATION'
            elif 'CODE_PAYS' in df.columns:  # Structure 2023
                destination_col = 'CODE_PAYS'

            if destination_col:
                destinations = set(df[destination_col].dropna().unique())
                for dest in destinations:
                    dest_str = str(dest).strip()
                    if dest_str not in master_entities['destinations']:
                        new_entities['destinations'][dest_str] = {'status': 'new', 'files': [filepath.name]}

        except Exception as e:
            st.error(f"Erreur lors du traitement de {filepath.name}: {e}")
            continue

    # Regroupement intelligent pour exportateurs
    if new_entities['exportateurs']:
        # Convertir le format pour être compatible avec group_similar_entities
        entities_dict = {}
        for exp, info in new_entities['exportateurs'].items():
            entities_dict[exp] = info['files']
        try:
            grouped_entities['exportateurs'] = group_similar_entities(entities_dict, 'exportateurs')
        except Exception as e:
            st.warning(f"Regroupement exportateurs échoué: {e}")
            grouped_entities['exportateurs'] = {}

    # Regroupement intelligent pour destinataires
    if new_entities['destinataires']:
        # Convertir le format pour être compatible avec group_similar_entities
        entities_dict = {}
        for dest, info in new_entities['destinataires'].items():
            entities_dict[dest] = info['files']
        try:
            grouped_entities['destinataires'] = group_similar_entities(entities_dict, 'destinataires')
        except Exception as e:
            st.warning(f"Regroupement destinataires échoué: {e}")
            grouped_entities['destinataires'] = {}

    # Regroupement intelligent pour destinations (moins critique)
    if new_entities['destinations']:
        entities_dict = {}
        for dest, info in new_entities['destinations'].items():
            entities_dict[dest] = info['files']
        try:
            grouped_entities['destinations'] = group_similar_entities(entities_dict, 'destinations')
        except Exception as e:
            st.warning(f"Regroupement destinations échoué: {e}")
            grouped_entities['destinations'] = {}

    return new_entities, volume_stats, suggested_mappings, grouped_entities

def main():
    volume_stats = []
    for file_info in selected_files:
        file_path = file_info['path']
        try:
            df = pd.read_excel(file_path)
            # Identifier la colonne de poids
            poids_col = None
            if 'TOT_PDSNET' in df.columns:
                poids_col = 'TOT_PDSNET'
            elif 'POIDS_NET' in df.columns:
                poids_col = 'POIDS_NET'

            if poids_col:
                volume = df[poids_col].sum() / 1000  # en tonnes
                volume_stats.append({
                    'Fichier': file_info['name'],
                    'Lignes': len(df),
                    'Volume (tonnes)': round(volume, 2)
                })
        except:
            pass  # Déjà traité au-dessus

    # Groupement intelligent (utilise la logique existante)
    grouped_entities = {}
    if new_entities['exportateurs']:
        grouped_entities['exportateurs'] = group_similar_entities(
            {exp: [] for exp in new_entities['exportateurs']}, 'exportateurs'
        )
    if new_entities['destinataires']:
        grouped_entities['destinataires'] = group_similar_entities(
            {dest: [] for dest in new_entities['destinataires']}, 'destinataires'
        )
    if new_entities['destinations']:
        grouped_entities['destinations'] = group_similar_entities(
            {dest: [] for dest in new_entities['destinations']}, 'destinations'
        )

    return new_entities, volume_stats, suggested_mappings, grouped_entities

def main():
    # CSS personnalisé pour les couleurs WATCHAI
    st.markdown("""
    <style>
        /* Variables de couleurs WATCHAI */
        :root {
            --watchai-teal: #4DBDB3;
            --watchai-dark-gray: #3D4547;
            --watchai-light-gray: #F5F5F5;
        }

        /* Styles généraux */
        .main {
            background-color: var(--watchai-light-gray);
        }

        /* Sidebar */
        .css-1d391kg {
            background-color: white;
            border-right: 2px solid var(--watchai-teal);
        }

        /* Header personnalisé */
        .watchai-header {
            background: linear-gradient(135deg, var(--watchai-teal) 0%, var(--watchai-dark-gray) 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .watchai-title {
            color: white;
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0;
            text-align: center;
        }

        .watchai-subtitle {
            color: #E0F2F1;
            font-size: 1.2rem;
            text-align: center;
            margin: 0.5rem 0 0 0;
        }

        /* Boutons */
        .stButton > button {
            background-color: var(--watchai-teal);
            color: white;
            border: none;
            border-radius: 5px;
            font-weight: bold;
        }

        .stButton > button:hover {
            background-color: var(--watchai-dark-gray);
        }

        /* Métriques */
        [data-testid="metric-container"] {
            background-color: white;
            border: 1px solid var(--watchai-teal);
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Expandeurs */
        .streamlit-expanderHeader {
            background-color: var(--watchai-teal);
            color: white;
        }

        /* Tableaux */
        .stDataFrame {
            border: 1px solid var(--watchai-teal);
            border-radius: 5px;
        }

        /* Alertes */
        .stSuccess {
            background-color: #E8F5E8;
            border-left: 5px solid var(--watchai-teal);
        }

        .stInfo {
            background-color: #E3F2FD;
            border-left: 5px solid var(--watchai-dark-gray);
        }

        .stWarning {
            background-color: #FFF3E0;
            border-left: 5px solid #FF9800;
        }

        .stError {
            background-color: #FFEBEE;
            border-left: 5px solid #F44336;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header avec logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("/Users/julienmarboeuf/Documents/BON PLEIN/WATCHAI/Images/WatchAI logo2.png", width=300)
        except:
            st.markdown("<h1 style='text-align: center; color: #4DBDB3;'>WatchAI</h1>", unsafe_allow_html=True)

    st.markdown("""
    <div class="watchai-header">
        <h1 class="watchai-title">Validation des Nouvelles Entités</h1>
        <p class="watchai-subtitle">Export Cacao - Government Logistics Intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("Configuration")

    # Nouvelle section de sélection des fichiers
    available_files = get_available_files()

    # Afficher aussi dans la zone principale

    if not available_files:
        st.sidebar.warning("Aucun fichier Excel trouvé dans Updates_Mensuels/")
        st.sidebar.info("Placez les nouveaux fichiers dans le dossier racine Updates_Mensuels/")
        selected_files = []
    else:
        st.sidebar.subheader("Sélection des fichiers")

        # Séparer les nouveaux fichiers des archives
        new_files = [f for f in available_files if f['location'] == 'Nouveaux fichiers']
        archive_files = [f for f in available_files if f['location'] != 'Nouveaux fichiers']

        selected_files = []

        # Section nouveaux fichiers (priorité)
        if new_files:
            st.sidebar.markdown("**Nouveaux fichiers à traiter:**")
            for file_info in new_files:
                is_selected = st.sidebar.checkbox(
                    f"{file_info['name']} ({file_info['size_mb']:.1f} MB)",
                    value=True,  # Sélectionné par défaut
                    key=f"new_{file_info['name']}"
                )
                if is_selected:
                    selected_files.append(file_info)

            st.sidebar.markdown("---")

        # Section archives (optionnelle)
        if archive_files:
            with st.sidebar.expander("Fichiers archivés (optionnel)"):
                for location in ['Archives 2025', 'Archives 2024', 'Archives 2023']:
                    location_files = [f for f in archive_files if f['location'] == location]
                    if location_files:
                        st.markdown(f"**{location}:**")
                        for file_info in location_files:
                            is_selected = st.checkbox(
                                f"{file_info['name']} ({file_info['size_mb']:.1f} MB)",
                                value=False,
                                key=f"archive_{file_info['name']}"
                            )
                            if is_selected:
                                selected_files.append(file_info)

        # Affichage du résumé de sélection
        if selected_files:
            st.sidebar.success(f"{len(selected_files)} fichier(s) sélectionné(s)")
            total_size = sum(f['size_mb'] for f in selected_files)
            st.sidebar.info(f"Taille totale: {total_size:.1f} MB")
        else:
            st.sidebar.warning("Aucun fichier sélectionné")

    # Section simplifiée pour les updates mensuels
    # (Section restaurer sauvegarde supprimée - pas nécessaire pour updates mensuels)


    # Bouton d'analyse avec fichiers sélectionnés
    if st.sidebar.button("Analyser les fichiers sélectionnés",
                        use_container_width=True,
                        disabled=not selected_files):
        st.session_state.analyzed = True
        st.session_state.selected_files = selected_files  # Sauvegarder la sélection
        result = analyze_selected_files(selected_files)
        st.session_state.new_entities = result[0]
        st.session_state.volume_stats = result[1]
        st.session_state.suggested_mappings = result[2] if len(result) > 2 else {}
        st.session_state.grouped_entities = result[3] if len(result) > 3 else {}
    
    # Charger les listes de référence pour les dropdowns
    mappings_file = MASTER_DATA / "Entity_Mappings.xlsx"
    try:
        exp_df = pd.read_excel(mappings_file, sheet_name='Exportateurs')
        dest_df = pd.read_excel(mappings_file, sheet_name='Destinataires')
        
        st.session_state.exportateur_simple_list = sorted(exp_df['EXPORTATEUR SIMPLE'].dropna().unique())
        st.session_state.destinataire_simple_list = sorted(dest_df['DESTINATAIRE SIMPLE'].dropna().unique())
    except Exception as e:
        st.error(f"Erreur chargement listes: {e}")
        st.session_state.exportateur_simple_list = []
        st.session_state.destinataire_simple_list = []
    

    # Contenu principal
    if 'analyzed' in st.session_state and st.session_state.analyzed:
        
        # Statistiques générales
        st.subheader("Statistiques des fichiers")
        if st.session_state.volume_stats and len(st.session_state.volume_stats) > 0:
            try:
                df_stats = pd.DataFrame(st.session_state.volume_stats)
            except ValueError:
                # En cas de données mal formatées, créer un DataFrame vide
                df_stats = pd.DataFrame(columns=['Fichier', 'Lignes', 'Volume (tonnes)'])
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Fichiers analysés", len(df_stats))
            with col2:
                st.metric("Total lignes", f"{df_stats['Lignes'].sum():,}")
            with col3:
                st.metric("Volume total", f"{df_stats['Volume (tonnes)'].sum():,.0f} tonnes")
            
            st.dataframe(df_stats, use_container_width=True)
        
        # Suggestions automatiques
        if 'suggested_mappings' in st.session_state and st.session_state.suggested_mappings:
            st.subheader("Suggestions Automatiques (Pré-validées)")
            
            suggestions = st.session_state.suggested_mappings
            total_auto = (len(suggestions.get('exportateurs', {})) + 
                         len(suggestions.get('destinataires', {})) + 
                         len(suggestions.get('destinations', {})))
            
            if total_auto > 0:
                with st.expander(f"Voir {total_auto} suggestions automatiques"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if suggestions.get('exportateurs'):
                            st.write("**Exportateurs:**")
                            for original, data in list(suggestions['exportateurs'].items())[:5]:
                                if isinstance(data, dict) and 'suggestion' in data and 'score' in data:
                                    st.write(f"`{original[:30]}...` → **{data['suggestion']}** ({data['score']:.2f})")
                                else:
                                    st.write(f"`{original[:30]}...` (format de suggestion non compatible)")
                    
                    with col2:
                        if suggestions.get('destinataires'):
                            st.write("**Destinataires:**")
                            for original, data in list(suggestions['destinataires'].items())[:5]:
                                if isinstance(data, dict) and 'suggestion' in data and 'score' in data:
                                    st.write(f"`{original[:30]}...` → **{data['suggestion']}** ({data['score']:.2f})")
                                else:
                                    st.write(f"`{original[:30]}...` (format de suggestion non compatible)")
                    
                    with col3:
                        if suggestions.get('destinations'):
                            st.write("**Destinations:**")
                            for original, data in suggestions['destinations'].items():
                                st.write(f"`{original}` → **{data['suggestion']}** ({data['score']:.2f})")

        # Validation par groupes intelligents
        if 'grouped_entities' in st.session_state and st.session_state.grouped_entities:
            st.subheader("Validation par Groupes Intelligents")
            
            tabs = st.tabs(["Exportateurs", "Destinataires", "Destinations"])
            
            # ONGLET EXPORTATEURS
            with tabs[0]:
                exp_groups = st.session_state.grouped_entities.get('exportateurs', {})
                exp_simple_list = st.session_state.get('exportateur_simple_list', [])
                
                if exp_groups:
                    st.warning(f"{len(exp_groups)} groupes d'exportateurs à valider")
                    
                    for idx, (group_name, group_data) in enumerate(exp_groups.items()):
                        with st.expander(f"Groupe: {group_name} ({group_data['count']} entités)"):
                            
                            # Afficher les entités du groupe
                            st.write("**Entités dans ce groupe:**")
                            for entity in group_data['entities']:
                                st.write(f"• {entity['full_name'][:100]}..." if len(entity['full_name']) > 100 else f"• {entity['full_name']}")
                            
                            st.write(f"**Fichiers:** {', '.join(group_data['total_files'])}")
                            
                            # Interface de validation
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                action = st.selectbox(
                                    "Action pour tout le groupe:",
                                    ["Accepter comme nouveau", "Mapper vers existant", "Ignorer"],
                                    key=f"exp_action_{idx}"
                                )
                            
                            with col2:
                                if action == "Mapper vers existant":
                                    if exp_simple_list:
                                        selected = st.selectbox(
                                            "Sélectionner l'exportateur simple:",
                                            [""] + exp_simple_list,
                                            key=f"exp_select_{idx}"
                                        )
                                        if selected:
                                            st.success(f"Tout le groupe → **{selected}**")
                                    else:
                                        manual_input = st.text_input(
                                            "Nom de l'exportateur simple:",
                                            key=f"exp_manual_{idx}"
                                        )
                                elif action == "Accepter comme nouveau":
                                    new_name = st.text_input(
                                        "Nom du nouvel exportateur simple:",
                                        value=group_name,
                                        key=f"exp_new_{idx}"
                                    )
                else:
                    st.success("Aucun groupe d'exportateurs à valider")
            
            # ONGLET DESTINATAIRES  
            with tabs[1]:
                dest_groups = st.session_state.grouped_entities.get('destinataires', {})
                dest_simple_list = st.session_state.get('destinataire_simple_list', [])
                
                if dest_groups:
                    st.warning(f"{len(dest_groups)} groupes de destinataires à valider")
                    
                    for idx, (group_name, group_data) in enumerate(dest_groups.items()):
                        with st.expander(f"Groupe: {group_name} ({group_data['count']} entités)"):
                            
                            # Afficher les entités du groupe
                            st.write("**Entités dans ce groupe:**")
                            for entity in group_data['entities'][:5]:  # Limiter à 5 pour l'affichage
                                st.write(f"• {entity['full_name'][:80]}..." if len(entity['full_name']) > 80 else f"• {entity['full_name']}")
                            if group_data['count'] > 5:
                                st.write(f"• ... et {group_data['count'] - 5} autres")
                            
                            st.write(f"**Fichiers:** {', '.join(group_data['total_files'])}")
                            
                            # Interface de validation
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                action = st.selectbox(
                                    "Action pour tout le groupe:",
                                    ["Créer nouveau destinataire", "Fusionner avec existant", "Ignorer"],
                                    key=f"dest_action_{idx}"
                                )
                            
                            with col2:
                                if action == "Fusionner avec existant":
                                    if dest_simple_list:
                                        # Proposer les plus probables en premier
                                        filtered_list = [d for d in dest_simple_list if any(word in d.upper() for word in group_name.split()[:2])]
                                        suggested_list = filtered_list[:10] if filtered_list else dest_simple_list[:20]
                                        
                                        selected = st.selectbox(
                                            "Sélectionner le destinataire existant:",
                                            [""] + suggested_list + ["--- Tous les destinataires ---"] + dest_simple_list,
                                            key=f"dest_select_{idx}"
                                        )
                                        if selected and selected != "--- Tous les destinataires ---":
                                            st.success(f"Tout le groupe → **{selected}**")
                                elif action == "Créer nouveau destinataire":
                                    new_name = st.text_input(
                                        "Nom du nouveau destinataire simple:",
                                        value=group_name,
                                        key=f"dest_new_{idx}"
                                    )
                else:
                    st.success("Aucun groupe de destinataires à valider")
            
            # ONGLET DESTINATIONS
            with tabs[2]:
                dest_pays_groups = st.session_state.grouped_entities.get('destinations', {})
                
                if dest_pays_groups:
                    st.warning(f"{len(dest_pays_groups)} groupes de destinations à valider")
                    
                    # Liste des pays courants pour suggestions
                    common_countries = [
                        "FRANCE", "ALLEMAGNE", "PAYS-BAS", "BELGIQUE", "ITALIE", "ESPAGNE", 
                        "ROYAUME-UNI", "ETATS-UNIS", "CANADA", "SUISSE", "CHINE", "JAPON"
                    ]
                    
                    for idx, (group_name, group_data) in enumerate(dest_pays_groups.items()):
                        with st.expander(f"Code: {group_name} ({group_data['count']} occurrences)"):
                            
                            # Afficher les codes du groupe
                            codes_in_group = [entity['full_name'] for entity in group_data['entities']]
                            st.write(f"**Codes pays:** {', '.join(str(code) for code in set(codes_in_group))}")
                            st.write(f"**Fichiers:** {', '.join(group_data['total_files'])}")
                            
                            # Interface de validation
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                action = st.selectbox(
                                    "Action:",
                                    ["Mapper vers pays", "Ignorer (code invalide)"],
                                    key=f"pays_action_{idx}"
                                )
                            
                            with col2:
                                if action == "Mapper vers pays":
                                    selected_country = st.selectbox(
                                        "Sélectionner le pays:",
                                        [""] + common_countries + ["--- Autre pays ---"],
                                        key=f"pays_select_{idx}"
                                    )
                                    if selected_country == "--- Autre pays ---":
                                        custom_country = st.text_input(
                                            "Nom du pays:",
                                            key=f"pays_custom_{idx}"
                                        )
                                    elif selected_country:
                                        st.success(f"{group_name} → **{selected_country}**")
                else:
                    st.success("Aucun regroupement de destinations - La webapp de lecture reconnaît les codes pays automatiquement")
        
        else:
            st.info("Cliquez sur 'Analyser les fichiers' pour commencer la validation.")
        
        # Boutons d'action
        st.markdown("---")
        
        # Boutons d'action simplifiés pour updates mensuels
        # (Bouton SAUVEGARDE RAPIDE supprimé - pas nécessaire pour updates mensuels)

        if False:  # Désactivé
            try:
                # Sauvegarder l'état complet de la session
                backup_data = {
                    'timestamp': datetime.now().isoformat(),
                    'session_state': {}
                }
                
                # Copier les données importantes de session_state
                important_keys = ['grouped_entities', 'analysis_done', 'new_entities', 'suggested_mappings', 'volume_stats']
                for key in important_keys:
                    if hasattr(st.session_state, key):
                        backup_data['session_state'][key] = getattr(st.session_state, key)
                
                # Sauvegarder aussi tous les widgets de validation
                for key in st.session_state.keys():
                    if any(prefix in key for prefix in ['exp_action_', 'exp_select_', 'exp_new_', 
                                                      'dest_action_', 'dest_select_', 'dest_new_',
                                                      'pays_action_', 'pays_select_', 'pays_custom_']):
                        backup_data['session_state'][key] = st.session_state[key]
                
                # Créer nom de fichier avec timestamp
                backup_file = VALIDATION_DIR / f"validation_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                import json as json_module
                import numpy as np
                
                def convert_types(obj):
                    """Convertit les types numpy pour JSON"""
                    if isinstance(obj, np.integer):
                        return int(obj)
                    elif isinstance(obj, np.floating):
                        return float(obj)
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    elif isinstance(obj, dict):
                        return {str(k): convert_types(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_types(item) for item in obj]
                    else:
                        return obj
                
                # Convertir les types avant sauvegarde
                backup_data_clean = convert_types(backup_data)
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json_module.dump(backup_data_clean, f, indent=2, ensure_ascii=False)
                
                st.success(f"Sauvegarde créée: {backup_file.name}")
                
            except Exception as e:
                st.error(f"Erreur sauvegarde: {e}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Mise à jour Entity_Mappings", type="primary", use_container_width=True):
                # Collecter tous les mappings validés pour apprentissage
                learned_mappings = {
                    'exportateurs': {},
                    'destinataires': {},
                    'destinations': {}
                }
                
                # Parcourir les validations exportateurs
                if hasattr(st.session_state, 'grouped_entities') and 'exportateurs' in st.session_state.grouped_entities:
                    exp_groups = st.session_state.grouped_entities['exportateurs']
                    for idx, (group_name, group_data) in enumerate(exp_groups.items()):
                        action_key = f"exp_action_{idx}"
                        select_key = f"exp_select_{idx}"
                        new_key = f"exp_new_{idx}"
                        
                        if action_key in st.session_state:
                            action = st.session_state[action_key]
                            if action == "Mapper vers existant" and select_key in st.session_state:
                                selected = st.session_state[select_key]
                                if selected:
                                    # Apprendre tous les mappings du groupe
                                    for entity in group_data['entities']:
                                        learned_mappings['exportateurs'][entity['full_name']] = selected
                            elif action == "Accepter comme nouveau" and new_key in st.session_state:
                                new_name = st.session_state[new_key]
                                if new_name:
                                    for entity in group_data['entities']:
                                        learned_mappings['exportateurs'][entity['full_name']] = new_name
                
                # Parcourir les validations destinataires
                if hasattr(st.session_state, 'grouped_entities') and 'destinataires' in st.session_state.grouped_entities:
                    dest_groups = st.session_state.grouped_entities['destinataires']
                    for idx, (group_name, group_data) in enumerate(dest_groups.items()):
                        action_key = f"dest_action_{idx}"
                        select_key = f"dest_select_{idx}"
                        new_key = f"dest_new_{idx}"
                        
                        if action_key in st.session_state:
                            action = st.session_state[action_key]
                            if action == "Fusionner avec existant" and select_key in st.session_state:
                                selected = st.session_state[select_key]
                                if selected and selected != "--- Tous les destinataires ---":
                                    # Apprendre tous les mappings du groupe
                                    for entity in group_data['entities']:
                                        learned_mappings['destinataires'][entity['full_name']] = selected
                            elif action == "Créer nouveau destinataire" and new_key in st.session_state:
                                new_name = st.session_state[new_key]
                                if new_name:
                                    for entity in group_data['entities']:
                                        learned_mappings['destinataires'][entity['full_name']] = new_name
                
                # Parcourir les validations destinations
                if hasattr(st.session_state, 'grouped_entities') and 'destinations' in st.session_state.grouped_entities:
                    dest_pays_groups = st.session_state.grouped_entities['destinations']
                    for idx, (group_name, group_data) in enumerate(dest_pays_groups.items()):
                        action_key = f"pays_action_{idx}"
                        select_key = f"pays_select_{idx}"
                        other_key = f"pays_other_{idx}"
                        
                        if action_key in st.session_state:
                            action = st.session_state[action_key]
                            if action == "Mapper vers pays" and select_key in st.session_state:
                                selected = st.session_state[select_key]
                                if selected and selected != "--- Autre pays ---":
                                    # Apprendre le mapping du code vers le pays
                                    for entity in group_data['entities']:
                                        learned_mappings['destinations'][entity['full_name']] = selected
                                elif selected == "--- Autre pays ---" and other_key in st.session_state:
                                    other_country = st.session_state[other_key]
                                    if other_country:
                                        for entity in group_data['entities']:
                                            learned_mappings['destinations'][entity['full_name']] = other_country
                
                # Sauvegarder les apprentissages dans Entity_Mappings.xlsx
                total_learned = 0
                if learned_mappings['exportateurs']:
                    success = batch_save_learned_mappings(learned_mappings['exportateurs'], 'exportateur')
                    if success:
                        total_learned += len(learned_mappings['exportateurs'])
                
                if learned_mappings['destinataires']:
                    success = batch_save_learned_mappings(learned_mappings['destinataires'], 'destinataire')
                    if success:
                        total_learned += len(learned_mappings['destinataires'])
                
                if learned_mappings['destinations']:
                    success = batch_save_learned_mappings(learned_mappings['destinations'], 'destination')
                    if success:
                        total_learned += len(learned_mappings['destinations'])
                
                # Sauvegarder aussi les décisions de validation (fichier JSON backup)
                # Extraire l'année des fichiers sélectionnés ou utiliser l'année courante
                file_year = datetime.now().year
                if 'selected_files' in st.session_state and st.session_state.selected_files:
                    # Essayer d'extraire l'année du nom des fichiers (ex: "ABJ - AOU 2025.xlsx")
                    for file_info in st.session_state.selected_files:
                        file_name = file_info['name']
                        import re
                        year_match = re.search(r'\b(20\d{2})\b', file_name)
                        if year_match:
                            file_year = int(year_match.group(1))
                            break

                validation_file = VALIDATION_DIR / f"validation_{file_year}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
                VALIDATION_DIR.mkdir(exist_ok=True)

                validation_data = {
                    'timestamp': datetime.now().isoformat(),
                    'year': file_year,
                    'learned_mappings': learned_mappings,
                    'session_state_keys': list(st.session_state.keys())
                }
                
                try:
                    import json as json_module
                    with open(validation_file, 'w', encoding='utf-8') as f:
                        json_module.dump(validation_data, f, indent=2, ensure_ascii=False)
                    
                    if total_learned > 0:
                        st.success(f"Apprentissage réussi: {total_learned} nouveaux mappings sauvegardés!")
                        st.success(f"Backup sauvegardé: {validation_file.name}")
                        st.info("Les prochaines analyses bénéficieront de cet apprentissage")
                    else:
                        st.info("Aucun nouveau mapping à apprendre (tout était déjà connu)")
                        
                except Exception as e:
                    st.error(f"Erreur sauvegarde backup: {e}")
                    st.success(f"Apprentissage principal réussi: {total_learned} mappings")
        
        with col2:
            if st.button("Intégrer les données", type="secondary", use_container_width=True):
                # Placeholder pour les messages de progression
                status_placeholder = st.empty()
                progress_bar = st.progress(0)
                
                try:
                    status_placeholder.info("Démarrage de l'intégration...")
                    progress_bar.progress(0.1)
                    
                    # Importer les fonctions d'intégration
                    from integrate_monthly_data import integrate_selected_files, load_entity_mappings, backup_master_database
                    
                    status_placeholder.info("Préparation des fichiers de validation...")
                    progress_bar.progress(0.2)
                    
                    # Chercher le fichier de validation le plus récent
                    validation_files = list(VALIDATION_DIR.glob("validation_*.json"))
                    latest_validation = max(validation_files, key=lambda f: f.stat().st_mtime) if validation_files else None
                    
                    # Créer une sauvegarde avant intégration
                    status_placeholder.info("Création d'une sauvegarde de sécurité...")
                    progress_bar.progress(0.3)
                    
                    backup_path = backup_master_database()
                    
                    if backup_path:
                        status_placeholder.success(f"Sauvegarde créée: {backup_path.name}")
                        progress_bar.progress(0.4)
                        
                        # Lancer l'intégration réelle
                        status_placeholder.info("Intégration des données dans DB_Shipping_Master.xlsx...")
                        progress_bar.progress(0.5)
                        
                        # Utiliser la fonction d'intégration pour fichiers sélectionnés
                        selected_file_paths = [file_info['path'] for file_info in st.session_state.selected_files]
                        stats = integrate_selected_files(
                            selected_file_paths=selected_file_paths,
                            validation_file=str(latest_validation) if latest_validation else None,
                            dry_run=False  # Intégration réelle
                        )
                        progress_bar.progress(1.0)
                        
                        if stats:
                            status_placeholder.success("Intégration terminée avec succès!")
                            
                            # Afficher statistiques
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Fichiers traités", f"{stats['files_processed']}")
                            with col_b:
                                st.metric("Lignes intégrées", f"{stats['total_lines']:,}")
                            with col_c:
                                st.metric("Volume (tonnes)", f"{stats['total_volume_kg']/1000:,.0f}")
                            
                            st.info("Les données sont maintenant disponibles dans la webapp d'analyse marché!")

                            # Archiver automatiquement les fichiers traités
                            status_placeholder.info("Archivage des fichiers traités...")
                            archived_files = []
                            for file_path in selected_file_paths:
                                try:
                                    # Extraire l'année du nom du fichier ou utiliser l'année courante
                                    import re
                                    year_match = re.search(r'(20\d{2})', file_path.name)
                                    file_year = year_match.group(1) if year_match else str(datetime.now().year)

                                    # Créer le dossier année s'il n'existe pas
                                    year_dir = UPDATES_DIR / file_year
                                    year_dir.mkdir(exist_ok=True)

                                    # Déplacer le fichier
                                    archive_path = year_dir / file_path.name
                                    if not archive_path.exists():
                                        file_path.rename(archive_path)
                                        archived_files.append(f"{file_path.name} → {file_year}/")

                                except Exception as e:
                                    st.warning(f"Impossible d'archiver {file_path.name}: {e}")

                            if archived_files:
                                with st.expander("Fichiers archivés"):
                                    for archived in archived_files:
                                        st.write(f"{archived}")

                            if stats.get('errors'):
                                with st.expander("Erreurs détectées"):
                                    for error in stats['errors']:
                                        st.write(f"- {error}")
                                st.error("Intégration terminée avec erreurs")
                            else:
                                st.success("Intégration réussie !")
                    else:
                        st.error("Impossible de créer la sauvegarde - intégration annulée")
                        
                except ImportError:
                        st.error("Module d'intégration non trouvé")
                        st.info("Vérifiez que integrate_monthly_data.py existe")
                        
                except Exception as e:
                        st.error(f"Erreur durant l'intégration: {e}")
                        st.info("L'apprentissage a déjà été sauvegardé, pas de perte de données")
                        st.info("La sauvegarde de DB_Shipping_Master.xlsx est disponible en cas de problème")
        
        with col3:
            # (Bouton Générer rapport supprimé - pas nécessaire pour updates mensuels)
            if False:  # Désactivé
                st.info("Génération du rapport...")
    
    else:
        # Instructions
        st.info("""
        ### Instructions

        1. **Sélectionnez l'année** à traiter dans la sidebar
        2. **Cliquez "Analyser"** pour identifier les nouvelles entités
        3. **Validez ou corrigez** les nouvelles entités détectées
        4. **Sauvegardez** vos décisions
        5. **Intégrez** les données dans la base master

        Les nouvelles entités peuvent être :
        - **Acceptées** : Ajoutées telles quelles
        - **Corrigées** : Remplacées par le nom correct
        - **Ignorées** : Non intégrées
        """)

if __name__ == "__main__":
    main()