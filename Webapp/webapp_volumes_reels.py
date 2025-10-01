"""
WATCHAI - Government Logistics Intelligence
Application Streamlit pour l'analyse des exportations de cacao
Version déployable sur GitHub/Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from pathlib import Path
import hashlib
import json

# Import du système de logging WATCHAI
try:
    from watchai_logger import watchai_logger
    LOGGING_ENABLED = True
except ImportError:
    LOGGING_ENABLED = False

# Import du middleware de sécurité
try:
    from security_middleware import security_middleware
    SECURITY_ENABLED = True
except ImportError:
    SECURITY_ENABLED = False
    st.warning("⚠️ Module de sécurité non disponible")

# Import du système de watermarking
try:
    from data_watermarking import watermarking, get_watermarked_data
    WATERMARKING_ENABLED = True
except ImportError:
    WATERMARKING_ENABLED = False

# Configuration de la page
st.set_page_config(
    page_title="WatchAI - Government Logistics Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS professionnel
st.markdown("""
<style>
    /* Import des fonts Google */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&family=Inter:wght@400;500;600&family=Fira+Code:wght@400;600&display=swap');

    /* Main styling WATCHAI */
    .stApp {
        background: #F8F9FA;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling WATCHAI */
    .main-header {
        background: linear-gradient(135deg, #4DBDB3 0%, #3D4547 100%);
        color: white;
        border-radius: 8px;
        padding: 2rem;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 16px rgba(61, 69, 71, 0.15);
    }
    
    .main-header h1 {
        font-family: 'Montserrat', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 10px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header p {
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.9);
        margin: 0;
        font-weight: 400;
    }
    
    /* Metrics styling WATCHAI */
    [data-testid="metric-container"] {
        background: white;
        border-left: 4px solid #4DBDB3;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(61, 69, 71, 0.1);
        transition: all 0.3s ease;
    }

    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(61, 69, 71, 0.15);
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #3D4547;
        font-family: 'Fira Code', monospace;
        font-weight: 700;
        font-size: 1.8rem;
    }
    
    [data-testid="metric-container"] [data-testid="metric-label"] {
        color: #2C3335;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 12px;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: white;
        border-radius: 8px;
        padding: 8px;
        border: 1px solid #ddd;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 4px;
        color: #2c3e50;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: #4DBDB3 !important;
        color: white !important;
    }
    
    /* Sidebar styling WATCHAI */
    .css-1d391kg {
        background: linear-gradient(180deg, #F8F9FA 0%, #FFFFFF 100%);
    }
    
    /* Footer styling WATCHAI */
    .footer {
        text-align: center;
        color: white;
        padding: 2rem;
        background: #2C3335;
        border-radius: 8px;
        margin-top: 2rem;
        box-shadow: 0 2px 8px rgba(61, 69, 71, 0.1);
    }

    /* Buttons WATCHAI */
    .stButton > button {
        background: #4DBDB3 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        background: #5DC9BF !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(77, 189, 179, 0.3) !important;
    }

    /* Progress bar WATCHAI */
    .stProgress > div > div > div {
        background: #4DBDB3 !important;
    }

    /* Logo styling */
    .watchai-logo {
        height: 50px;
        width: auto;
        filter: brightness(0) invert(1);
    }
</style>
""", unsafe_allow_html=True)

# Configuration des couleurs WATCHAI selon la charte graphique
COLORS = {
    'primary': '#4DBDB3',       # WatchAI Teal
    'secondary': '#3D4547',     # WatchAI Dark
    'accent': '#7DD8D0',        # Teal clair
    'charcoal': '#2C3335',      # Charcoal
    'silver': '#E8E8E8',        # Silver
    'success': '#27AE60',       # Green
    'warning': '#F39C12',       # Orange
    'error': '#E74C3C',         # Red
    'info': '#3498DB',          # Blue
    'chart_palette': ['#4DBDB3', '#3D4547', '#7DD8D0', '#2C3335', '#F39C12', '#3498DB', '#27AE60', '#E74C3C']
}

# Saisons incomplètes avec détails des mois exclus
INCOMPLETE_SEASONS = {
    '2024-2025': '(excl: sept)'
}

# Mapping pays
COUNTRY_NAMES = {
    'NL': 'Pays-Bas',
    'DE': 'Allemagne',
    'BE': 'Belgique',
    'FR': 'France',
    'ES': 'Espagne',
    'IT': 'Italie',
    'GB': 'Royaume-Uni',
    'US': 'États-Unis',
    'MY': 'Malaisie',
    'SG': 'Singapour',
    'ID': 'Indonésie',
    'TR': 'Turquie',
    'RU': 'Russie',
    'CN': 'Chine',
    'IN': 'Inde',
    'XX': 'Autres'
}

# Logging de l'accès initial à la webapp
if LOGGING_ENABLED:
    if 'logged_access' not in st.session_state:
        watchai_logger.log_access("webapp_volumes_reels", "page_load")
        st.session_state.logged_access = True

@st.cache_data(ttl=3600, show_spinner="Chargement des données mises à jour...")
def load_data_raw():
    """Charge les données BRUTES depuis DB_Shipping_Master.xlsx (sans watermarking)"""
    if LOGGING_ENABLED:
        watchai_logger.log_activity("data_load", "Loading DB_Shipping_Master.xlsx")

    # Vérifier et synchroniser la base de données automatiquement
    try:
        from db_sync import auto_sync_check
        auto_sync_check()
    except ImportError:
        pass
    except Exception as e:
        if LOGGING_ENABLED:
            watchai_logger.log_activity("sync_warning", f"Auto-sync failed: {str(e)}")

    try:
        # UNE SEULE source de données : Master_Data/DB_Shipping_Master.xlsx
        possible_paths = [
            Path("Master_Data/DB_Shipping_Master.xlsx"),  # Relatif à WATCHAI (racine Git)
            Path("../Master_Data/DB_Shipping_Master.xlsx"),  # Depuis Webapp/ (local)
            Path("/mount/src/watchai/Master_Data/DB_Shipping_Master.xlsx"),  # Streamlit Cloud
        ]

        df = None
        for path in possible_paths:
            if path.exists():
                df_abj = pd.read_excel(path, sheet_name='DB ABJ')
                df_sp = pd.read_excel(path, sheet_name='DB SP')

                # Ajouter colonne PORT
                df_abj['PORT'] = 'ABIDJAN'
                df_sp['PORT'] = 'SAN PEDRO'

                # NE PAS utiliser la colonne 9 qui contient des valeurs incorrectes
                df_abj['CATEGORIE_PRODUIT'] = None
                df_sp['CATEGORIE_PRODUIT'] = None

                # Combiner
                df = pd.concat([df_abj, df_sp], ignore_index=True)
                break

        if df is None:
            st.error("Impossible de trouver DB_Shipping_Master.xlsx dans Master_Data/")
            return None
        
        # Traitement des données
        df['DATENR'] = pd.to_datetime(df['DATENR'], errors='coerce')
        df = df[df['DATENR'].notna()]
        
        # Ajouter la saison cacaoyère
        df['SAISON'] = df['DATENR'].apply(determine_season)
        df = df[df['SAISON'].notna()]
        
        # Ajouter colonnes temporelles
        df['ANNEE'] = df['DATENR'].dt.year
        df['MOIS'] = df['DATENR'].dt.month
        df['MOIS_NOM'] = df['DATENR'].dt.strftime('%b')
        
        # Catégoriser les produits - utiliser la colonne si disponible, sinon POSTAR
        def get_product_category(row):
            if pd.notna(row.get('CATEGORIE_PRODUIT')):
                return str(row['CATEGORIE_PRODUIT']).strip()
            else:
                return categorize_product(row['POSTAR'])
        
        df['PRODUIT'] = df.apply(get_product_category, axis=1)
        
        # Poids en tonnes
        df['POIDS_TONNES'] = pd.to_numeric(df['PDSNET'], errors='coerce') / 1000
        
        return df
        
    except Exception as e:
        st.error(f"Erreur chargement données: {e}")
        return None

def load_data():
    """
    Charge les données et applique le watermarking selon l'utilisateur connecté
    """
    # Charger les données brutes (depuis cache)
    df_raw = load_data_raw()

    if df_raw is None:
        return None

    # Appliquer le watermarking si activé et si utilisateur connecté
    if WATERMARKING_ENABLED and 'username' in st.session_state:
        username = st.session_state.username
        df_watermarked = watermarking.apply_watermark(df_raw, username)

        # Logger pour l'admin
        if LOGGING_ENABLED and username != "Julien":
            watchai_logger.log_activity(
                "data_watermark",
                f"Applied watermark for user {username}"
            )

        return df_watermarked
    else:
        # Pas de watermarking (pas connecté ou désactivé)
        return df_raw.copy()

def determine_season(date):
    """Détermine la saison cacaoyère (Oct-Sept)"""
    if pd.isna(date):
        return None
    try:
        month = date.month
        year = date.year
        if month >= 10:
            return f"{year}-{year+1}"
        else:
            return f"{year-1}-{year}"
    except:
        return None

def categorize_product(postar):
    """Catégorise le produit selon le code POSTAR"""
    if pd.isna(postar):
        return 'FEVES'
    
    # Convertir en string et prendre les 4 premiers chiffres
    postar_str = str(int(postar)) if isinstance(postar, (int, float)) else str(postar).strip()
    
    # Les codes POSTAR peuvent avoir 4, 6 ou 10 chiffres - on prend les 4 premiers
    if len(postar_str) >= 4:
        code = postar_str[:4]
    else:
        code = postar_str
    
    # Catégoriser selon les 4 premiers chiffres
    if code == '1801':
        return 'FEVES'
    elif code == '1803':
        return 'LIQUEUR'  # Pâte de cacao / Liqueur
    elif code == '1804':
        return 'BEURRE'
    elif code == '1805':
        return 'POUDRE'
    elif code == '1806':
        return 'CHOCOLAT'
    elif code == '1802':
        return 'COQUES'
    else:
        # Par défaut FEVES
        return 'FEVES'

def display_header(df):
    """Affiche l'en-tête WATCHAI avec logo et statistiques globales"""

    # Charger l'image en base64 pour intégration directe
    try:
        import base64
        # Essayer plusieurs chemins possibles pour le logo
        logo_paths = [
            Path("logo.png"),                              # Local (Webapp/)
            Path("Webapp/logo.png"),                       # Depuis racine
            Path("Images/WatchAI logo2.png"),              # Images à la racine
            Path("../Images/WatchAI logo2.png"),           # Images depuis Webapp/
        ]

        logo_found = False
        for logo_path in logo_paths:
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode()
                    logo_html = f'<img src="data:image/png;base64,{logo_data}" width="80" height="80" style="margin-right: 24px;">'
                logo_found = True
                break

        if not logo_found:
            logo_html = '<div style="width: 80px; height: 80px; background: rgba(255,255,255,0.2); border-radius: 8px; margin-right: 24px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px;">WA</div>'
    except:
        logo_html = '<div style="width: 80px; height: 80px; background: rgba(255,255,255,0.2); border-radius: 8px; margin-right: 24px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px;">WA</div>'

    # Header avec logo WATCHAI
    st.markdown(f"""
    <div class="main-header">
        <div style="display: flex; align-items: center;">
            {logo_html}
            <div>
                <h1 style='margin: 0;'>WatchAI</h1>
                <p style='margin: 0.5rem 0 0 0;'>Government Logistics Intelligence - Export Analysis Platform</p>
            </div>
        </div>
        <div style="text-align: right; font-size: 0.9rem;">
            <div><strong>WatchAI</strong></div>
            <div>Version 1.2 - Oct 2025</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Métriques globales
    col1, col2, col3, col4 = st.columns(4)
    
    total_volume = df['POIDS_TONNES'].sum() / 1_000_000
    total_operations = len(df)
    nb_seasons = df['SAISON'].nunique()
    nb_exporters = df['EXPORTATEUR SIMPLE'].nunique()
    
    with col1:
        st.metric("Volume Total", f"{total_volume:.1f}M tonnes", 
                 help="Volume total exporté depuis 2013")
    with col2:
        st.metric("Opérations", f"{total_operations:,}", 
                 help="Nombre total d'opérations d'export")
    with col3:
        st.metric("Saisons", f"{nb_seasons:,}", 
                 help="Nombre de saisons cacaoyères")
    with col4:
        st.metric("Exportateurs", f"{nb_exporters:,}", 
                 help="Nombre d'exportateurs uniques")

def create_season_evolution(df):
    """Graphique évolution par saison"""
    season_volumes = df.groupby('SAISON')['POIDS_TONNES'].sum().reset_index()
    season_volumes = season_volumes.sort_values('SAISON')
    
    fig = go.Figure()
    
    # Ligne principale
    fig.add_trace(go.Scatter(
        x=season_volumes['SAISON'],
        y=season_volumes['POIDS_TONNES'],
        mode='lines+markers',
        name='Volume',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=10),
        fill='tozeroy',
        fillcolor='rgba(30, 58, 95, 0.2)'
    ))
    
    # Marquer les saisons incomplètes
    for season, note in INCOMPLETE_SEASONS.items():
        if season in season_volumes['SAISON'].values:
            vol = season_volumes[season_volumes['SAISON'] == season]['POIDS_TONNES'].values[0]
            fig.add_annotation(
                x=season, y=vol,
                text=note,
                showarrow=True,
                arrowhead=2,
                arrowcolor=COLORS['warning'],
                ax=0, ay=-40
            )
    
    fig.update_layout(
        title="Évolution des Volumes par Saison",
        xaxis_title="Saison",
        yaxis_title="Volume (tonnes)",
        hovermode='x unified',
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(tickformat=',.0f')
    )
    
    return fig

def create_monthly_pattern(df, season=None):
    """Graphique pattern mensuel"""
    if season:
        df_filtered = df[df['SAISON'] == season]
        title = f"Pattern Mensuel - Saison {season}"
    else:
        df_filtered = df
        title = "Pattern Mensuel - Toutes Saisons"
    
    # Ordre des mois dans une saison cacaoyère
    months_order = {10: 'Oct', 11: 'Nov', 12: 'Déc', 
                   1: 'Jan', 2: 'Fév', 3: 'Mar',
                   4: 'Avr', 5: 'Mai', 6: 'Juin',
                   7: 'Juil', 8: 'Août', 9: 'Sept'}
    
    monthly_data = df_filtered.groupby('MOIS')['POIDS_TONNES'].sum().reset_index()
    monthly_data['MOIS_NOM'] = monthly_data['MOIS'].map(months_order)
    monthly_data['ORDER'] = monthly_data['MOIS'].map({10:1, 11:2, 12:3, 1:4, 2:5, 3:6, 4:7, 5:8, 6:9, 7:10, 8:11, 9:12})
    monthly_data = monthly_data.sort_values('ORDER')
    
    fig = go.Figure(data=[
        go.Bar(
            x=monthly_data['MOIS_NOM'],
            y=monthly_data['POIDS_TONNES'],
            marker_color=COLORS['chart_palette'],
            text=monthly_data['POIDS_TONNES'],
            texttemplate='%{text:,.0f}',
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Mois",
        yaxis_title="Volume (tonnes)",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(tickformat=',.0f')
    )
    
    return fig

def create_top_exporters(df, season=None, top_n=15):
    """Graphique top exportateurs"""
    if season:
        df_filtered = df[df['SAISON'] == season]
        title = f"Top {top_n} Exportateurs - {season}"
    else:
        df_filtered = df
        title = f"Top {top_n} Exportateurs - Toutes Saisons"
    
    top_exp = df_filtered.groupby('EXPORTATEUR SIMPLE')['POIDS_TONNES'].sum().nlargest(top_n).reset_index()
    
    fig = go.Figure(data=[
        go.Bar(
            y=top_exp['EXPORTATEUR SIMPLE'],
            x=top_exp['POIDS_TONNES'],
            orientation='h',
            marker_color=COLORS['primary'],
            text=top_exp['POIDS_TONNES'],
            texttemplate='%{text:,.0f} t',
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Volume (tonnes)",
        yaxis_title="",
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(tickformat=',.0f'),
        yaxis=dict(autorange="reversed")
    )
    
    return fig

def create_destinations_map(df, season=None):
    """Carte des destinations"""
    if season:
        df_filtered = df[df['SAISON'] == season]
        title = f"Destinations - {season}"
    else:
        df_filtered = df
        title = "Destinations - Toutes Saisons"
    
    dest_data = df_filtered.groupby('DESTINATION')['POIDS_TONNES'].sum().reset_index()
    dest_data['PAYS'] = dest_data['DESTINATION'].map(COUNTRY_NAMES).fillna(dest_data['DESTINATION'])
    dest_data = dest_data.nlargest(15, 'POIDS_TONNES')
    
    fig = go.Figure(data=[
        go.Bar(
            x=dest_data['PAYS'],
            y=dest_data['POIDS_TONNES'],
            marker_color=COLORS['secondary'],
            text=dest_data['POIDS_TONNES'],
            texttemplate='%{text:,.0f}',
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Pays",
        yaxis_title="Volume (tonnes)",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(tickformat=',.0f'),
        xaxis_tickangle=-45
    )
    
    return fig

def create_ports_distribution(df, season=None):
    """Distribution par port"""
    if season:
        df_filtered = df[df['SAISON'] == season]
        title = f"Répartition par Port - {season}"
    else:
        df_filtered = df
        title = "Répartition par Port"
    
    port_data = df_filtered.groupby('PORT')['POIDS_TONNES'].sum().reset_index()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=port_data['PORT'],
            values=port_data['POIDS_TONNES'],
            hole=0.4,
            marker_colors=[COLORS['primary'], COLORS['secondary']]
        )
    ])
    
    fig.update_layout(
        title=title,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_products_mix(df, season=None):
    """Mix produits"""
    if season:
        df_filtered = df[df['SAISON'] == season]
        title = f"Mix Produits - {season}"
    else:
        df_filtered = df
        title = "Mix Produits Global"
    
    product_data = df_filtered.groupby('PRODUIT')['POIDS_TONNES'].sum().reset_index()
    product_data = product_data.sort_values('POIDS_TONNES', ascending=False)
    
    fig = go.Figure(data=[
        go.Pie(
            labels=product_data['PRODUIT'],
            values=product_data['POIDS_TONNES'],
            hole=0.3,
            marker_colors=COLORS['chart_palette']
        )
    ])
    
    fig.update_layout(
        title=title,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def display_season_analysis(df, season):
    """Affiche l'analyse détaillée d'une saison"""
    df_season = df[df['SAISON'] == season]
    
    # Alerte si saison incomplète
    if season in INCOMPLETE_SEASONS:
        st.warning(f"Saison {season} - Données incomplètes {INCOMPLETE_SEASONS[season]}")
    
    # Métriques de la saison
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        volume = df_season['POIDS_TONNES'].sum()
        st.metric("Volume Saison", f"{volume:,.0f} tonnes")
    
    with col2:
        operations = len(df_season)
        st.metric("Opérations", f"{operations:,}")
    
    with col3:
        exporters = df_season['EXPORTATEUR SIMPLE'].nunique()
        st.metric("Exportateurs", f"{exporters:,}")
    
    with col4:
        avg_shipment = df_season['POIDS_TONNES'].mean()
        st.metric("Envoi Moyen", f"{avg_shipment:,.0f} tonnes")
    
    # Graphiques
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Mensuel", "Exportateurs", "Destinations", "Produits", "Ports"]
    )
    
    with tab1:
        st.plotly_chart(create_monthly_pattern(df, season), use_container_width=True)
    
    with tab2:
        st.plotly_chart(create_top_exporters(df, season), use_container_width=True)
        
        # Table détaillée
        with st.expander("Voir le détail complet"):
            exp_data = df_season.groupby('EXPORTATEUR SIMPLE')['POIDS_TONNES'].agg(['sum', 'count']).reset_index()
            exp_data.columns = ['Exportateur', 'Volume Total (tonnes)', 'Nb Opérations']
            exp_data = exp_data.sort_values('Volume Total (tonnes)', ascending=False)
            # Formatter les colonnes numériques
            exp_data['Volume Total (tonnes)'] = exp_data['Volume Total (tonnes)'].apply(lambda x: f"{x:,.0f}")
            exp_data['Nb Opérations'] = exp_data['Nb Opérations'].apply(lambda x: f"{x:,}")
            st.dataframe(exp_data, use_container_width=True)
    
    with tab3:
        st.plotly_chart(create_destinations_map(df, season), use_container_width=True)
        
        # Top clients
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 10 Clients")
            top_clients = df_season.groupby('DESTINATAIRE SIMPLE')['POIDS_TONNES'].sum().nlargest(10)
            top_clients_df = top_clients.reset_index()
            top_clients_df.columns = ['Client', 'Volume (tonnes)']
            top_clients_df['Volume (tonnes)'] = top_clients_df['Volume (tonnes)'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(top_clients_df, use_container_width=True)
        
        with col2:
            st.subheader("Top 10 Pays")
            top_countries = df_season.groupby('DESTINATION')['POIDS_TONNES'].sum().nlargest(10)
            top_countries_df = top_countries.reset_index()
            top_countries_df.columns = ['Code Pays', 'Volume (tonnes)']
            top_countries_df['Code Pays'] = top_countries_df['Code Pays'].map(lambda x: COUNTRY_NAMES.get(x, x))
            top_countries_df['Volume (tonnes)'] = top_countries_df['Volume (tonnes)'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(top_countries_df, use_container_width=True)
    
    with tab4:
        st.plotly_chart(create_products_mix(df, season), use_container_width=True)
        
        # Détail par produit
        product_detail = df_season.groupby('PRODUIT')['POIDS_TONNES'].agg(['sum', 'mean', 'count']).reset_index()
        product_detail.columns = ['Produit', 'Volume Total', 'Volume Moyen', 'Nb Opérations']
        product_detail = product_detail.sort_values('Volume Total', ascending=False)
        # Formatter les colonnes numériques
        product_detail['Volume Total'] = product_detail['Volume Total'].apply(lambda x: f"{x:,.0f}")
        product_detail['Volume Moyen'] = product_detail['Volume Moyen'].apply(lambda x: f"{x:,.0f}")
        product_detail['Nb Opérations'] = product_detail['Nb Opérations'].apply(lambda x: f"{x:,}")
        st.dataframe(product_detail, use_container_width=True)
    
    with tab5:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_ports_distribution(df, season), use_container_width=True)
        
        with col2:
            port_stats = df_season.groupby('PORT').agg({
                'POIDS_TONNES': ['sum', 'mean', 'count']
            }).reset_index()
            port_stats.columns = ['Port', 'Volume Total', 'Volume Moyen', 'Nb Opérations']
            # Formatter les colonnes numériques
            port_stats['Volume Total'] = port_stats['Volume Total'].apply(lambda x: f"{x:,.0f}")
            port_stats['Volume Moyen'] = port_stats['Volume Moyen'].apply(lambda x: f"{x:,.0f}")
            port_stats['Nb Opérations'] = port_stats['Nb Opérations'].apply(lambda x: f"{x:,}")
            st.dataframe(port_stats, use_container_width=True)

def check_authentication():
    """Gère l'authentification des utilisateurs avec protections de sécurité"""

    # Utiliser la configuration depuis auth_config.py
    from auth_config import USERS, verify_password, get_user_info, log_connection

    # Initialiser l'état de session
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_info = None

    # Si pas authentifié, afficher le formulaire de connexion
    if not st.session_state.authenticated:
        # Charger le logo WATCHAI pour la page de connexion
        try:
            import base64
            # Essayer plusieurs chemins possibles pour le logo
            logo_paths = [
                Path("logo.png"),                              # Local (Webapp/)
                Path("Webapp/logo.png"),                       # Depuis racine
                Path("Images/WatchAI logo2.png"),              # Images à la racine
                Path("../Images/WatchAI logo2.png"),           # Images depuis Webapp/
            ]

            logo_found = False
            for logo_path in logo_paths:
                if logo_path.exists():
                    with open(logo_path, "rb") as f:
                        logo_data = base64.b64encode(f.read()).decode()
                        logo_html = f'<img src="data:image/png;base64,{logo_data}" width="120" style="margin-bottom: 1rem;">'
                    logo_found = True
                    break

            if not logo_found:
                logo_html = '<div style="width: 120px; height: 120px; background: #4DBDB3; border-radius: 8px; margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">WA</div>'
        except:
            logo_html = '<div style="width: 120px; height: 120px; background: #4DBDB3; border-radius: 8px; margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">WA</div>'

        st.markdown(f"""
        <div style='text-align: center; padding: 2rem;'>
            {logo_html}
            <h1 style='color: #3D4547; font-family: Montserrat, sans-serif;'>WatchAI</h1>
            <h2 style='color: #4DBDB3; font-size: 1.2rem; margin-bottom: 1rem;'>Government Logistics Intelligence</h2>
            <p style='color: #666;'>Veuillez vous connecter pour accéder au dashboard</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            # Vérifier si CAPTCHA est nécessaire
            needs_captcha = False
            if SECURITY_ENABLED and 'temp_username' in st.session_state:
                needs_captcha, attempts = security_middleware.track_login_attempt(
                    st.session_state.temp_username, success=False
                )
                if attempts > 0:
                    st.warning(f"⚠️ {attempts} tentative(s) échouée(s)")

            with st.form("login_form"):
                st.subheader("Connexion")
                username = st.text_input("Nom d'utilisateur", key="login_username")
                password = st.text_input("Mot de passe", type="password", key="login_password")

                # Afficher CAPTCHA si nécessaire
                captcha_valid = True
                if SECURITY_ENABLED and needs_captcha:
                    st.warning("🔒 Plusieurs tentatives échouées détectées. Veuillez compléter le CAPTCHA.")
                    security_middleware.display_captcha()
                    captcha_input = st.text_input("Entrez le code ci-dessus:", key="captcha_input")
                    captcha_valid = False  # Sera vérifié lors du submit

                submit = st.form_submit_button("Se connecter", use_container_width=True)

                if submit:
                    st.session_state.temp_username = username

                    # Vérifier CAPTCHA si nécessaire
                    if SECURITY_ENABLED and needs_captcha:
                        if not security_middleware.verify_captcha(captcha_input):
                            st.error("❌ Code CAPTCHA incorrect")
                            st.session_state.regenerate_captcha = True
                            st.rerun()
                            return False

                    # Vérifier les identifiants
                    if verify_password(username, password):
                        # Connexion réussie
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_info = get_user_info(username)
                        log_connection(username, success=True)

                        # Reset sécurité
                        if SECURITY_ENABLED:
                            security_middleware.track_login_attempt(username, success=True)
                            if 'temp_username' in st.session_state:
                                del st.session_state.temp_username

                        st.rerun()
                    else:
                        # Connexion échouée
                        log_connection(username, success=False)
                        if SECURITY_ENABLED:
                            security_middleware.track_login_attempt(username, success=False)
                        st.error("❌ Nom d'utilisateur ou mot de passe incorrect")
                        st.session_state.regenerate_captcha = True

        return False

    return True

def main():
    """Fonction principale"""

    # Vérifier l'authentification
    if not check_authentication():
        return

    # === SÉCURITÉ 1: SESSION TIMEOUT ===
    if SECURITY_ENABLED:
        if not security_middleware.check_session_timeout():
            st.warning("⏰ Votre session a expiré par inactivité (30 minutes)")
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_info = None
            security_middleware.reset_session()
            st.rerun()
            return

    # === SÉCURITÉ 2: RATE LIMITING ===
    if SECURITY_ENABLED:
        session_id = security_middleware.get_session_id()
        allowed, remaining, reset_time = security_middleware.check_rate_limit(session_id)

        if not allowed:
            st.error(f"🚫 Limite de requêtes dépassée (100 requêtes/heure)")
            st.info(f"Réinitialisation à: {reset_time}")
            st.stop()

    # Afficher les infos utilisateur dans la sidebar
    st.sidebar.markdown(f"""
    **Connecté en tant que:**
    {st.session_state.user_info['name']}
    *({st.session_state.user_info['role']})*
    """)

    # Afficher les infos de sécurité en sidebar (si admin)
    if st.session_state.get("username") == "Julien":
        security_info = []

        # Rate limiting info
        if SECURITY_ENABLED:
            session_id = security_middleware.get_session_id()
            rate_info = security_middleware.get_rate_limit_info(session_id)
            security_info.append(f"- Requêtes: {rate_info['total_requests']}/{rate_info['limit']}")
            security_info.append(f"- Restantes: {rate_info['remaining']}")

        # Watermarking info
        if WATERMARKING_ENABLED:
            wm_info = watermarking.get_watermark_info("Julien")
            security_info.append(f"- Watermark: {wm_info['type']}")

        if security_info:
            st.sidebar.markdown(f"""
        **🔒 Sécurité:**
        {chr(10).join(security_info)}
        """)
    elif WATERMARKING_ENABLED:
        # Pour les non-admins, afficher juste une info discrète
        username = st.session_state.get("username", "")
        wm_info = watermarking.get_watermark_info(username)
        if wm_info['enabled']:
            st.sidebar.markdown(f"""
        *🔐 Données protégées*
        """)

    # Bouton de déconnexion
    if st.sidebar.button("Déconnexion"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_info = None
        if SECURITY_ENABLED:
            security_middleware.reset_session()
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Titre et description dans la sidebar
    st.sidebar.title("Navigation")
    st.sidebar.markdown("""
    **Dashboard Analytics Cacao CI**
    
    Analyse complète des exportations de cacao de Côte d'Ivoire depuis 2013.
    """)
    
    # Chargement des données
    with st.spinner("Chargement des données..."):
        df = load_data()
    
    if df is None:
        st.error("Impossible de charger les données. Vérifiez que DB_Shipping_Master.xlsx est présent.")
        return
    
    # Header
    display_header(df)
    
    st.markdown("---")
    
    # Sélection du mode d'analyse
    analysis_mode = st.sidebar.radio(
        "Mode d'analyse",
["Vue Globale", "Analyse par Saison", "Analyse Comparative"]
    )
    
    if analysis_mode == "Vue Globale":
        st.header("Vue Globale - Toutes Saisons")
        
        # Évolution temporelle
        st.plotly_chart(create_season_evolution(df), use_container_width=True)
        
        # Graphiques en colonnes
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_ports_distribution(df), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_products_mix(df), use_container_width=True)
        
        # Top exportateurs et destinations
        st.plotly_chart(create_top_exporters(df), use_container_width=True)
        st.plotly_chart(create_destinations_map(df), use_container_width=True)
    
    elif analysis_mode == "Analyse par Saison":
        # Sélection de la saison
        seasons = sorted(df['SAISON'].unique(), reverse=True)
        
        # Ajouter indicateur pour saisons incomplètes
        selected_season = st.sidebar.selectbox(
            "Sélectionner une saison",
            options=seasons,
            format_func=lambda x: f"{x} {INCOMPLETE_SEASONS.get(x, '')}" if x in INCOMPLETE_SEASONS else x
        )
        
        st.header(f"Analyse Saison {selected_season}")
        display_season_analysis(df, selected_season)
    
    else:  # Analyse Comparative
        st.header("Analyse Comparative")
        
        # Sélection de plusieurs saisons
        seasons = sorted(df['SAISON'].unique())
        selected_seasons = st.sidebar.multiselect(
            "Sélectionner les saisons à comparer",
            options=seasons,
            default=[]  # Vide par défaut
        )
        
        if len(selected_seasons) < 2:
            st.warning("Sélectionnez au moins 2 saisons pour la comparaison")
        else:
            # Filtres additionnels dans la sidebar
            st.sidebar.markdown("---")
            st.sidebar.subheader("Filtres")
            
            # Préparer les données pour les filtres - garder df_base intacte
            df_base = df[df['SAISON'].isin(selected_seasons)]
            
            # Préparer toutes les listes AVANT de créer les multiselects
            exportateurs = sorted(df_base['EXPORTATEUR SIMPLE'].unique())
            destinataires = sorted(df_base['DESTINATAIRE SIMPLE'].unique())
            destinations_raw = df_base['DESTINATION'].unique()
            destinations = sorted([str(d) for d in destinations_raw if pd.notna(d)])
            destinations_with_names = [f"{code} - {COUNTRY_NAMES.get(code, code)}" for code in destinations]
            produits = sorted(df_base['PRODUIT'].unique())
            
            # Créer les multiselects avec les bonnes listes
            selected_exportateurs = st.sidebar.multiselect(
                "Filtrer par Exportateur",
                options=exportateurs,
                default=[],
                key="filter_exportateurs"
            )
            
            selected_destinataires = st.sidebar.multiselect(
                "Filtrer par Destinataire",
                options=destinataires,
                default=[],
                key="filter_destinataires"
            )
            
            selected_destinations_display = st.sidebar.multiselect(
                "Filtrer par Destination",
                options=destinations_with_names,
                default=[],
                key="filter_destinations"
            )
            selected_destinations = [d.split(' - ')[0] for d in selected_destinations_display]
            
            selected_produits = st.sidebar.multiselect(
                "Filtrer par Produit",
                options=produits,
                default=[],
                key="filter_produits"
            )
            
            # Appliquer les filtres sur df_base
            df_filtered = df_base.copy()
            if selected_exportateurs:
                df_filtered = df_filtered[df_filtered['EXPORTATEUR SIMPLE'].isin(selected_exportateurs)]
            if selected_destinataires:
                df_filtered = df_filtered[df_filtered['DESTINATAIRE SIMPLE'].isin(selected_destinataires)]
            if selected_destinations:
                df_filtered = df_filtered[df_filtered['DESTINATION'].isin(selected_destinations)]
            if selected_produits:
                df_filtered = df_filtered[df_filtered['PRODUIT'].isin(selected_produits)]
            
            # Utiliser df_filtered pour la suite
            df = df_filtered
            # Métriques générales
            st.subheader(" Vue d'ensemble")
            comparison_data = []
            for season in selected_seasons:
                df_s = df[df['SAISON'] == season]
                comparison_data.append({
                    'Saison': season,
                    'Volume Total': df_s['POIDS_TONNES'].sum(),
                    'Opérations': len(df_s),
                    'Exportateurs': df_s['EXPORTATEUR SIMPLE'].nunique(),
                    'Destinations': df_s['DESTINATION'].nunique()
                })
            
            comp_df = pd.DataFrame(comparison_data)
            comp_display = comp_df.copy()
            comp_display['Volume Total'] = comp_display['Volume Total'].apply(lambda x: f"{x:,.0f}")
            comp_display['Opérations'] = comp_display['Opérations'].apply(lambda x: f"{x:,}")
            comp_display['Exportateurs'] = comp_display['Exportateurs'].apply(lambda x: f"{x:,}")
            comp_display['Destinations'] = comp_display['Destinations'].apply(lambda x: f"{x:,}")
            st.dataframe(comp_display, use_container_width=True)
            
            # Graphiques comparatifs détaillés
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏭 Top 5 Exportateurs")
                # Top 5 exportateurs pour chaque saison
                fig_exp = go.Figure()
                for i, season in enumerate(selected_seasons):
                    df_s = df[df['SAISON'] == season]
                    top_exp = df_s.groupby('EXPORTATEUR SIMPLE')['POIDS_TONNES'].sum().nlargest(5)
                    
                    fig_exp.add_trace(go.Bar(
                        name=season,
                        x=top_exp.index,
                        y=top_exp.values,
                        marker_color=COLORS['chart_palette'][i % len(COLORS['chart_palette'])],
                        text=[f"{v:,.0f}" for v in top_exp.values],
                        textposition='outside'
                    ))
                
                fig_exp.update_layout(
                    barmode='group',
                    xaxis_title="Exportateurs",
                    yaxis_title="Volume (tonnes)",
                    yaxis=dict(tickformat=',.0f'),
                    showlegend=True,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_exp, use_container_width=True)
            
            with col2:
                st.subheader(" Top 5 Destinataires")
                # Top 5 destinataires pour chaque saison
                fig_dest = go.Figure()
                for i, season in enumerate(selected_seasons):
                    df_s = df[df['SAISON'] == season]
                    top_dest = df_s.groupby('DESTINATAIRE SIMPLE')['POIDS_TONNES'].sum().nlargest(5)
                    
                    fig_dest.add_trace(go.Bar(
                        name=season,
                        x=top_dest.index,
                        y=top_dest.values,
                        marker_color=COLORS['chart_palette'][i % len(COLORS['chart_palette'])],
                        text=[f"{v:,.0f}" for v in top_dest.values],
                        textposition='outside'
                    ))
                
                fig_dest.update_layout(
                    barmode='group',
                    xaxis_title="Destinataires",
                    yaxis_title="Volume (tonnes)",
                    yaxis=dict(tickformat=',.0f'),
                    showlegend=True,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_dest, use_container_width=True)
            
            # Deuxième ligne de graphiques
            col3, col4 = st.columns(2)
            
            with col3:
                st.subheader(" Top 5 Destinations (Pays)")
                # Top 5 pays pour chaque saison
                fig_pays = go.Figure()
                for i, season in enumerate(selected_seasons):
                    df_s = df[df['SAISON'] == season]
                    top_pays = df_s.groupby('DESTINATION')['POIDS_TONNES'].sum().nlargest(5)
                    # Convertir codes pays en noms
                    pays_names = [COUNTRY_NAMES.get(code, code) for code in top_pays.index]
                    
                    fig_pays.add_trace(go.Bar(
                        name=season,
                        x=pays_names,
                        y=top_pays.values,
                        marker_color=COLORS['chart_palette'][i % len(COLORS['chart_palette'])],
                        text=[f"{v:,.0f}" for v in top_pays.values],
                        textposition='outside'
                    ))
                
                fig_pays.update_layout(
                    barmode='group',
                    xaxis_title="Pays",
                    yaxis_title="Volume (tonnes)",
                    yaxis=dict(tickformat=',.0f'),
                    showlegend=True,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_pays, use_container_width=True)
            
            with col4:
                st.subheader("📦 Fèves vs Produits Transformés")
                # Séparer Fèves et Produits transformés pour chaque saison
                fig_prod = go.Figure()
                for i, season in enumerate(selected_seasons):
                    df_s = df[df['SAISON'] == season]
                    
                    # Calculer les volumes Fèves vs Produits transformés
                    feves_vol = df_s[df_s['PRODUIT'].str.contains('FEVE', case=False, na=False)]['POIDS_TONNES'].sum()
                    produits_vol = df_s[~df_s['PRODUIT'].str.contains('FEVE', case=False, na=False)]['POIDS_TONNES'].sum()
                    
                    # Ajouter les barres
                    fig_prod.add_trace(go.Bar(
                        name=season,
                        x=['Fèves', 'Produits Transformés'],
                        y=[feves_vol, produits_vol],
                        marker_color=COLORS['chart_palette'][i % len(COLORS['chart_palette'])],
                        text=[f"{feves_vol:,.0f}", f"{produits_vol:,.0f}"],
                        textposition='outside'
                    ))
                
                fig_prod.update_layout(
                    barmode='group',
                    xaxis_title="Catégories",
                    yaxis_title="Volume (tonnes)",
                    yaxis=dict(tickformat=',.0f'),
                    showlegend=True,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_prod, use_container_width=True)
                
                # Détail des produits transformés
                with st.expander("Voir détail des produits transformés"):
                    for season in selected_seasons:
                        df_s = df[df['SAISON'] == season]
                        # Exclure les fèves pour le détail
                        df_produits = df_s[~df_s['PRODUIT'].str.contains('FEVE', case=False, na=False)]
                        if not df_produits.empty:
                            prod_detail = df_produits.groupby('PRODUIT')['POIDS_TONNES'].sum().sort_values(ascending=False)
                            prod_df = prod_detail.reset_index()
                            prod_df.columns = ['Produit', 'Volume (tonnes)']
                            prod_df['Volume (tonnes)'] = prod_df['Volume (tonnes)'].apply(lambda x: f"{x:,.0f}")
                            st.write(f"**{season}**")
                            st.dataframe(prod_df, use_container_width=True)
            
            # Split Abidjan/San Pedro
            st.subheader("🚢 Répartition Abidjan vs San Pedro")
            col5, col6 = st.columns(2)
            
            with col5:
                # Graphique en barres
                fig_ports = go.Figure()
                for i, season in enumerate(selected_seasons):
                    df_s = df[df['SAISON'] == season]
                    port_data = df_s.groupby('PORT')['POIDS_TONNES'].sum()
                    
                    fig_ports.add_trace(go.Bar(
                        name=season,
                        x=port_data.index,
                        y=port_data.values,
                        marker_color=COLORS['chart_palette'][i % len(COLORS['chart_palette'])],
                        text=[f"{v:,.0f}" for v in port_data.values],
                        textposition='outside'
                    ))
                
                fig_ports.update_layout(
                    barmode='group',
                    xaxis_title="Ports",
                    yaxis_title="Volume (tonnes)",
                    yaxis=dict(tickformat=',.0f'),
                    showlegend=True,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_ports, use_container_width=True)
            
            with col6:
                # Tableau détaillé des ports
                st.subheader("Détail par Port")
                for season in selected_seasons:
                    df_s = df[df['SAISON'] == season]
                    port_detail = df_s.groupby('PORT')['POIDS_TONNES'].agg(['sum', 'count']).reset_index()
                    port_detail.columns = ['Port', 'Volume (tonnes)', 'Nb Opérations']
                    port_detail['Volume (tonnes)'] = port_detail['Volume (tonnes)'].apply(lambda x: f"{x:,.0f}")
                    port_detail['Nb Opérations'] = port_detail['Nb Opérations'].apply(lambda x: f"{x:,}")
                    
                    # Calculer le pourcentage
                    total_volume = df_s['POIDS_TONNES'].sum()
                    port_detail['%'] = df_s.groupby('PORT')['POIDS_TONNES'].sum().reset_index()['POIDS_TONNES'].apply(
                        lambda x: f"{(x/total_volume*100):.1f}%"
                    )
                    
                    st.write(f"**{season}**")
                    st.dataframe(port_detail, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Source: DB_Shipping_Master | Dernière mise à jour: Juillet 2025</p>
        <p>Saisons incomplètes: 2024-2025 (excl: sept)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Interface Admin - Logs d'accès (visible uniquement pour Julien)
    if st.session_state.get("username") == "Julien":  # Admin uniquement
        st.markdown("---")
        
        # Bouton pour vider le cache
        col_cache, col_space = st.columns([1, 4])
        with col_cache:
            if st.button(" Vider Cache", help="Force le rechargement des données"):
                st.cache_data.clear()
                st.rerun()
        
        with st.expander("🔍 Console de Logs - WATCHAI (Admin)", expanded=False):
            if LOGGING_ENABLED:
                # Statistiques des sessions
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

                st.markdown("---")

                # Tabs pour différentes vues
                tab_overview, tab_sessions, tab_logs = st.tabs(["Vue d'ensemble", "Sessions récentes", "Logs système"])

                with tab_overview:
                    # Sessions récentes
                    recent_sessions = watchai_logger.get_recent_sessions(10)
                    if recent_sessions:
                        st.subheader("Sessions récentes (10 dernières)")
                        df_sessions = pd.DataFrame(recent_sessions)
                        df_sessions['timestamp'] = pd.to_datetime(df_sessions['timestamp'])
                        df_sessions['time'] = df_sessions['timestamp'].dt.strftime('%H:%M:%S')

                        display_df = df_sessions[['time', 'session_id', 'client_ip', 'page', 'action', 'hostname']].copy()
                        display_df.columns = ['Heure', 'Session ID', 'IP Client', 'Page', 'Action', 'Hostname']

                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("Aucune session enregistrée")

                with tab_sessions:
                    # Sessions des dernières heures
                    hours_filter = st.selectbox("Afficher les sessions des dernières:", [1, 6, 12, 24], index=1)

                    recent_sessions = watchai_logger.get_recent_sessions(500)
                    if recent_sessions:
                        # Filtrer par heures
                        from datetime import timedelta
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
                            st.write(f"**{len(filtered_sessions)} sessions** dans les {hours_filter} dernières heures")

                            # Affichage des sessions
                            for session in filtered_sessions[-20:]:  # 20 dernières sessions
                                timestamp = datetime.fromisoformat(session['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                                st.markdown(f"""
                                <div style="background: white; border-left: 4px solid #4DBDB3; padding: 8px; margin: 4px 0; border-radius: 4px;">
                                    <strong>{timestamp}</strong> | Session: {session.get('session_id', 'N/A')[:8]}... |
                                    IP: {session.get('client_ip', 'N/A')} |
                                    Page: {session.get('page', 'N/A')} |
                                    Action: {session.get('action', 'N/A')}
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info(f"Aucune session dans les {hours_filter} dernières heures")
                    else:
                        st.info("Aucune session enregistrée")

                with tab_logs:
                    # Logs système
                    log_type = st.radio("Type de log:", ["Access Logs", "Activity Logs"])
                    num_lines = st.number_input("Nombre de lignes:", min_value=10, max_value=100, value=20)

                    try:
                        if log_type == "Access Logs":
                            log_file = "/Users/julienmarboeuf/Documents/BON PLEIN/WATCHAI/Logs/access.log"
                        else:
                            log_file = "/Users/julienmarboeuf/Documents/BON PLEIN/WATCHAI/Logs/activity.log"

                        if Path(log_file).exists():
                            with open(log_file, 'r', encoding='utf-8') as f:
                                lines = f.readlines()

                            recent_lines = lines[-num_lines:]

                            for line in reversed(recent_lines):
                                if line.strip():
                                    st.markdown(f"""
                                    <div style="background: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; margin: 2px 0; border-radius: 4px; font-family: monospace; font-size: 12px;">
                                        {line.strip()}
                                    </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.warning(f"Fichier de log non trouvé: {log_file}")

                    except Exception as e:
                        st.error(f"Erreur lors de la lecture des logs: {str(e)}")

            else:
                st.warning("Système de logging non disponible")

if __name__ == "__main__":
    main()
