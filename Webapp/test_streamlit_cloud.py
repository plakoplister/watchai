"""
Script de diagnostic pour Streamlit Cloud
"""
import streamlit as st
import sys
from pathlib import Path

st.title("WATCHAI - Diagnostic Streamlit Cloud")

st.subheader("1. Version Python")
st.code(sys.version)

st.subheader("2. Répertoire de travail")
st.code(str(Path.cwd()))

st.subheader("3. Fichiers présents")
files = list(Path.cwd().glob("*"))
for f in files:
    st.text(f"- {f.name}")

st.subheader("4. Test des imports")
try:
    import pandas as pd
    st.success(f"pandas OK - version {pd.__version__}")
except Exception as e:
    st.error(f"pandas ERREUR: {e}")

try:
    import plotly
    st.success(f"plotly OK - version {plotly.__version__}")
except Exception as e:
    st.error(f"plotly ERREUR: {e}")

try:
    from watchai_logger import watchai_logger
    st.success("watchai_logger OK")
except Exception as e:
    st.error(f"watchai_logger ERREUR: {e}")

try:
    from auth_config import USERS
    st.success(f"auth_config OK - {len(USERS)} utilisateurs")
except Exception as e:
    st.error(f"auth_config ERREUR: {e}")

st.subheader("5. Test du fichier Excel")
db_file = Path("DB_Shipping_Master.xlsx")
if db_file.exists():
    st.success(f"DB_Shipping_Master.xlsx trouvé - Taille: {db_file.stat().st_size / 1024 / 1024:.2f} MB")
    try:
        import pandas as pd
        df = pd.read_excel(db_file, nrows=5)
        st.success(f"Lecture Excel OK - {len(df.columns)} colonnes")
    except Exception as e:
        st.error(f"Erreur lecture Excel: {e}")
else:
    st.error("DB_Shipping_Master.xlsx non trouvé")

st.subheader("6. Test du logo")
logo_file = Path("logo.png")
if logo_file.exists():
    st.success("logo.png trouvé")
    try:
        from PIL import Image
        img = Image.open(logo_file)
        st.image(img, width=200)
    except Exception as e:
        st.error(f"Erreur lecture logo: {e}")
else:
    st.error("logo.png non trouvé")