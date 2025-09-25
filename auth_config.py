"""
Configuration de l'authentification pour l'application Cacao CI
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

# Configuration des utilisateurs (mots de passe hashés)
# Pour générer un hash: hashlib.sha256("motdepasse".encode()).hexdigest()
USERS = {
    "Julien": {
        "password_hash": "117032426e05ce97262a0a8e60db8c30fdb7cda9ee13ede8a52c51a9520f0386",  # jo06v2
        "name": "Julien",
        "role": "admin"
    },
    "Erick": {
        "password_hash": "66e7891119d11a23f96c5c6066d6635ee687724af80a58a9cae89e89cdda9106",  # FNOA3SAfj*v5h%
        "name": "Erick",
        "role": "user"
    },
    "Jean": {
        "password_hash": "9bf00b33ce29fe15428298f5b773530a5103dd5662d652140d0dfa24bdbb3fcf",  # WatchAI02$
        "name": "Jean",
        "role": "user"
    }
}

def verify_password(username, password):
    """Vérifie le mot de passe d'un utilisateur"""
    if username not in USERS:
        return False
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return USERS[username]["password_hash"] == password_hash

def get_user_info(username):
    """Retourne les informations d'un utilisateur"""
    if username in USERS:
        return {
            "username": username,
            "name": USERS[username]["name"],
            "role": USERS[username]["role"]
        }
    return None

def log_connection(username, success=True):
    """Enregistre une tentative de connexion"""
    log_file = Path("connection_logs.json")
    
    # Charger les logs existants
    if log_file.exists():
        with open(log_file, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
    
    # Ajouter le nouveau log
    logs.append({
        "username": username,
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "user_info": get_user_info(username) if success else None
    })
    
    # Sauvegarder les logs
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    return True

def get_connection_stats():
    """Retourne les statistiques de connexion"""
    log_file = Path("connection_logs.json")
    
    if not log_file.exists():
        return {
            "total_connections": 0,
            "unique_users": 0,
            "connections_by_user": {},
            "last_connections": []
        }
    
    with open(log_file, 'r') as f:
        logs = json.load(f)
    
    # Calculer les statistiques
    stats = {
        "total_connections": len([l for l in logs if l.get("success", False)]),
        "unique_users": len(set([l["username"] for l in logs if l.get("success", False)])),
        "connections_by_user": {},
        "last_connections": []
    }
    
    # Compter par utilisateur
    for log in logs:
        if log.get("success", False):
            username = log["username"]
            if username not in stats["connections_by_user"]:
                stats["connections_by_user"][username] = 0
            stats["connections_by_user"][username] += 1
    
    # Dernières connexions
    successful_logs = [l for l in logs if l.get("success", False)]
    stats["last_connections"] = successful_logs[-10:][::-1]  # 10 dernières, ordre inverse
    
    return stats

# Instructions pour changer les mots de passe
"""
Pour changer un mot de passe:
1. Générer le hash du nouveau mot de passe:
   python -c "import hashlib; print(hashlib.sha256('nouveaumotdepasse'.encode()).hexdigest())"
2. Remplacer le password_hash dans USERS

Utilisateurs configurés:
- Julien: jo06v2 (admin)
- Erick: FNOA3SAfj*v5h% (user)
- Jean: WatchAI02$ (user)
"""