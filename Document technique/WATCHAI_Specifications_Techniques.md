# WATCHAI - Government Logistics Intelligence
## Spécifications Techniques Complètes

**Version :** 2.0
**Date :** Septembre 2025
**Auteur :** Système WATCHAI
**Classification :** Document Technique Confidentiel

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture Système](#architecture-système)
3. [Stack Technologique](#stack-technologique)
4. [Modules et Fonctionnalités](#modules-et-fonctionnalités)
5. [Système de Sécurité](#système-de-sécurité)
6. [Base de Données](#base-de-données)
7. [Authentification](#authentification)
8. [Déploiement et Infrastructure](#déploiement-et-infrastructure)
9. [Performance et Scalabilité](#performance-et-scalabilité)
10. [Maintenance et Monitoring](#maintenance-et-monitoring)

---

## 1. Vue d'Ensemble

### 1.1 Objectif du Système
WATCHAI est une solution d'intelligence logistique gouvernementale spécialisée dans l'analyse des exportations de cacao de Côte d'Ivoire. Le système fournit des analyses avancées, des visualisations interactives et des rapports détaillés pour le pilotage stratégique des opérations portuaires.

### 1.2 Périmètre Fonctionnel
- **Analyse des volumes d'exportation** : Traitement de données historiques depuis 2013
- **Visualisations interactives** : Dashboards temps réel avec graphiques Plotly
- **Rapports analytiques** : Comparaisons saisonnières et évolutions temporelles
- **Gestion utilisateurs** : Système d'authentification multi-niveaux
- **Sécurité avancée** : Protection anti-scraping et monitoring des accès
- **Administration** : Interface de gestion des logs et sessions utilisateurs

### 1.3 Utilisateurs Cibles
- **Administrateurs gouvernementaux** : Accès complet aux données et fonctions d'administration
- **Analystes métier** : Consultation des données et génération de rapports
- **Opérateurs portuaires** : Accès en lecture aux statistiques opérationnelles

---

## 2. Architecture Système

### 2.1 Architecture Générale
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend Web  │    │  Applications   │    │   Base de       │
│   (Streamlit)   │◄──►│   Métier        │◄──►│   Données       │
│                 │    │   (Python)      │    │   (Excel/JSON)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Sécurité &    │    │   Logging &     │    │   Validation &  │
│   Monitoring    │    │   Audit         │    │   Scripts       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 Structure des Modules

#### Module Principal (`webapp_volumes_reels.py`)
- **Responsabilité** : Interface utilisateur principale
- **Fonctions clés** : Authentification, visualisations, analyses
- **Dépendances** : Streamlit, Plotly, Pandas, Security Manager

#### Module de Sécurité (`security_manager.py`)
- **Responsabilité** : Protection anti-scraping et contrôle d'accès
- **Fonctions clés** : Rate limiting, obfuscation, détection d'intrusion
- **Algorithmes** : Hash MD5, Base64, JavaScript protection

#### Module de Logging (`watchai_logger.py`)
- **Responsabilité** : Traçabilité et audit système
- **Fonctions clés** : Logs d'accès, sessions utilisateurs, monitoring
- **Stockage** : Fichiers JSON, logs textuels

#### Module de Validation (`validation_app.py`)
- **Responsabilité** : Validation et contrôle qualité des données
- **Fonctions clés** : Détection d'anomalies, validation business rules
- **Algorithmes** : Détection statistique, règles métier

---

## 3. Stack Technologique

### 3.1 Technologies Core

| Composant | Technologie | Version | Rôle |
|-----------|-------------|---------|------|
| **Frontend** | Streamlit | 1.39.0 | Interface utilisateur web |
| **Langage** | Python | 3.8+ | Logique métier et calculs |
| **Data Processing** | Pandas | 2.2.3 | Manipulation et analyse des données |
| **Visualisation** | Plotly | 5.24.1 | Graphiques interactifs |
| **Base de données** | Excel/JSON | - | Stockage et persistence |
| **Authentification** | SHA-256 | - | Hashage des mots de passe |

### 3.2 Dépendances Système
```python
# requirements.txt
streamlit==1.39.0
pandas==2.2.3
plotly==5.24.1
openpyxl==3.1.5
Pillow==10.4.0
numpy>=1.21.0
hashlib (built-in)
json (built-in)
pathlib (built-in)
datetime (built-in)
```

### 3.3 Architecture de Déploiement

#### Déploiement Local
- **Environnement** : Python 3.8+ avec pip
- **Commande** : `streamlit run webapp_volumes_reels.py --server.port=8523`
- **Configuration** : Fichiers locaux, accès direct aux données

#### Déploiement Cloud (Streamlit Cloud)
- **Plateforme** : Streamlit Cloud (streamlit.io)
- **Repository** : GitHub integration
- **Configuration** : Variables d'environnement, chemins relatifs
- **Domaine** : URL automatique Streamlit Cloud

---

## 4. Modules et Fonctionnalités

### 4.1 Module Principal - Analyse des Données

#### Fonctionnalités Core
1. **Chargement des données**
   ```python
   def load_data():
       # Synchronisation automatique base locale/cloud
       # Validation intégrité des données
       # Gestion des chemins multiples
   ```

2. **Analyses temporelles**
   - Évolution saisonnière des exportations
   - Comparaisons inter-annuelles
   - Tendances et prévisions

3. **Analyses géographiques**
   - Répartition par ports (Abidjan/San Pedro)
   - Destinations internationales
   - Cartographie interactive

4. **Analyses produits**
   - Mix produits (Cacao, Fèves, Transformés)
   - Volumes par catégorie
   - Évolutions qualitatives

#### Métriques Calculées
- **Volume total** : Somme des exportations (tonnes)
- **Nombre d'opérations** : Comptage des transactions
- **Volume moyen** : Volume/Opération
- **Taux de croissance** : Évolution périodique
- **Parts de marché** : Répartition pourcentage

### 4.2 Module de Visualisation

#### Types de Graphiques
1. **Graphiques temporels**
   ```python
   # Évolution mensuelle avec Plotly
   fig = px.line(df, x='DATE', y='VOLUME',
                 title="Évolution des Exportations")
   ```

2. **Graphiques de répartition**
   - Camemberts interactifs
   - Barres empilées
   - Treemaps hiérarchiques

3. **Cartes géographiques**
   - Cartographie mondiale des destinations
   - Heatmaps par pays
   - Flux commerciaux

#### Interactivité
- Filtrage dynamique par saison
- Zoom et pan sur les graphiques
- Tooltips détaillés
- Export des visualisations

### 4.3 Module d'Administration

#### Interface Admin (`admin_logs.py`)
- **Port d'accès** : 8524
- **Fonctionnalités** :
  - Consultation des logs d'accès
  - Monitoring des sessions actives
  - Statistiques d'utilisation
  - Gestion des utilisateurs bloqués

#### Métriques de Monitoring
- Nombre de sessions quotidiennes
- IPs uniques connectées
- Tentatives d'accès suspectes
- Performance des requêtes

---

## 5. Système de Sécurité

### 5.1 Architecture de Sécurité

#### Couches de Protection
1. **Authentification** : Contrôle d'accès utilisateur
2. **Rate Limiting** : Limitation des requêtes abusives
3. **Obfuscation** : Protection des données sensibles
4. **Monitoring** : Détection comportements suspects
5. **Protection client** : JavaScript anti-scraping

### 5.2 Rate Limiting

#### Configuration
```python
class SecurityManager:
    MAX_REQUESTS_PER_MINUTE = 30      # Limite requêtes/minute
    MAX_DATA_ACCESS_PER_HOUR = 10     # Limite accès données/heure
    BLOCK_DURATION_MINUTES = 30       # Durée blocage temporaire
    SESSION_TIMEOUT_HOURS = 2         # Timeout session
```

#### Algorithme de Contrôle
1. **Identification client** : Hash MD5 (IP + Session ID)
2. **Comptage requêtes** : Collections temporelles
3. **Évaluation limites** : Comparaison seuils
4. **Action** : Autorisation/Blocage/Alerte

### 5.3 Obfuscation des Données

#### Techniques Implémentées
1. **Bruit numérique**
   ```python
   # Ajout variation < 0.1% sur données numériques
   noise = df[col] * random.uniform(-0.001, 0.001)
   obfuscated_df[col] = df[col] + noise
   ```

2. **Mélange d'ordre**
   ```python
   # Randomisation ordre des lignes
   obfuscated_df = df.sample(frac=1).reset_index(drop=True)
   ```

3. **Préservation temporelle**
   - Colonnes YEAR/MONTH non altérées
   - Cohérence chronologique maintenue

### 5.4 Détection d'Intrusion

#### Patterns Détectés
1. **Requêtes rapides** : 10+ requêtes en 30 secondes
2. **Accès sans interaction** : Données sans clicks UI
3. **Comportement automatisé** : Intervalles réguliers (variance < 2s)

#### Actions Automatiques
- Logging des événements suspects
- Blocage temporaire (30 minutes)
- Notification administrateur
- Analyse forensique des sessions

### 5.5 Protection JavaScript

#### Mesures Côté Client
```javascript
// Détection DevTools
if (window.outerHeight - window.innerHeight > threshold) {
    console.warn('Accès aux données restreint');
    window.parent.postMessage('devtools_detected', '*');
}

// Désactivation interactions
document.addEventListener('contextmenu', e => e.preventDefault());
document.addEventListener('keydown', e => {
    if (e.keyCode == 123 || // F12
        (e.ctrlKey && e.shiftKey && e.keyCode == 73)) { // Ctrl+Shift+I
        e.preventDefault();
    }
});
```

---

## 6. Base de Données

### 6.1 Structure des Données

#### Fichier Principal : `DB_Shipping_Master.xlsx`
- **Format** : Excel multi-feuilles
- **Taille** : ~50MB (200k+ enregistrements)
- **Encodage** : UTF-8
- **Fréquence MAJ** : Mensuelle

#### Schema Principal
| Colonne | Type | Description | Contraintes |
|---------|------|-------------|-------------|
| DATE | DateTime | Date d'exportation | Format YYYY-MM-DD |
| VOLUME | Float | Volume en tonnes | > 0, < 50000 |
| PRODUIT | String | Type de produit | Enum: {CACAO, FEVES, TRANSFORME} |
| PORT | String | Port d'origine | Enum: {ABIDJAN, SAN_PEDRO} |
| DESTINATION | String | Pays de destination | Code ISO 3166 |
| EXPORTATEUR | String | Société exportatrice | Non-null |
| NAVIRE | String | Nom du navire | Optionnel |
| VOLUME_NET | Float | Poids net | Calculé |

### 6.2 Synchronisation des Données

#### Mécanisme de Sync (`db_sync.py`)
1. **Détection des modifications**
   ```python
   local_mtime = LOCAL_DB_PATH.stat().st_mtime
   webapp_mtime = WEBAPP_DB_PATH.stat().st_mtime
   if local_mtime > webapp_mtime:
       sync_database()
   ```

2. **Sauvegarde automatique**
   - Backup horodaté avant sync
   - Conservation des 10 dernières versions
   - Restauration en cas d'échec

3. **Validation d'intégrité**
   - Vérification format Excel
   - Contrôle des colonnes obligatoires
   - Validation des types de données

### 6.3 Gestion des Sessions

#### Format de Stockage (`sessions.json`)
```json
{
  "sessions": [
    {
      "timestamp": "2025-09-25T10:30:00",
      "session_id": "abc123def456",
      "client_ip": "192.168.1.100",
      "hostname": "watchai-server",
      "page": "webapp_volumes_reels",
      "action": "data_load",
      "user_agent": "Streamlit Client"
    }
  ]
}
```

#### Rétention des Données
- **Sessions actives** : Conservation 1000 dernières
- **Logs d'accès** : Archivage mensuel
- **Logs sécurité** : Conservation 12 mois

---

## 7. Authentification

### 7.1 Système d'Authentification

#### Mécanisme
1. **Hashage des mots de passe** : SHA-256 avec salt
2. **Gestion des sessions** : Streamlit session_state
3. **Timeout automatique** : 2 heures d'inactivité
4. **Rôles utilisateurs** : Admin, User, Readonly

#### Configuration (`auth_config.py`)
```python
USERS = {
    "Julien": {
        "name": "Julien Marboeuf",
        "role": "admin",
        "password_hash": "hash_sha256",
        "permissions": ["read", "write", "admin"]
    },
    "Jean": {
        "name": "Jean Utilisateur",
        "role": "user",
        "password_hash": "9bf00b33ce29fe15428298f5b773530a5103dd5662d652140d0dfa24bdbb3fcf",
        "permissions": ["read"]
    }
}
```

### 7.2 Gestion des Permissions

#### Niveaux d'Accès
1. **Admin** : Accès total + administration système
2. **User** : Consultation données + exports limités
3. **Readonly** : Visualisation uniquement

#### Contrôles d'Accès
- Vérification du rôle à chaque requête
- Limitation des fonctionnalités par profil
- Audit trail des actions utilisateurs

---

## 8. Déploiement et Infrastructure

### 8.1 Environnements

#### Développement Local
```bash
# Installation
git clone [repository]
cd WATCHAI/Webapp
pip install -r requirements.txt

# Lancement
streamlit run webapp_volumes_reels.py --server.port=8523
streamlit run admin_logs.py --server.port=8524
```

#### Production Streamlit Cloud
```yaml
# Configuration streamlit.toml
[server]
port = 8501
enableCORS = true
enableXsrfProtection = true

[theme]
primaryColor = "#4DBDB3"
backgroundColor = "#F8F9FA"
secondaryBackgroundColor = "#FFFFFF"
```

### 8.2 Variables d'Environnement

#### Configuration Cloud
- `DATABASE_PATH` : Chemin vers DB_Shipping_Master.xlsx
- `LOG_LEVEL` : Niveau de logging (INFO, DEBUG, ERROR)
- `SECURITY_ENABLED` : Activation du module sécurité
- `MAX_UPLOAD_SIZE` : Limite taille fichiers (200MB)

### 8.3 Monitoring de Production

#### Métriques Système
- **Uptime** : Disponibilité application
- **Response Time** : Temps de réponse moyen
- **Memory Usage** : Consommation RAM
- **Error Rate** : Taux d'erreurs applicatives

#### Alerting
- Email administrateur si erreur critique
- Notification Slack pour anomalies détectées
- Dashboard temps réel Streamlit Cloud

---

## 9. Performance et Scalabilité

### 9.1 Optimisations Performance

#### Chargement des Données
```python
@st.cache_data(ttl=3600)  # Cache 1 heure
def load_data():
    # Chargement optimisé avec cache
    return pd.read_excel(path, engine='openpyxl')
```

#### Visualisations
- Limitation du nombre de points affichés (max 10k)
- Agrégation intelligente pour grandes périodes
- Rendering différé pour graphiques complexes

#### Mémoire
- Nettoyage automatique des DataFrames
- Garbage collection forcé après opérations lourdes
- Limite taille session Streamlit (1GB)

### 9.2 Limites Techniques Actuelles

#### Contraintes
- **Volume de données** : Optimal jusqu'à 500k enregistrements
- **Utilisateurs simultanés** : 50 sessions concurrentes
- **Taille fichier** : Maximum 200MB Excel
- **Calculs complexes** : Timeout après 5 minutes

#### Évolutions Futures
- Migration vers base PostgreSQL
- Mise en cache Redis pour performances
- API REST pour intégrations externes
- Clustering pour haute disponibilité

---

## 10. Maintenance et Monitoring

### 10.1 Maintenance Préventive

#### Tâches Quotidiennes
- Vérification disponibilité application
- Contrôle taille des logs (rotation si > 100MB)
- Backup base de données
- Nettoyage caches temporaires

#### Tâches Hebdomadaires
- Analyse des logs sécurité
- Mise à jour données master
- Vérification performances
- Tests fonctionnels automatisés

#### Tâches Mensuelles
- Archivage des anciens logs
- Revue des utilisateurs actifs
- Mise à jour dépendances Python
- Audit sécurité complet

### 10.2 Procédures de Récupération

#### Panne Application
1. Vérification logs d'erreur
2. Restart automatique Streamlit Cloud
3. Restauration depuis backup si nécessaire
4. Notification utilisateurs si downtime > 30min

#### Corruption de Données
1. Détection via validation automatique
2. Restauration depuis dernière sauvegarde valide
3. Re-synchronisation base locale/cloud
4. Validation intégrité post-restauration

### 10.3 Évolutions et Roadmap

#### Version 3.0 (Prévue Q4 2025)
- **Base de données relationnelle** : Migration PostgreSQL
- **API REST** : Endpoints pour intégrations externes
- **Machine Learning** : Prédictions et détection d'anomalies
- **Multi-tenancy** : Support multi-pays/multi-produits

#### Améliorations Techniques
- **Performance** : Optimisation requêtes et caching avancé
- **Sécurité** : 2FA et SSO enterprise
- **UX/UI** : Interface responsive et mobile
- **DevOps** : CI/CD et déploiement automatisé

---

## 📊 Annexes Techniques

### Annexe A : Commandes de Gestion

```bash
# Démarrage complet du système
cd /Users/julienmarboeuf/Documents/BON\ PLEIN/WATCHAI/Webapp
streamlit run webapp_volumes_reels.py --server.port=8523
streamlit run admin_logs.py --server.port=8524

# Synchronisation manuelle des données
python db_sync.py

# Validation des données
cd ../Scripts
streamlit run validation_app.py --server.port=8508

# Nettoyage des logs
find ./logs -name "*.log" -mtime +30 -delete
```

### Annexe B : Configuration Nginx (si applicable)
```nginx
server {
    listen 80;
    server_name watchai.example.com;

    location / {
        proxy_pass http://localhost:8523;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Annexe C : Script de Monitoring
```python
#!/usr/bin/env python3
# monitoring.py - Script de surveillance système
import requests
import time
import logging

def check_webapp_health():
    try:
        response = requests.get('http://localhost:8523/_stcore/health')
        return response.status_code == 200
    except:
        return False

def check_database_sync():
    # Vérification dernière synchronisation
    pass

if __name__ == "__main__":
    # Surveillance continue
    pass
```

---

**Document généré automatiquement par le système WATCHAI**
**© 2025 - Government Logistics Intelligence**
**Classification : Confidentiel - Usage Interne Uniquement**