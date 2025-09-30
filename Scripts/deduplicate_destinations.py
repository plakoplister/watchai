#!/usr/bin/env python3
"""
Déduplique la feuille Destinations dans Entity_Mappings.xlsx
"""

import pandas as pd
from pathlib import Path

def deduplicate_destinations():
    """Déduplique les destinations pour avoir seulement les codes pays uniques"""
    
    file_path = Path("/Users/julienmarboeuf/Documents/MEREYA/AGL/EXPORT-Db/Master_Data/Entity_Mappings.xlsx")
    
    print("🧹 DÉDUPLICATION DES DESTINATIONS")
    print("="*50)
    
    try:
        # Lire la feuille Destinations
        print("📖 Lecture de la feuille Destinations...")
        df_dest = pd.read_excel(file_path, sheet_name='Destinations')
        print(f"   Lignes avant: {len(df_dest):,}")
        
        # Afficher quelques exemples
        print(f"\n📋 Exemples de données:")
        sample = df_dest.head(10)
        for _, row in sample.iterrows():
            code = str(row.get('DESTINATION', 'N/A'))
            name = str(row.get('DESTINATION SIMPLE', 'N/A'))
            print(f"   {code} → {name}")
        
        # Déduplicater par DESTINATION (garder la première occurrence de chaque code)
        print(f"\n🔄 Déduplication en cours...")
        df_dest_unique = df_dest.drop_duplicates(subset=['DESTINATION'], keep='first')
        print(f"   Lignes après: {len(df_dest_unique):,}")
        
        # Statistiques
        reduction = ((len(df_dest) - len(df_dest_unique)) / len(df_dest)) * 100
        print(f"   Réduction: {reduction:.1f}%")
        
        # Convertir les codes en string et trier
        df_dest_unique['DESTINATION'] = df_dest_unique['DESTINATION'].astype(str)
        df_dest_unique = df_dest_unique.sort_values('DESTINATION')
        
        # Afficher les codes pays uniques
        print(f"\n🌍 Codes pays uniques trouvés:")
        unique_codes = df_dest_unique['DESTINATION'].dropna().unique()
        valid_codes = [code for code in unique_codes if str(code).strip() and str(code) != 'nan']
        print(f"   Total codes valides: {len(valid_codes)}")
        print(f"   Exemples: {sorted(valid_codes)[:10]}")
        
        # Sauvegarder le fichier mis à jour
        print(f"\n💾 Sauvegarde du fichier...")
        
        # Lire les autres feuilles pour les préserver
        exportateurs = pd.read_excel(file_path, sheet_name='Exportateurs')
        destinataires = pd.read_excel(file_path, sheet_name='Destinataires')
        
        # Écrire toutes les feuilles
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            exportateurs.to_excel(writer, sheet_name='Exportateurs', index=False)
            destinataires.to_excel(writer, sheet_name='Destinataires', index=False)
            df_dest_unique.to_excel(writer, sheet_name='Destinations', index=False)
        
        print(f"✅ Fichier mis à jour: {file_path}")
        
        # Vérification finale
        print(f"\n📊 RÉSUMÉ:")
        print(f"   Exportateurs: {len(exportateurs):,} lignes")
        print(f"   Destinataires: {len(destinataires):,} lignes") 
        print(f"   Destinations: {len(df_dest_unique):,} lignes (était {len(df_dest):,})")
        
        # Afficher les 20 premiers pays
        print(f"\n🗺️ LISTE DES PAYS (20 premiers):")
        for _, row in df_dest_unique.head(20).iterrows():
            code = str(row.get('DESTINATION', 'N/A'))
            name = str(row.get('DESTINATION SIMPLE', 'N/A'))
            if code != 'nan' and name != 'nan':
                print(f"   {code:3s} → {name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = deduplicate_destinations()
    if success:
        print(f"\n🎉 DÉDUPLICATION RÉUSSIE!")
        print(f"   L'interface devrait maintenant être beaucoup plus rapide!")
    else:
        print(f"\n💥 ÉCHEC DE LA DÉDUPLICATION")