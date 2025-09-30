# WATCHAI - Système d'Intelligence Logistique Gouvernementale

## 🎯 Vue d'Ensemble

WATCHAI est un système complet d'analyse des exportations de cacao de Côte d'Ivoire. Il traite mensuellement les données d'exportation des ports d'Abidjan (ABJ) et San Pedro (SPY), avec validation intelligente des entités et intégration automatisée.

**Version** : Production 2025
**Ports gérés** : Abidjan (ABJ), San Pedro (SPY)
**Période couverte** : 2023-2025
**Volume traité** : 50+ fichiers mensuels, ~57 millions kg

## 🏗️ Architecture du Système

```
WATCHAI/
├── Scripts/           # Scripts principaux d'intégration et validation
├── Master_Data/       # Base de données principale et mappings
├── Updates_Mensuels/  # Données mensuelles par année
├── Validation/        # Rapports et sauvegardes
├── Webapp/           # Application web de visualisation
├── Backups/          # Sauvegardes automatiques
└── TRASH/            # Fichiers obsolètes
```

## 📋 Workflow de Mise à Jour Mensuelle

### Phase 1 : Réception des Données
1. **Déposer** les nouveaux fichiers dans `/Updates_Mensuels/`
   - Format : `ABJ - AOU 2025.xlsx` ou `SPY - AOU 2025.xlsx`
   - Le système détecte automatiquement le format

### Phase 2 : Validation des Entités
```bash
cd Scripts/
streamlit run validation_app.py --server.port=8501
```
1. **Analyser** les nouvelles entités (exportateurs/destinataires)
2. **Valider** les mappings proposés automatiquement
3. **Corriger** manuellement si nécessaire
4. **Sauvegarder** via "🔧 Mise à jour Entity_Mappings"

### Phase 3 : Intégration
1. **Cliquer** sur "🚀 Intégrer les données"
2. Le système :
   - Charge les mappings depuis Entity_Mappings.xlsx
   - Transforme au format DB_Shipping_Master (colonnes A→I)
   - Sauvegarde automatique du master existant
   - Intègre dans les feuilles appropriées (DB ABJ/DB SP)
   - Archive les fichiers traités
   - Génère le rapport d'intégration

### Phase 4 : Visualisation
```bash
cd Webapp/
streamlit run webapp_volumes_reels.py --server.port=8502
```
Accéder aux tableaux de bord mis à jour avec les nouvelles données.

## 🔧 Scripts Principaux

### Scripts de Production

#### `integrate_monthly_data.py` (32KB)
**Script principal d'intégration**
- Gère 4 formats de fichiers différents (2023, 2024, juillet 2025, août 2025)
- Transforme les données au format DB_Shipping_Master exact
- Applique les mappings d'entités appris
- Sauvegarde automatique avant intégration

```python
# Exécution directe
python integrate_monthly_data.py

# Via l'app de validation (recommandé)
streamlit run validation_app.py
```

#### `validation_app.py` (83KB)
**Application Streamlit de validation**
- Interface web pour valider les nouvelles entités
- Normalisation intelligente des noms d'entreprises
- Regroupement automatique des destinataires similaires
- Sauvegarde des mappings dans Entity_Mappings.xlsx

**URL**: http://localhost:8501 (par défaut)

### Scripts d'Analyse et Support

- **`analyze_monthly_files.py`** - Analyse la structure des fichiers mensuels
- **`pre_integration_check.py`** - Contrôle qualité avant intégration
- **`deduplicate_destinations.py`** - Déduplication des destinataires
- **`update_country_names.py`** - Normalisation des codes pays

### Scripts de Test

- **`test_all_corrections.py`** - Test complet du workflow
- **`test_na_count.py`** - Comptage des entités non-mappées
- **`test_detection_suivi.py`** - Test de détection des fichiers

## 📊 Base de Données

### `DB_Shipping_Master.xlsx` (7.3MB)
**Base de données principale**

**Structure des colonnes (A→I)** :
| Col | Nom | Description |
|-----|-----|-------------|
| A | DATENR | Date de déclaration |
| B | ORIGINE | Toujours "CI" (Côte d'Ivoire) |
| C | DESTINATION | Code pays ISO (NL, DE, BE, etc.) |
| D | EXPORTATEUR | Nom complet exportateur |
| E | DESTINATAIRE | Nom complet destinataire |
| F | POSTAR | Code type de produit |
| G | PDSNET | Poids net en kg |
| H | EXPORTATEUR SIMPLE | Nom simplifié exportateur |
| I | DESTINATAIRE SIMPLE | Nom simplifié destinataire |

**Feuilles** :
- `DB ABJ` : Données port d'Abidjan
- `DB SP` : Données port de San Pedro

### `Entity_Mappings.xlsx` (814KB)
**Mappings d'entités appris**

**Feuilles** :
- `Exportateurs` : Mapping noms complets → noms simplifiés
- `Destinataires` : Mapping noms complets → noms simplifiés

Actuellement : 308 exportateurs, 36,210 destinataires mappés

### `fichiers_traites.json` (374B)
**Suivi des intégrations**
```json
{
  "derniere_mise_a_jour": "2025-09-24T18:00:00",
  "fichiers_integres": [
    {
      "nom": "ABJ - JUL 2025.xlsx",
      "date_integration": "2025-09-23T12:00:00",
      "lignes": 340,
      "volume_kg": 21500000
    }
  ]
}
```

## 🌐 Application Web

### `webapp_volumes_reels.py` (47KB)
**Application Streamlit principale de visualisation**

**Fonctionnalités** :
- Tableaux de bord interactifs
- Analyses par port, exportateur, destination
- Filtres par période, entité
- Export des données visualisées

**Lancement** :
```bash
cd Webapp/
streamlit run webapp_volumes_reels.py --server.port=8502
```

**URL** : http://localhost:8502

## 📁 Formats de Fichiers Supportés

### Format 2023 (Ancien)
- `DECLARATION_DATE, NOM_EXPORTATEUR, NOM_IMPORTATEUR, CODE_SH2, POIDS_NET`

### Format 2024-Mars (Nouveau)
- `DATE_DECLARATION, EXPORTATEUR, DESTINATAIRE, POSTAR, POIDS_NET`

### Format Juillet 2025 (Spécial)
- `DATE_DEC, OPERATEUR, CLIENT_EXPORT, TOT_PDSNET, CODE_PAYS_DESTINATION`

### Format Août 2025 (Final)
- `DATENR, EXPORTATEUR, DESTINATAIRE, POSTAR, PDSNET, DESTINATION`

Le système détecte automatiquement le format basé sur les colonnes présentes.

## 🚀 Installation et Configuration

### Prérequis
```bash
# Python 3.8+
pip install streamlit pandas openpyxl numpy
```

### Structure des Dossiers
```bash
mkdir -p WATCHAI/{Scripts,Master_Data,Updates_Mensuels,Validation,Webapp,Backups,TRASH}
mkdir -p WATCHAI/Updates_Mensuels/{2023,2024,2025}
```

### Première Utilisation
1. **Placer** les fichiers de base dans Master_Data/
2. **Configurer** les chemins dans les scripts si nécessaire
3. **Tester** avec `python test_all_corrections.py`

## 🔍 Surveillance et Maintenance

### Logs et Rapports
- **Validation/** : Rapports d'intégration avec timestamps
- **Backups/** : Sauvegardes automatiques avant chaque intégration
- **Console** : Logs détaillés pendant l'exécution

### Indicateurs de Santé
- **Taux de mapping** : % d'entités automatiquement reconnues
- **Volume intégré** : Tonnes traitées par mois
- **Erreurs** : Fichiers en échec d'intégration

### Nettoyage Périodique
```bash
# Nettoyer les anciens backups (> 30 jours)
find Backups/ -name "*.xlsx" -mtime +30 -delete

# Nettoyer les anciens rapports (> 90 jours)
find Validation/ -name "*.json" -mtime +90 -delete
```

## 🛠️ Dépannage

### Problèmes Courants

**Fichier non détecté**
- Vérifier le format du nom : `ABJ/SPY - MOI ANNEE.xlsx`
- Vérifier que le fichier n'est pas déjà dans fichiers_traites.json

**Colonnes manquantes**
- Le système s'adapte automatiquement aux différents formats
- Vérifier les logs pour identifier les colonnes non reconnues

**Erreur de mapping**
- Utiliser l'interface de validation pour corriger manuellement
- Les corrections sont sauvegardées pour les prochaines fois

**Application ne démarre pas**
- Vérifier les dépendances : `pip install -r requirements.txt`
- Vérifier les ports disponibles (8501, 8502)

### Récupération d'Erreur
- **Backups automatiques** : Tous les fichiers sont sauvegardés avant modification
- **Rapports d'intégration** : Traçabilité complète des opérations
- **Fichiers de test** : Scripts de validation pour tester les corrections

## 📈 Performance et Statistiques

### Métriques Actuelles (Sept 2025)
- **Fichiers traités** : 50+ fichiers mensuels
- **Données intégrées** : 3 années complètes (2023-2025)
- **Volume total** : ~57 millions kg
- **Entités mappées** : Centaines d'exportateurs et destinataires
- **Taux de réussite** : 100% d'intégration sans perte de données
- **Temps de traitement** : ~2-5 minutes par fichier mensuel

### Évolution du Système
- **2023** : Version initiale, format basique
- **2024** : Amélioration des formats, validation manuelle
- **2025** : Workflow automatisé, validation intelligente, interface web

## 🔒 Sécurité et Conformité

- **Sauvegardes automatiques** avant chaque modification
- **Traçabilité complète** des opérations via les rapports
- **Validation des données** avant intégration
- **Contrôles d'intégrité** sur la structure des fichiers
- **Logs d'accès** pour l'application web

## 👥 Support et Contact

Pour toute question ou problème :
1. **Consulter** les logs dans la console
2. **Vérifier** les rapports dans Validation/
3. **Tester** avec les scripts de test inclus
4. **Documenter** le problème avec les logs d'erreur

---

**WATCHAI** - Système d'Intelligence Logistique Gouvernementale
*Développé pour l'analyse des exportations de cacao de Côte d'Ivoire*
*Version Production 2025*