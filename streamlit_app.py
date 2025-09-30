"""
Point d'entrée pour Streamlit Cloud
Redirige vers Webapp/webapp_volumes_reels.py
"""
import sys
from pathlib import Path

# Ajouter le dossier Webapp au path
webapp_dir = Path(__file__).parent / "Webapp"
sys.path.insert(0, str(webapp_dir))

# Importer et exécuter l'application principale
import webapp_volumes_reels