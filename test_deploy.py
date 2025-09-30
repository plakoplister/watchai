import streamlit as st
from pathlib import Path

st.title("Test de déploiement WATCHAI")

# Test 1: Vérifier le working directory
st.subheader("1. Working Directory")
st.code(str(Path.cwd()))

# Test 2: Lister les fichiers
st.subheader("2. Fichiers à la racine")
files = list(Path.cwd().glob("*"))
for f in files[:20]:
    st.text(f"- {f.name}")

# Test 3: Chercher Master_Data
st.subheader("3. Master_Data existe ?")
master_data = Path("Master_Data")
if master_data.exists():
    st.success(f"Master_Data trouvé !")
    db_file = master_data / "DB_Shipping_Master.xlsx"
    if db_file.exists():
        st.success(f"DB_Shipping_Master.xlsx trouvé ! Taille: {db_file.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        st.error("DB_Shipping_Master.xlsx non trouvé")
else:
    st.error("Master_Data non trouvé")

# Test 4: Chercher Webapp
st.subheader("4. Webapp existe ?")
webapp = Path("Webapp")
if webapp.exists():
    st.success("Webapp trouvé !")
else:
    st.error("Webapp non trouvé")