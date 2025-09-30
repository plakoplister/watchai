# 🍫 Exportations de cacao de Côte d'Ivoire - Dashboard Analytique

Système complet de gestion et visualisation des données d'exportation cacao pour la Côte d'Ivoire, incluant validation des données mensuelles et dashboard interactif.

## 📁 Structure du Projet

```
EXPORT-Db/
├── Master_Data/                # Base de données principale
│   └── DB_Shipping_Master.xlsb # Master database (2021-2022)
├── Updates_Mensuels/           # Fichiers de mise à jour
│   ├── 2023/                   # Données mensuelles 2023
│   ├── 2024/                   # Données mensuelles 2024
│   └── 2025/                   # Données mensuelles 2025
├── Scripts/                    # Scripts de traitement
├── Validation/                 # Résultats de validation
├── Archive/                    # Sauvegardes
└── Reports/                    # Rapports générés
```

## 🚀 Flux de Traitement

### 1. Réception des Fichiers Mensuels
- Les fichiers Excel sont déposés dans `Updates_Mensuels/YYYY/`
- Format: `PORT - MOIS ANNÉE.xlsx` (ex: `ABJ - JAN 2025.xlsx`)
- Ports supportés: ABJ (Abidjan), SPY (San Pedro)

### 2. Validation des Nouvelles Entités
Avant intégration, le système identifie:
- **Nouveaux exportateurs** non présents dans le master
- **Nouveaux destinataires** non répertoriés
- **Nouvelles destinations** (codes pays)

### 3. Interface de Validation
Interface web Streamlit pour:
- ✅ **Accepter** : Ajouter l'entité telle quelle
- 🔧 **Corriger** : Remplacer par le nom standardisé
- ❌ **Ignorer** : Exclure de l'intégration

### 4. Intégration dans le Master
- Application des corrections validées
- Consolidation des données par port
- Sauvegarde automatique du master
- Génération de rapports d'intégration

## 📊 Dashboard Interactif

### Application Principale - `webapp_volumes_reels.py`
Dashboard Streamlit avec interface sécurisée pour visualiser les données d'exportation:

```bash
streamlit run webapp_volumes_reels.py
```

**Fonctionnalités principales:**
- 🔐 **Système d'authentification multi-utilisateurs** avec tracking des connexions
- 📈 **Analyses temporelles** : évolution des volumes par mois et saisons
- 🏭 **Top 5 exportateurs** avec volumes détaillés et séparateurs de milliers
- 🌍 **Top 5 destinations** avec codes pays et volumes formatés
- 📦 **Analyse par produits** : séparation Fèves vs Produits Transformés
- 🔍 **Analyse comparative avancée** avec 4 filtres indépendants :
  - Filtrage par Exportateur
  - Filtrage par Destinataire  
  - Filtrage par Destination (pays)
  - Filtrage par Mois de Déclaration
- 📊 **Graphiques interactifs** avec design gradient bleu professionnel
- ⚠️ **Notifications de saisons incomplètes** avec détail des mois exclus

### Système d'Authentification

**Utilisateurs configurés:**
- **Julien** (jo06v2) - Accès complet
- **Erick** (FNOA3SAfj*v5h%) - Accès complet

**Sécurité:**
- Mots de passe hashés SHA256
- Logs de connexion dans `connection_logs.json`
- Interface de monitoring avec `view_connections.py`

### Scripts de Validation des Données

### `analyze_monthly_files.py`
Analyse la structure des fichiers mensuels:
```bash
python Scripts/analyze_monthly_files.py
```

### `validation_app.py` 
Interface web de validation:
```bash
streamlit run Scripts/validation_app.py
```

### `test_validation.py`
Test de détection des nouvelles entités:
```bash
python Scripts/test_validation.py
```

### `integrate_monthly_data.py`
Intégration des données validées:
```bash
# Mode test (recommandé)
python Scripts/integrate_monthly_data.py

# Mode production
python Scripts/integrate_monthly_data.py --production
```

### `view_connections.py`
Monitoring des connexions au dashboard:
```bash
python view_connections.py
```

## 📈 Données Master

### Base de Données Actuelle (2021-2022)
- **107 exportateurs** référencés
- **109 destinataires** connus  
- **81 destinations** (codes pays)
- **42,043 lignes** d'export au total

### Structure des Fichiers Mensuels
**Colonnes principales:**
- `EXPORTATEUR` - Société exportatrice
- `DESTINATAIRE` - Client final
- `DESTINATION` - Code pays (ISO 2 lettres)
- `POIDS_NET` - Poids en kg
- `POSTAR` - Code produit
- `DATE_DECLARATION` - Date d'export

## 🔍 Validation des Entités

### Exemples de Nouvelles Entités Détectées (2025)

**Nouveaux Exportateurs (238):**
- AKAGNY CACAO S.A
- CARGILL WEST AFRICA  
- OLAM COCOA PROCESSING CI
- AFRICA SOURCING COTE D'IVOIRE

**Nouveaux Destinataires (6,040):**
- ACT INTERNATIONAL AG (Suisse)
- THEOBROMA BV (Pays-Bas)
- ECOM AGROTRADE LTD (Royaume-Uni)

**Nouvelles Destinations (5):**
- KE (Kenya)
- VE (Venezuela) 
- JO (Jordanie)
- MG (Madagascar)
- KH (Cambodge)

## 📊 Volumes Traités

### Année 2025 (Partiel - Oct 2024 à Jun 2025)
- **14 fichiers** mensuels
- **10,296 lignes** d'export
- **1,295,215 tonnes** exportées
- Répartition: 57% Abidjan, 43% San Pedro

## ⚙️ Configuration

### Prérequis
```bash
pip install pandas streamlit openpyxl pyxlsb plotly hashlib pathlib
```

### Configuration Dashboard
**Fichier de données:** `DB_Shipping_Master.xlsx` (doit être présent dans le répertoire)
**Assets:** Logo placé dans `assets/logo.png` pour affichage via GitHub

### Validation Mensuelle Intégrée
Le système inclut une validation automatique des données mensuelles avec:
- **Détection des saisons incomplètes** 
- **Exclusion automatique** des mois non finalisés
- **Notifications spécifiques** par saison (ex: "Saison 2024-2025 (excl: aoû, sep)")
- **Catégorisation intelligente** des produits depuis la colonne J du fichier Excel

### Chemins de Configuration
Modifiez dans les scripts si nécessaire:
```python
BASE_DIR = Path("/path/to/EXPORT-Db")
```

## 🔄 Processus de Mise à Jour Trimestrielle

1. **Réception fichiers** → `Updates_Mensuels/YYYY/`
2. **Analyse** → `python analyze_monthly_files.py`
3. **Validation** → `streamlit run validation_app.py`
4. **Test intégration** → `python integrate_monthly_data.py`
5. **Intégration finale** → Mode production
6. **Génération rapports** → `Reports/`

## 📋 Format des Fichiers de Validation

### Structure JSON des Décisions
```json
{
  "validation_date": "2025-01-15T10:30:00",
  "year": "2025",
  "corrections": {
    "exportateurs": {
      "OLD_NAME": "CORRECTED_NAME"
    },
    "destinataires": {
      "OLD_NAME": "CORRECTED_NAME"  
    },
    "destinations": {
      "OLD_CODE": "CORRECT_CODE"
    }
  },
  "ignored_entities": {
    "exportateurs": ["ENTITY_TO_IGNORE"],
    "destinataires": ["ENTITY_TO_IGNORE"],
    "destinations": ["CODE_TO_IGNORE"]
  }
}
```

## 🔐 Sécurité et Sauvegardes

- **Sauvegarde automatique** du master avant chaque intégration
- **Archivage horodaté** dans `Archive/`
- **Journalisation complète** des opérations
- **Mode dry-run** pour tests sécurisés

## 📞 Support

Pour questions ou problèmes:
1. Vérifier les logs dans `Validation/`
2. Consulter les sauvegardes dans `Archive/` 
3. Utiliser le mode dry-run pour déboguer

## 🎨 Charte Graphique BON PLEIN

### Palette de Couleurs Principale

**Bleus Corporates (Couleurs principales):**
```css
/* Bleu Principal Foncé */
#1e3a5f  /* Utilisé pour titres principaux et éléments forts */

/* Bleu Principal Moyen */  
#2c5282  /* Utilisé pour boutons et éléments interactifs */

/* Bleu Clair Accent */
#bee3f8  /* Utilisé pour sous-titres et textes secondaires */
```

**Couleurs Complémentaires:**
```css
/* Gris Texte */
#2c3e50  /* Texte principal sur fond blanc */
#666     /* Texte secondaire et sous-titres */
#bdc3c7  /* Texte sur fond sombre */

/* Transparence */
rgba(0,0,0,0)     /* Arrière-plans transparents graphiques */
rgba(30,58,95,0.2) /* Zones de remplissage graphiques */
rgba(0,0,0,0.1)   /* Ombres légères */
```

### Gradients Signature

**Gradient Principal (Header/Background):**
```css
background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
```

**Gradient Boutons:**
```css
background: linear-gradient(135deg, #1e3a5f, #2c5282) !important;
```

### Structure et Espacement

**Layout Standard:**
- Header avec gradient bleu et logo
- Contenus sur fond blanc avec texte #2c3e50
- Graphiques sur fond transparent
- Footer discret en #666

**Guidelines d'Usage:**
1. **#1e3a5f** pour tous les titres H1 et éléments de navigation
2. **#2c5282** pour boutons d'action et éléments cliquables  
3. **#bee3f8** pour sous-titres et descriptions sur fond sombre
4. **Gradients** uniquement pour headers et boutons principaux
5. **rgba(0,0,0,0)** pour tous les arrière-plans de graphiques Plotly

### Logo et Assets

**Placement Logo:**
- Fichiers dans `/assets/logo.png` pour affichage via GitHub
- URL GitHub raw: `https://raw.githubusercontent.com/plakoplister/caca-dashboard-ci/main/assets/logo.png`
- Éviter base64 (problème d'affichage en carré blanc)
- Logo aligné à gauche du header sur gradient bleu

### Format des Nombres

**Standards Numériques BON PLEIN:**
```python
# Formatage obligatoire pour TOUS les nombres
def format_number(value):
    return f"{int(value):,}".replace(",", " ")

# Exemples d'application:
# 1234567 → "1 234 567"
# 45678.9 → "45 679" (arrondi entier)
```

**Règles Strictes:**
1. **Entiers uniquement** - aucune décimale affichée
2. **Séparateur de milliers** obligatoire (espace, pas virgule)
3. **Application universelle** : graphiques, tableaux, métriques
4. **Cohérence totale** sur toute l'interface

### Exemples d'Application

**Header Type:**
```html
<div style="background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);">
    <h1 style="color: white;">Titre Application</h1>
    <p style="color: #bee3f8;">Sous-titre descriptif</p>
</div>
```

**Contenu Principal:**
```html
<h2 style="color: #1e3a5f;">Section Title</h2>
<p style="color: #2c3e50;">Texte principal</p>
<p style="color: #666;">Texte secondaire</p>
```

Cette charte garantit une cohérence visuelle across toutes les applications BON PLEIN.

---

*Système développé pour la gestion des exportations cacao - Côte d'Ivoire*
