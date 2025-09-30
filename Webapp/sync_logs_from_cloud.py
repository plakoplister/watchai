#!/usr/bin/env python3
"""
WATCHAI - Synchronisation des logs depuis Streamlit Cloud
Récupère les logs de connexion depuis l'application web
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import streamlit as st
from watchai_logger import watchai_logger
import time

# Configuration
STREAMLIT_APP_URL = "https://watchai.streamlit.app"  # Remplacer par l'URL réelle de votre app
LOCAL_LOG_FILE = Path("connection_logs_cloud.json")
SYNC_INTERVAL = 60  # Synchronisation toutes les 60 secondes

def fetch_cloud_logs():
    """
    Récupère les logs depuis l'application Streamlit Cloud
    Note: Cette fonction nécessite que l'app expose un endpoint API pour les logs
    """
    try:
        # Pour l'instant, on va lire le fichier local si disponible
        # Dans une vraie implémentation, il faudrait un endpoint API
        cloud_log_file = Path("connection_logs.json")

        if cloud_log_file.exists():
            with open(cloud_log_file, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Erreur lors de la récupération des logs cloud: {e}")
        return []

def sync_logs():
    """
    Synchronise les logs cloud avec le système local
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Synchronisation des logs...")

    # Récupérer les logs cloud
    cloud_logs = fetch_cloud_logs()

    if not cloud_logs:
        print("Aucun log cloud trouvé")
        return

    # Charger les logs locaux existants
    local_logs = []
    if LOCAL_LOG_FILE.exists():
        with open(LOCAL_LOG_FILE, 'r') as f:
            local_logs = json.load(f)

    # Identifier les nouveaux logs
    existing_timestamps = {log['timestamp'] for log in local_logs}
    new_logs = [log for log in cloud_logs if log['timestamp'] not in existing_timestamps]

    if new_logs:
        print(f"Trouvé {len(new_logs)} nouvelle(s) connexion(s)")

        # Traiter les nouvelles connexions de Jean
        for log in new_logs:
            if log.get('username') == 'Jean' and log.get('success'):
                print(f"🔔 JEAN S'EST CONNECTÉ: {log['timestamp']}")

                # Enregistrer dans le système de logs WATCHAI
                watchai_logger.log_activity(
                    "jean_connection",
                    f"Jean connecté depuis l'app web à {log['timestamp']}"
                )

        # Fusionner les logs
        local_logs.extend(new_logs)

        # Sauvegarder les logs mis à jour
        with open(LOCAL_LOG_FILE, 'w') as f:
            json.dump(local_logs, f, indent=2)

        print(f"Logs synchronisés: {len(new_logs)} nouvelle(s) entrée(s)")
    else:
        print("Aucune nouvelle connexion")

    return cloud_logs

def get_jean_connections():
    """
    Retourne toutes les connexions de Jean
    """
    if LOCAL_LOG_FILE.exists():
        with open(LOCAL_LOG_FILE, 'r') as f:
            logs = json.load(f)

        jean_logs = [
            log for log in logs
            if log.get('username') == 'Jean' and log.get('success')
        ]

        return jean_logs
    return []

def display_jean_activity():
    """
    Affiche l'activité de Jean dans Streamlit
    """
    st.title("📊 Activité de Jean sur WATCHAI Web")

    jean_logs = get_jean_connections()

    if jean_logs:
        st.success(f"Jean s'est connecté {len(jean_logs)} fois")

        # Afficher les dernières connexions
        st.subheader("Dernières connexions de Jean")
        for log in jean_logs[-5:][::-1]:  # 5 dernières, ordre inverse
            timestamp = datetime.fromisoformat(log['timestamp'])
            st.info(f"🔑 Connexion le {timestamp.strftime('%d/%m/%Y à %H:%M:%S')}")

        # Graphique d'activité
        if len(jean_logs) > 1:
            df = pd.DataFrame(jean_logs)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date

            daily_counts = df.groupby('date').size().reset_index(name='connexions')

            fig = px.bar(
                daily_counts,
                x='date',
                y='connexions',
                title="Connexions de Jean par jour",
                labels={'date': 'Date', 'connexions': 'Nombre de connexions'}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Jean ne s'est pas encore connecté sur l'application web")

def main():
    """
    Mode ligne de commande pour synchronisation continue
    """
    print("=== WATCHAI - Synchronisation des logs Cloud ===")
    print(f"Synchronisation toutes les {SYNC_INTERVAL} secondes")
    print("Appuyez sur Ctrl+C pour arrêter\n")

    try:
        while True:
            sync_logs()
            time.sleep(SYNC_INTERVAL)
    except KeyboardInterrupt:
        print("\n\nSynchronisation arrêtée.")

if __name__ == "__main__":
    # Si lancé directement, mode synchronisation continue
    if st._is_running_with_streamlit:
        # Mode Streamlit
        display_jean_activity()
    else:
        # Mode ligne de commande
        main()