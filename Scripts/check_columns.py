#!/usr/bin/env python3
"""Vérifier les colonnes des fichiers août 2025"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path("/Users/julienmarboeuf/Documents/BON PLEIN/WATCHAI")
UPDATES_DIR = BASE_DIR / "Updates_Mensuels"

# Fichiers à vérifier
files = [
    UPDATES_DIR / "ABJ - AOU 2025.xlsx",
    UPDATES_DIR / "SPY - AOU 2025.xlsx"
]

print("=== VÉRIFICATION COLONNES FICHIERS AOÛT 2025 ===")

for file_path in files:
    print(f"\n📄 {file_path.name}")
    print("-" * 50)

    if not file_path.exists():
        print("❌ Fichier n'existe pas")
        continue

    try:
        df = pd.read_excel(file_path)
        print(f"✅ Chargé: {len(df)} lignes")
        print(f"📋 Colonnes ({len(df.columns)}):")

        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")

        # Vérifier colonnes critiques
        critical_columns = ['DECLARATION_DATE', 'EXPORTATEUR', 'DESTINATAIRE', 'DESTINATION', 'PDSNET']
        print(f"\n🔍 Colonnes critiques:")
        for col in critical_columns:
            status = "✅" if col in df.columns else "❌"
            print(f"   {status} {col}")

    except Exception as e:
        print(f"❌ Erreur: {e}")

print("\n=== FIN VÉRIFICATION ===")