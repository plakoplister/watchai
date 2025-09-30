"""
WATCHAI - Interface d'Administration des Logs
Console pour visualiser les connexions et l'activité des utilisateurs
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from watchai_logger import watchai_logger
from auth_config import get_connection_stats

# Configuration de la page
st.set_page_config(
    page_title="WATCHAI - Console d'Administration",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS pour l'interface admin
st.markdown("""
<style>
    .admin-header {
        background: linear-gradient(135deg, #FF6B6B 0%, #4DBDB3 100%);
        color: white;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        text-align: center;
    }

    .log-entry {
        background: white;
        border-left: 4px solid #4DBDB3;
        border-radius: 4px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
        font-size: 12px;
    }

    .session-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="admin-header">
        <h1>WATCHAI - Console d'Administration</h1>
        <p>Surveillance des connexions et activité utilisateur</p>
    </div>
    """, unsafe_allow_html=True)

    # Tabs pour différentes vues
    tab1, tab2, tab3, tab4 = st.tabs(["Vue d'ensemble", "Sessions actives", "Logs détaillés", "Statistiques"])

    with tab1:
        show_overview()

    with tab2:
        show_active_sessions()

    with tab3:
        show_detailed_logs()

    with tab4:
        show_statistics()

def show_overview():
    """Vue d'ensemble des statistiques"""
    st.header("Vue d'ensemble du système")

    # Récupérer les statistiques de connexion des utilisateurs
    conn_stats = get_connection_stats()

    # Section des connexions utilisateurs
    st.subheader("Connexions des utilisateurs aujourd'hui")

    # Lire les logs de connexion
    log_file = Path("connection_logs.json")
    today_connections = []

    if log_file.exists():
        with open(log_file, 'r') as f:
            all_logs = json.load(f)

        # Filtrer les connexions d'aujourd'hui
        today = datetime.now().date()
        for log in all_logs:
            if log.get('success'):
                log_time = datetime.fromisoformat(log['timestamp'])
                if log_time.date() == today:
                    today_connections.append({
                        'username': log['username'],
                        'time': log_time.strftime('%H:%M:%S'),
                        'timestamp': log_time
                    })

    # Afficher les connexions d'aujourd'hui
    col1, col2, col3 = st.columns(3)

    with col1:
        julien_today = len([c for c in today_connections if c['username'] == 'Julien'])
        st.metric("Julien", f"{julien_today} connexion(s)")
        if julien_today > 0:
            last_julien = max([c['timestamp'] for c in today_connections if c['username'] == 'Julien'])
            st.caption(f"Dernière: {last_julien.strftime('%H:%M:%S')}")

    with col2:
        erick_today = len([c for c in today_connections if c['username'] == 'Erick'])
        st.metric("Erick", f"{erick_today} connexion(s)")
        if erick_today > 0:
            last_erick = max([c['timestamp'] for c in today_connections if c['username'] == 'Erick'])
            st.caption(f"Dernière: {last_erick.strftime('%H:%M:%S')}")

    with col3:
        jean_today = len([c for c in today_connections if c['username'] == 'Jean'])
        st.metric("Jean", f"{jean_today} connexion(s)")
        if jean_today > 0:
            last_jean = max([c['timestamp'] for c in today_connections if c['username'] == 'Jean'])
            st.caption(f"Dernière: {last_jean.strftime('%H:%M:%S')}")

    # Afficher les dernières connexions avec noms d'utilisateur
    if today_connections:
        st.subheader("Dernières connexions aujourd'hui")
        # Trier par timestamp décroissant
        today_connections.sort(key=lambda x: x['timestamp'], reverse=True)

        # Afficher les 10 dernières
        for conn in today_connections[:10]:
            st.success(f"**{conn['username']}** - {conn['time']}")
    else:
        st.info("Aucune connexion aujourd'hui")

    st.divider()

    # Statistiques générales du système
    st.subheader("Statistiques système")

    # Récupérer les statistiques
    stats = watchai_logger.get_session_stats()

    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Sessions totales", stats.get('total', 0))

    with col2:
        st.metric("Sessions aujourd'hui", stats.get('today', 0))

    with col3:
        st.metric("IPs uniques", stats.get('unique_ips', 0))

    with col4:
        last_access = stats.get('last_access', 'N/A')
        if last_access != 'N/A':
            try:
                dt = datetime.fromisoformat(last_access)
                last_access = dt.strftime("%H:%M:%S")
            except:
                pass
        st.metric("Dernier accès", last_access)

    # Sessions récentes
    st.subheader("Sessions récentes (10 dernières)")
    recent_sessions = watchai_logger.get_recent_sessions(10)

    if recent_sessions:
        df = pd.DataFrame(recent_sessions)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['time'] = df['timestamp'].dt.strftime('%H:%M:%S')
        df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')

        # Affichage sous forme de tableau stylé
        display_df = df[['time', 'session_id', 'client_ip', 'page', 'action', 'hostname']].copy()
        display_df.columns = ['Heure', 'Session ID', 'IP Client', 'Page', 'Action', 'Hostname']

        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("Aucune session enregistrée")

def show_active_sessions():
    """Affichage des sessions actives"""
    st.header("Sessions et connexions")

    # Sessions des dernières heures
    hours_filter = st.selectbox("Afficher les sessions des dernières:", [1, 6, 12, 24, 48], index=2)

    recent_sessions = watchai_logger.get_recent_sessions(1000)

    if recent_sessions:
        # Filtrer par heures
        cutoff_time = datetime.now() - timedelta(hours=hours_filter)
        filtered_sessions = []

        for session in recent_sessions:
            try:
                session_time = datetime.fromisoformat(session['timestamp'])
                if session_time >= cutoff_time:
                    filtered_sessions.append(session)
            except:
                continue

        if filtered_sessions:
            st.write(f"**{len(filtered_sessions)} sessions** trouvées dans les {hours_filter} dernières heures")

            # Groupement par IP
            ip_sessions = {}
            for session in filtered_sessions:
                ip = session.get('client_ip', 'unknown')
                if ip not in ip_sessions:
                    ip_sessions[ip] = []
                ip_sessions[ip].append(session)

            # Affichage par IP
            for ip, sessions in ip_sessions.items():
                with st.expander(f"IP: {ip} ({len(sessions)} sessions)"):
                    for session in sessions[-10:]:  # 10 dernières sessions par IP
                        timestamp = datetime.fromisoformat(session['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                        st.markdown(f"""
                        <div class="session-card">
                            <strong>{timestamp}</strong><br/>
                            Session: {session.get('session_id', 'N/A')}<br/>
                            Page: {session.get('page', 'N/A')}<br/>
                            Action: {session.get('action', 'N/A')}<br/>
                            Host: {session.get('hostname', 'N/A')}
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info(f"Aucune session dans les {hours_filter} dernières heures")
    else:
        st.info("Aucune session enregistrée")

def show_detailed_logs():
    """Affichage des logs détaillés"""
    st.header("Logs détaillés du système")

    # Sélection du type de log
    log_type = st.radio("Type de log:", ["Access Logs", "Activity Logs"])

    try:
        if log_type == "Access Logs":
            log_file = "/Users/julienmarboeuf/Documents/BON PLEIN/WATCHAI/Logs/access.log"
        else:
            log_file = "/Users/julienmarboeuf/Documents/BON PLEIN/WATCHAI/Logs/activity.log"

        if Path(log_file).exists():
            # Nombre de lignes à afficher
            num_lines = st.number_input("Nombre de lignes à afficher:", min_value=10, max_value=1000, value=50)

            # Lire les dernières lignes du fichier
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Afficher les dernières lignes
            recent_lines = lines[-num_lines:]

            st.subheader(f"Dernières {len(recent_lines)} entrées")

            for line in reversed(recent_lines):
                if line.strip():
                    st.markdown(f"""
                    <div class="log-entry">
                        {line.strip()}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning(f"Fichier de log non trouvé: {log_file}")

    except Exception as e:
        st.error(f"Erreur lors de la lecture des logs: {str(e)}")

def show_statistics():
    """Statistiques et graphiques"""
    st.header("Statistiques d'utilisation")

    recent_sessions = watchai_logger.get_recent_sessions(1000)

    if recent_sessions:
        df = pd.DataFrame(recent_sessions)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour

        # Graphique des connexions par jour
        st.subheader("Connexions par jour")
        daily_stats = df.groupby('date').size().reset_index(name='sessions')
        daily_stats['date'] = pd.to_datetime(daily_stats['date'])

        fig = px.line(daily_stats, x='date', y='sessions', title="Sessions par jour")
        fig.update_traces(line_color='#4DBDB3')
        st.plotly_chart(fig, use_container_width=True)

        # Graphique des connexions par heure
        st.subheader("Connexions par heure (24h)")
        hourly_stats = df.groupby('hour').size().reset_index(name='sessions')

        fig = px.bar(hourly_stats, x='hour', y='sessions', title="Sessions par heure")
        fig.update_traces(marker_color='#4DBDB3')
        st.plotly_chart(fig, use_container_width=True)

        # Top des pages visitées
        st.subheader("Pages les plus visitées")
        page_stats = df['page'].value_counts().head(10)

        fig = px.pie(values=page_stats.values, names=page_stats.index, title="Répartition des visites par page")
        st.plotly_chart(fig, use_container_width=True)

        # Top des IPs
        st.subheader("IPs les plus actives")
        ip_stats = df['client_ip'].value_counts().head(10)
        st.bar_chart(ip_stats)

    else:
        st.info("Pas assez de données pour générer des statistiques")

if __name__ == "__main__":
    main()