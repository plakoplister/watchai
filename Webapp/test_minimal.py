"""
Test minimal pour vérifier Streamlit Cloud
"""
import streamlit as st

st.title("WATCHAI - Test Minimal")
st.success("Si vous voyez ce message, Streamlit fonctionne!")

st.write("Version de test pour diagnostiquer le problème")

# Test de login basique
username = st.text_input("Nom d'utilisateur")
password = st.text_input("Mot de passe", type="password")

if st.button("Tester"):
    st.info(f"Utilisateur saisi: {username}")