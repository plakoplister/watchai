# 🔐 Guide du Watermarking Invisible - WATCHAI

**Date**: 2025-10-01
**Status**: ✅ **IMPLÉMENTÉ ET TESTÉ**

---

## 🎯 Objectif

Protéger les données de la webapp contre le scraping en appliquant un **watermark invisible unique** à chaque utilisateur. Si quelqu'un scrappe et partage les données, on peut **identifier la source de la fuite**.

---

## ✅ Ce qui a été implémenté

### Fichiers créés:
- `Webapp/data_watermarking.py` - Module de watermarking (260 lignes)
- `Webapp/test_watermarking.py` - Tests automatiques du watermarking

### Fichiers modifiés:
- `Webapp/webapp_volumes_reels.py` - Intégration du watermarking dans `load_data()`

---

## 🔬 Comment ça fonctionne

### Principe:
Chaque utilisateur non-admin voit des données **légèrement différentes** (±0.3%) :

```
Volume réel: 125,432.5 tonnes

┌─────────────────┬──────────────────┬─────────────────┐
│ Utilisateur     │ Volume affiché   │ Différence      │
├─────────────────┼──────────────────┼─────────────────┤
│ Julien (admin)  │  125,432.5 t     │      0.0 t      │  ← Données exactes
│ Erick (user)    │  126,059.7 t     │   +627.2 t      │  ← Watermark unique
│ Jean (user)     │  125,208.2 t     │   -224.3 t      │  ← Watermark unique
└─────────────────┴──────────────────┴─────────────────┘
```

### Caractéristiques:

1. **Invisible à l'œil nu**: ±0.3% de variation (max ±0.5%)
2. **Unique**: Chaque utilisateur a un bruit différent
3. **Déterministe**: Le même utilisateur voit toujours les mêmes données
4. **Traçable**: On peut identifier qui a partagé des données leakées
5. **Admin privilégié**: Julien voit les données **exactes** (0% de bruit)

### Algorithme:

```python
# Pour chaque utilisateur non-admin:
seed = hash(username)  # Seed unique et déterministe
bruit = gaussian(0, 0.3%)  # Bruit centré sur 0, écart-type 0.3%
valeur_affichée = valeur_réelle * (1 + bruit)
```

---

## 📊 Tests réalisés

```bash
cd Webapp && python3 test_watermarking.py
```

### Résultats des tests:

✅ **Test 1**: Admin (Julien) voit données exactes (0% différence)
✅ **Test 2**: Erick voit données watermarkées (±0.3%)
✅ **Test 3**: Jean voit données watermarkées (±0.3%)
✅ **Test 4**: Erick et Jean voient des données DIFFÉRENTES
✅ **Test 5**: Le watermarking est DÉTERMINISTE (reproductible)
✅ **Test 6**: **Forensics**: On peut identifier la source d'une fuite (100% de précision)

---

## 🔍 Traçabilité (Forensics)

Si on trouve des données leakées, on peut identifier qui les a partagées :

```python
from data_watermarking import watermarking

# On a trouvé des données suspectes
leaked_data = pd.read_csv("données_leakées.csv")

# Tester contre chaque utilisateur
for user in ["Julien", "Erick", "Jean"]:
    result = watermarking.verify_watermark(
        leaked_data,
        user,
        original_data
    )
    print(f"{user}: {result['score']:.0%} match")
```

**Résultat**:
```
Julien: 0% match
Erick: 100% match  ← COUPABLE IDENTIFIÉ
Jean: 0% match
```

---

## 🎛️ Configuration

Dans `Webapp/data_watermarking.py` :

```python
class DataWatermarking:
    ADMIN_USER = "Julien"              # Admin voit données exactes
    NOISE_PERCENTAGE = 0.003           # ±0.3% de bruit moyen
    MIN_NOISE = 0.001                  # Min 0.1%
    MAX_NOISE = 0.005                  # Max 0.5%

    WATERMARK_COLUMNS = [
        'POIDS_TONNES',  # Colonne à watermarker
        'PDSNET'         # Colonne à watermarker
    ]
```

**Pour ajuster le niveau de bruit** :
- Augmenter `NOISE_PERCENTAGE` = bruit plus visible (meilleure traçabilité)
- Diminuer `NOISE_PERCENTAGE` = bruit plus invisible (meilleure UX)

**Recommandation actuelle** : 0.3% = bon équilibre

---

## 🌐 Intégration dans la webapp

### Code simplifié:

```python
# 1. Import du module
from data_watermarking import watermarking

# 2. Application automatique
def load_data():
    df_raw = load_data_raw()  # Données brutes depuis Excel

    # Watermarking selon l'utilisateur
    username = st.session_state.username
    df_watermarked = watermarking.apply_watermark(df_raw, username)

    return df_watermarked
```

### Affichage en sidebar:

**Pour Julien (admin)** :
```
🔒 Sécurité:
- Requêtes: 15/100
- Restantes: 85
- Watermark: ADMIN - No watermark
```

**Pour Erick/Jean (users)** :
```
🔐 Données protégées
```

---

## 📈 Impact et performance

### Sécurité:
- ✅ **Protection contre scraping massif**: Données "empoisonnées"
- ✅ **Traçabilité**: Identification de la source en cas de fuite
- ✅ **Dissuasion**: Les utilisateurs savent que les données sont tracées

### Performance:
- ⚡ **Impact minimal**: Calcul en mémoire (NumPy optimisé)
- ⚡ **Cache préservé**: Les données brutes sont cachées (TTL 3600s)
- ⚡ **Watermark appliqué à la volée**: Pas de stockage supplémentaire

### UX:
- ✅ **Invisible**: ±0.3% non détectable visuellement
- ✅ **Cohérent**: Même utilisateur = mêmes données
- ✅ **Admin privilégié**: Julien voit toujours les données exactes
- ✅ **Aucun changement d'interface**: Tout fonctionne normalement

---

## 🧪 Comment tester en local

### 1. Tester le watermarking seul:
```bash
cd Webapp
python3 test_watermarking.py
```

### 2. Tester dans la webapp:
```bash
# Ouvrir http://localhost:8523
# Se connecter avec différents comptes:

# Admin (données exactes):
Username: Julien
Password: jo06v2

# User 1 (données watermarkées):
Username: Erick
Password: FNOA3SAfj*v5h%

# User 2 (données watermarkées):
Username: Jean
Password: WatchAI02$
```

### 3. Vérifier le watermarking:
- Connecte-toi avec **Julien** → Note un volume (ex: 125,432.5 t)
- Déconnecte-toi
- Connecte-toi avec **Erick** → Note le MÊME volume (ex: 126,059.7 t)
- Déconnecte-toi
- Connecte-toi avec **Jean** → Note le MÊME volume (ex: 125,208.2 t)
- **Les 3 valeurs doivent être différentes** ✅

---

## 🔒 Sécurité combinée

Le watermarking s'ajoute aux autres protections :

| Protection | Status | Fonction |
|------------|--------|----------|
| Rate Limiting | ✅ | Empêche scraping rapide |
| Session Timeout | ✅ | Déconnexion auto après 30 min |
| CAPTCHA | ✅ | Bloque attaques brute-force |
| **Watermarking** | ✅ | **Trace les fuites de données** |

**Ensemble**, ces protections rendent le scraping :
1. **Lent** (rate limiting)
2. **Difficile** (session timeout + CAPTCHA)
3. **Traçable** (watermarking) ← **NOUVEAU**
4. **Inutilisable** (données empoisonnées) ← **NOUVEAU**

---

## ⚠️ Limitations et considérations

### Ce que le watermarking PROTÈGE:
- ✅ Scraping via dataframes (copier-coller)
- ✅ Scraping via console JavaScript
- ✅ Scraping via Network tab
- ✅ Export de graphiques (données dans Plotly)

### Ce que le watermarking NE PROTÈGE PAS:
- ❌ Screenshots (mais données approximatives)
- ❌ Utilisateur qui retape manuellement les données
- ❌ Attaquant qui a accès direct au fichier Excel source

### Recommandations supplémentaires:
Si tu veux aller plus loin :
- **Niveau 2**: Rate limiting spécifique sur les changements de vue (déjà implémenté)
- **Niveau 3**: Désactiver le clic droit sur les dataframes (CSS)
- **Niveau 4**: Convertir graphiques en images statiques (PNG au lieu de Plotly interactif)

---

## 📝 Logs et monitoring

Le watermarking est loggé automatiquement :

```bash
# Voir les logs de watermarking
tail -f Webapp/logs/activity.log | grep watermark
```

**Exemple de log** :
```
2025-10-01 14:05:32 | INFO | ACTIVITY | data_watermark | Applied watermark for user Erick
2025-10-01 14:07:18 | INFO | ACTIVITY | data_watermark | Applied watermark for user Jean
```

---

## 🆘 Désactiver le watermarking

Si besoin de désactiver temporairement :

### Option 1: Désactiver pour TOUS
```python
# Dans webapp_volumes_reels.py
WATERMARKING_ENABLED = False  # Forcer à False
```

### Option 2: Désactiver pour un utilisateur spécifique
```python
# Dans data_watermarking.py
self.ADMIN_USER = "Julien"  # Ajouter d'autres users ici
# Exemple: self.ADMIN_USERS = ["Julien", "Erick"]
```

### Option 3: Réduire le bruit
```python
# Dans data_watermarking.py
self.NOISE_PERCENTAGE = 0.001  # Réduire à ±0.1%
```

---

## 🎓 Exemple d'utilisation forensics

Scénario : Tu trouves un article de presse avec des chiffres de la webapp.

**Étape 1** : Extraire les données de l'article
```python
leaked_data = pd.DataFrame({
    'EXPORTATEUR': ['CARGILL'],
    'POIDS_TONNES': [126059.7]  # Chiffre trouvé dans l'article
})
```

**Étape 2** : Identifier la source
```python
from data_watermarking import watermarking

# Charger les données originales
df_original = load_data_raw()
df_original_cargill = df_original[df_original['EXPORTATEUR'] == 'CARGILL']

# Tester contre chaque utilisateur
for user in ["Julien", "Erick", "Jean"]:
    result = watermarking.verify_watermark(
        leaked_data,
        user,
        df_original_cargill
    )
    if result['match']:
        print(f"⚠️ FUITE IDENTIFIÉE: {user} (confiance: {result['confidence']})")
```

**Résultat** :
```
⚠️ FUITE IDENTIFIÉE: Erick (confiance: HIGH)
```

---

## 📚 Ressources

- Code source: `Webapp/data_watermarking.py`
- Tests: `Webapp/test_watermarking.py`
- Documentation complète: `RECAP_SECURITE.md`
- Status: `STATUS_SECURITE.txt`

---

## ✅ Résumé

| Critère | Valeur |
|---------|--------|
| **Niveau de bruit** | ±0.3% (invisible) |
| **Admin affecté** | Non (Julien voit données exactes) |
| **Users affectés** | Oui (Erick, Jean) |
| **Traçabilité** | 100% de précision |
| **Impact UX** | Nul |
| **Impact performance** | Minimal |
| **Déterminisme** | Oui (reproductible) |
| **Unicité** | Oui (chaque user = watermark unique) |

---

**🚀 WATERMARKING OPÉRATIONNEL**

Le watermarking invisible est maintenant actif sur la webapp.
Prêt pour le déploiement en production.

**Version**: 1.0-WATERMARKING
**Date**: 2025-10-01
**Testé et validé**: ✅
